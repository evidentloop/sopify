"""Plan discovery and loading for Sopify runtime.

Provides functions to find existing plan artifacts by reference or topic key,
and to reconstruct ``PlanArtifact`` objects from on-disk plan directories.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Mapping

from .._yaml import YamlParseError, load_yaml
from .identity import derive_topic_key
from sopify_contracts.artifacts import PlanArtifact
from sopify_contracts.core import RuntimeConfig

_FRONT_MATTER_RE = re.compile(r"\A---\n(?P<front>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)
_PLAN_REFERENCE_RE = re.compile(r"(?P<plan_id>\d{8}_[a-z0-9][a-z0-9_.-]*)", re.IGNORECASE)


def find_plan_by_request_reference(request_text: str, *, config: RuntimeConfig) -> PlanArtifact | None:
    for match in _PLAN_REFERENCE_RE.finditer(request_text):
        plan_id = (match.group("plan_id") or "").strip()
        if not plan_id:
            continue
        artifact = load_plan_artifact(config.plan_root / plan_id, config=config)
        if artifact is not None:
            return artifact
    return None


def find_plan_by_topic_key(topic_key: str, *, config: RuntimeConfig) -> PlanArtifact | None:
    matches: list[PlanArtifact] = []
    plan_root = config.plan_root
    if not plan_root.exists():
        return None
    for plan_dir in sorted(plan_root.iterdir()):
        artifact = load_plan_artifact(plan_dir, config=config)
        if artifact is None:
            continue
        candidate_topic_key = artifact.topic_key or derive_topic_key(artifact.title)
        if candidate_topic_key == topic_key:
            matches.append(artifact)
            if len(matches) > 1:
                return None
    return matches[0] if len(matches) == 1 else None


def load_plan_artifact(plan_dir: Path, *, config: RuntimeConfig) -> PlanArtifact | None:
    if not plan_dir.exists() or not plan_dir.is_dir():
        return None

    metadata_path = _pick_metadata_file(plan_dir)
    if metadata_path is None:
        return None

    metadata, body = _load_plan_metadata(metadata_path)
    if metadata is None:
        return None

    plan_id = str(metadata.get("plan_id") or plan_dir.name)
    level = str(metadata.get("level") or ("light" if metadata_path.name == "plan.md" else "standard"))
    title = _extract_title(body) or plan_id
    summary = _extract_summary(body, fallback=title)
    topic_key = str(metadata.get("topic_key") or metadata.get("feature_key") or derive_topic_key(title))
    files = tuple(str(path.relative_to(config.workspace_root)) for path in _collect_plan_files(plan_dir))
    created_at = _path_created_at(metadata_path)

    return PlanArtifact(
        plan_id=plan_id,
        title=title,
        summary=summary,
        level=level,
        path=str(plan_dir.relative_to(config.workspace_root)),
        files=files,
        created_at=created_at,
        topic_key=topic_key,
    )


def _pick_metadata_file(plan_dir: Path) -> Path | None:
    for filename in ("plan.md", "tasks.md"):
        candidate = plan_dir / filename
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _load_plan_metadata(metadata_path: Path) -> tuple[Mapping[str, object] | None, str]:
    raw_text = metadata_path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(raw_text)
    if match is None:
        return None, raw_text
    front_matter = match.group("front")
    body = match.group("body")
    try:
        metadata = load_yaml(front_matter)
    except YamlParseError:
        return None, body
    if not isinstance(metadata, Mapping):
        return None, body
    return metadata, body


def _collect_plan_files(plan_dir: Path) -> list[Path]:
    collected: list[Path] = []
    for child in sorted(plan_dir.iterdir()):
        collected.append(child)
    return collected


def _extract_title(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def _extract_summary(body: str, *, fallback: str) -> str:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return fallback
    for index, line in enumerate(lines):
        if line.startswith("# "):
            if index + 1 < len(lines):
                return lines[index + 1]
            break
    return lines[0]


def _path_created_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()
