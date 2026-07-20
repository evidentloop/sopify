"""Deterministic contract for Sopify managed-plan packages."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


PLAN_FILES_BY_LEVEL: dict[str, tuple[str, ...]] = {
    "light": ("plan.md",),
    "standard": ("plan.md", "tasks.md"),
    "architecture": ("plan.md", "tasks.md", "design.md"),
}
_SEMANTIC_FILENAMES = frozenset({"plan.md", "tasks.md", "design.md", "background.md"})
_FRONTMATTER_LEVEL_RE = re.compile(r"^level\s*:\s*(.+?)\s*$")


@dataclass(frozen=True)
class PlanPackageSnapshot:
    """Objective structure and version facts for one plan directory."""

    valid: bool
    level: str | None
    version: str | None
    files: tuple[str, ...]
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "level": self.level,
            "version": self.version,
            "error": self.error,
        }


def _read_level(plan_md: Path) -> tuple[str | None, str | None]:
    try:
        lines = plan_md.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return None, f"cannot read plan.md: {exc}"

    if not lines or lines[0].strip() != "---":
        return None, "plan.md must start with YAML frontmatter"

    levels: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _FRONTMATTER_LEVEL_RE.match(line)
        if match:
            levels.append(match.group(1).strip().strip("'\""))
    else:
        return None, "plan.md frontmatter is not closed"

    if len(levels) != 1:
        return None, "plan.md frontmatter must contain exactly one level"
    level = levels[0]
    if level not in PLAN_FILES_BY_LEVEL:
        expected = ", ".join(PLAN_FILES_BY_LEVEL)
        return None, f"unsupported plan level {level!r}; expected {expected}"
    return level, None


def _calculate_version(plan_dir: Path, filenames: tuple[str, ...]) -> str:
    digest = sha256()
    for filename in filenames:
        raw = (plan_dir / filename).read_bytes()
        path_bytes = filename.encode("utf-8")
        # Length framing keeps path/content boundaries deterministic and unambiguous.
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return f"sha256:{digest.hexdigest()}"


def inspect_plan_package(plan_dir: Path) -> PlanPackageSnapshot:
    """Validate a plan package and compute its semantic version when valid."""
    if not plan_dir.is_dir():
        return PlanPackageSnapshot(False, None, None, (), "plan directory not found")

    plan_md = plan_dir / "plan.md"
    if not plan_md.is_file():
        return PlanPackageSnapshot(False, None, None, (), "missing plan.md")

    level, level_error = _read_level(plan_md)
    if level_error is not None or level is None:
        return PlanPackageSnapshot(False, level, None, (), level_error)

    expected = PLAN_FILES_BY_LEVEL[level]
    present_semantic = tuple(
        name for name in sorted(_SEMANTIC_FILENAMES) if (plan_dir / name).is_file()
    )
    missing = [name for name in expected if name not in present_semantic]
    extra = [name for name in present_semantic if name not in expected]
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing semantic files: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected semantic files: {', '.join(extra)}")
        return PlanPackageSnapshot(
            False, level, None, present_semantic, "; ".join(details)
        )

    try:
        version = _calculate_version(plan_dir, expected)
    except OSError as exc:
        return PlanPackageSnapshot(
            False, level, None, expected, f"cannot read plan files: {exc}"
        )
    return PlanPackageSnapshot(True, level, version, expected, None)
