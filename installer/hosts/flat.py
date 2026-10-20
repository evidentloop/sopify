"""One flat Skill projection for hosts that discover only direct children."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory

from installer.bootstrap_workspace import upsert_managed_instruction_block
from installer.hosts.base import HostAdapter, read_sopify_version, skill_tree_matches
from installer.models import InstallError, InstallPhaseResult

STAGES = ("analyze", "design", "develop", "kb", "templates")
_IGNORE = shutil.ignore_patterns(".DS_Store", "Thumbs.db", "__pycache__")


def _flat_path(path: Path) -> Path:
    first, *rest = path.parts
    return Path(f"sopify-{first}", *rest) if first in STAGES else Path("sopify", *path.parts)


def _rewrite_text(text: str, *, source: Path, source_root: Path, config_dir: str) -> str:
    """Relocate real source references, leaving project/template examples intact."""
    text = text.replace("{{config_dir}}", config_dir)
    for stage in STAGES:
        text = text.replace(f"`{stage}`", f"`sopify-{stage}`")
        text = re.sub(rf"(?m)^name: {stage}$", f"name: sopify-{stage}", text)
    # Repository-relative executable examples must work from any user project.
    text = re.sub(
        r"skills/(?:zh|en)/skills/sopify/([A-Za-z0-9_./-]+)",
        lambda match: f"{config_dir}/skills/{_flat_path(Path(match[1])).as_posix()}",
        text,
    )
    # Markdown links and code spans use the same relative-path spelling. Only
    # relocate files in the source tree, never future .sopify project artifacts.
    def relocate(match: re.Match[str]) -> str:
        candidate = (source.parent / match[0]).resolve()
        if not candidate.is_file() or not candidate.is_relative_to(source_root.resolve()):
            return match[0]
        target = _flat_path(candidate.relative_to(source_root.resolve()))
        parent = _flat_path(source.relative_to(source_root)).parent
        return Path(os.path.relpath(target, parent)).as_posix()

    return re.sub(r"(?:\.\./)+[A-Za-z0-9_./-]+", relocate, text)


def install_flat_host_assets(
    adapter: HostAdapter, *, repo_root: Path, home_root: Path, language_directory: str,
) -> InstallPhaseResult:
    """Render first, then update only the owned flat directories and entry block."""
    source = adapter.source_root(repo_root, language_directory) / "skills" / "sopify"
    header_source = adapter.instruction_source(repo_root, language_directory)
    for required in (
        header_source,
        *(source / stage / "SKILL.md" for stage in STAGES),
        source / "references/shared-writing-dna.md",
        source / "references/output-contract.md",
    ):
        if not required.is_file():
            raise InstallError(f"Missing source file: {required}")
    root = adapter.destination_root(home_root)
    entry = root / adapter.header_filename
    action = "updated" if root.exists() else "installed"
    header = _rewrite_text(
        header_source.read_text(encoding="utf-8"), source=header_source,
        source_root=source, config_dir=adapter.config_dir or "",
    )
    # Add exact locations to the existing routing table, without a second list.
    for stage in STAGES:
        header = header.replace(
            f"| `sopify-{stage}` |",
            f"| `sopify-{stage}` (`{adapter.config_dir}/skills/sopify-{stage}/SKILL.md`) |",
        )

    with TemporaryDirectory(prefix="sopify-flat-") as temporary:
        staged = Path(temporary)
        for child in source.iterdir():
            if child.is_dir() and child.name in (*STAGES, "references"):
                target = staged / _flat_path(Path(child.name))
                shutil.copytree(child, target, ignore=_IGNORE)
                for path in target.rglob("*.md"):
                    original = child / path.relative_to(target)
                    path.write_text(_rewrite_text(
                        path.read_text(encoding="utf-8"), source=original,
                        source_root=source, config_dir=adapter.config_dir or "",
                    ), encoding="utf-8")

        # Stage the shared file too: malformed markers fail before any host write.
        staged_entry = staged / "entry.md"
        if entry.exists():
            shutil.copyfile(entry, staged_entry)
        if adapter.entry_skill_template:
            metadata = (repo_root / adapter.entry_skill_template).read_bytes()
            body = staged_entry.read_bytes() if staged_entry.exists() else b""
            # The entry's identity is owned; preserve user prose outside its
            # managed body while repairing missing or edited Skill metadata.
            body = re.sub(rb"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", b"", body, count=1, flags=re.S)
            staged_entry.write_bytes(metadata + body)
        try:
            upsert_managed_instruction_block(staged_entry, header, migrate_legacy=True)
        except ValueError as exc:
            raise InstallError(str(exc)) from exc
        entry_changed = not entry.is_file() or entry.read_bytes() != staged_entry.read_bytes()
        # Keep the entry separate from the owned shared-reference directory so
        # user text around its managed block survives language switches/repairs.
        trees = [
            (staged / f"sopify-{stage}", root / "skills" / f"sopify-{stage}")
            for stage in STAGES
        ]
        trees.append((staged / "sopify/references", root / "skills/sopify/references"))
        changed_trees = [(src, dst) for src, dst in trees if not skill_tree_matches(src, dst)]
        if not entry_changed and not changed_trees:
            action = "skipped"
        else:
            if entry_changed:
                entry.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(staged_entry, entry)
            for src, dst in changed_trees:
                if dst.exists():
                    shutil.rmtree(dst)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst)

    return InstallPhaseResult(
        action=action, root=root, version=read_sopify_version(header_source),
        paths=adapter.expected_paths(home_root),
    )
