"""Migration, shared instruction blocks and repair in disposable homes."""

from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from installer.hosts.base import install_host_assets, render_single_file
from installer.hosts.claude import CLAUDE_ADAPTER
from installer.hosts.codex import CODEX_ADAPTER
from installer.hosts.copilot import COPILOT_ADAPTER
from installer.hosts.cursor import CURSOR_ADAPTER
from installer.hosts.qoder import QODER_ADAPTER
from installer.models import InstallError

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- BEGIN SOPIFY MANAGED BLOCK -->"
END = "<!-- END SOPIFY MANAGED BLOCK -->"
HOME_HOSTS = [CLAUDE_ADAPTER, CODEX_ADAPTER, QODER_ADAPTER]
BLOCK_HOSTS = [*HOME_HOSTS, COPILOT_ADAPTER]


def install(adapter, home, language="CN", repo=ROOT):
    return install_host_assets(
        adapter, repo_root=repo, home_root=home, language_directory=language,
        workspace_root=home / "workspace" if adapter.is_workspace_scope else None,
    )


def header_path(adapter, home):
    root = home / "workspace" if adapter.is_workspace_scope else home
    path = adapter.destination_root(root) / adapter.header_filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def rendered_header(adapter, language="CN"):
    source = adapter.instruction_source(ROOT, language)
    if adapter.is_workspace_scope:
        return render_single_file(source, source.parent / "skills/sopify", adapter)
    return source.read_text(encoding="utf-8").replace("{{config_dir}}", adapter.config_dir or "")


def snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("adapter", BLOCK_HOSTS, ids=lambda a: a.host_name)
def test_user_only_header_is_preserved_and_reinstall_is_idempotent(tmp_path, adapter):
    path = header_path(adapter, tmp_path)
    original = b"# My instructions\r\n\r\nKeep my settings.\r\n\r\n"
    path.write_bytes(original)
    install(adapter, tmp_path)
    once = path.read_bytes()
    assert once.startswith(original)
    assert once.count(BEGIN.encode()) == once.count(END.encode()) == 1
    assert install(adapter, tmp_path).action == "skipped"
    assert path.read_bytes() == once


@pytest.mark.parametrize("adapter,old_language,newline,mixed", [
    (CODEX_ADAPTER, "zh", "\n", False),
    (CLAUDE_ADAPTER, "en", "\n", False),
    (QODER_ADAPTER, "en", "\r\n", True),
    (CODEX_ADAPTER, "zh", "\r\n", True),
], ids=["codex-august-whole", "claude-june-whole", "qoder-june-mixed-crlf", "codex-august-mixed-crlf"])
def test_legacy_migration_is_version_independent(tmp_path, adapter, old_language, newline, mixed):
    """Actual June/August bodies migrate even after the new template changes."""
    home, repo = tmp_path / "home", tmp_path / "repo"
    old = (ROOT / f"tests/fixtures/legacy-home-headers/{old_language}.md").read_text(
        encoding="utf-8",
    ).replace("{{config_dir}}", adapter.config_dir or "")
    prefix, suffix = ("My rules\r\n\r\n", "\nMy trailing rule") if mixed else ("", "")
    path = header_path(adapter, home)
    path.write_bytes((prefix + old.replace("\n", newline) + suffix).encode())
    shutil.copytree(ROOT / "skills/zh", repo / "skills/zh")
    new = "<!-- SOPIFY_VERSION: 2099-01-01.000000 -->\n# New concise rules\n"
    (repo / "skills/zh/header.md.template").write_text(new, encoding="utf-8")
    assert install(adapter, home, repo=repo).action == "updated"
    assert path.read_bytes() == f"{prefix}{BEGIN}\n{new.strip()}\n{END}{newline}{suffix}".encode()
    assert install(adapter, home, repo=repo).action == "skipped"


@pytest.mark.parametrize("damage", [
    "missing_start", "missing_end", "duplicate_start", "duplicate_range",
    "missing_version", "malformed_version", "duplicate_version",
])
def test_ambiguous_legacy_header_is_rejected_without_writes(tmp_path, damage):
    # Parser cases need one home host; all three are wired by the migration test.
    install(CODEX_ADAPTER, tmp_path)
    path = header_path(CODEX_ADAPTER, tmp_path)
    old = rendered_header(CODEX_ADAPTER)
    start, end = old.splitlines()[0], old.splitlines()[-1]
    version = next(line for line in old.splitlines() if "SOPIFY_VERSION:" in line)
    changes = {
        "missing_start": old.replace(start, ""),
        "missing_end": old.replace(end, ""),
        "duplicate_start": start + "\n" + old,
        "duplicate_range": old + old,
        "missing_version": old.replace(version, ""),
        "malformed_version": old.replace(version, version.removesuffix(" -->")),
        "duplicate_version": old.replace(version, version + "\n" + version),
    }
    path.write_text(changes[damage] + "\nUser additions\n", encoding="utf-8")
    before = snapshot(tmp_path)
    with pytest.raises(InstallError, match="(?i)migration.*incomplete"):
        install(CODEX_ADAPTER, tmp_path)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("adapter", BLOCK_HOSTS, ids=lambda a: a.host_name)
def test_valid_managed_block_repairs_content_and_preserves_outside_bytes(tmp_path, adapter):
    path = header_path(adapter, tmp_path)
    prefix, suffix = b"User prefix\r\n\r\n", b"\n\nUser suffix without final newline"
    content = rendered_header(adapter).strip()
    stale = content.replace("~go finalize", "~go broken")  # same version, different content
    path.write_bytes(prefix + f"{BEGIN}\n{stale}\n{END}".encode() + suffix)
    assert install(adapter, tmp_path).action == "updated"
    assert path.read_bytes() == prefix + f"{BEGIN}\n{content}\n{END}".encode() + suffix
    assert install(adapter, tmp_path).action == "skipped"


@pytest.mark.parametrize("adapter", [CODEX_ADAPTER, COPILOT_ADAPTER], ids=lambda a: a.host_name)
@pytest.mark.parametrize("damage", ["missing_end", "missing_begin", "reversed", "duplicate", "nested"])
def test_malformed_markers_fail_without_writes(tmp_path, adapter, damage):
    valid = f"{BEGIN}\n{rendered_header(adapter).strip()}\n{END}"
    broken = {
        "missing_end": BEGIN + "\nuser rules", "missing_begin": "user rules\n" + END,
        "reversed": END + "\nuser rules\n" + BEGIN,
        "duplicate": valid + "\n" + valid, "nested": BEGIN + "\n" + valid,
    }[damage]
    path = header_path(adapter, tmp_path)
    path.write_text(broken, encoding="utf-8")
    before = snapshot(tmp_path)
    with pytest.raises(InstallError, match="(?i)managed block"):
        install(adapter, tmp_path)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("adapter", [CODEX_ADAPTER, CURSOR_ADAPTER], ids=lambda a: a.host_name)
@pytest.mark.parametrize("relative,damage", [
    ("develop/SKILL.md", "missing"), ("analyze/SKILL.md", "corrupt"),
    ("references/shared-writing-dna.md", "corrupt"),
    ("analyze/scripts/score_requirement.py", "corrupt"), ("obsolete-owned-file.txt", "extra"),
])
def test_reinstall_repairs_the_complete_owned_tree(tmp_path, adapter, relative, damage):
    # Cover both implementations, rather than three copies of the home adapter.
    install(adapter, tmp_path)
    skills = adapter.destination_root(tmp_path) / "skills"
    unrelated = skills / "my-personal-skill/SKILL.md"
    unrelated.parent.mkdir()
    unrelated.write_bytes(b"# My skill\n")
    damaged = skills / "sopify" / relative
    if damage == "missing":
        damaged.unlink()
    else:
        damaged.write_bytes(b"damaged\n")
    assert install(adapter, tmp_path).action == "updated"
    if damage == "extra":
        assert not damaged.exists()
    else:
        assert damaged.read_bytes() == (
            adapter.source_root(ROOT, "CN") / "skills/sopify" / relative
        ).read_bytes()
    assert unrelated.read_bytes() == b"# My skill\n"
    assert install(adapter, tmp_path).action == "skipped"


@pytest.mark.parametrize("adapter", [*HOME_HOSTS, CURSOR_ADAPTER], ids=lambda a: a.host_name)
def test_language_switch_and_ignored_cache_preserve_other_skills(tmp_path, adapter):
    install(adapter, tmp_path)
    root = adapter.destination_root(tmp_path)
    unrelated = root / "skills/my-other-skill/SKILL.md"
    unrelated.parent.mkdir()
    unrelated.write_bytes(b"keep\n")
    ignored = root / "skills/sopify/analyze/__pycache__/x.pyc"
    ignored.parent.mkdir()
    ignored.write_bytes(b"cache")
    assert install(adapter, tmp_path).action == "skipped"
    assert install(adapter, tmp_path, "EN").action == "updated"
    assert (root / "skills/sopify/develop/SKILL.md").read_bytes() == (
        adapter.source_root(ROOT, "EN") / "skills/sopify/develop/SKILL.md"
    ).read_bytes()
    if adapter in HOME_HOSTS:
        assert rendered_header(adapter, "EN").strip() in header_path(adapter, tmp_path).read_text()
    assert unrelated.read_bytes() == b"keep\n"
    assert install(adapter, tmp_path, "EN").action == "skipped"


def test_standalone_helper_uses_strict_blocks_and_preserves_outside_bytes(tmp_path):
    helper = tmp_path / "bootstrap_workspace.py"
    shutil.copyfile(ROOT / "installer/bootstrap_workspace.py", helper)
    # -I prevents importing the repository: exercise the standalone deployment.
    result = subprocess.run([sys.executable, "-I", "-c", """
import pathlib, runpy, sys
module = runpy.run_path(sys.argv[1])
upsert, remove = module['upsert_managed_instruction_block'], module['_remove_managed_instruction_block']
path = pathlib.Path(sys.argv[1]).with_name('instructions.md')
prefix, suffix = b'user\\r\\n\\r\\n', b'\\nend without newline'
begin, end = b'<!-- BEGIN SOPIFY MANAGED BLOCK -->', b'<!-- END SOPIFY MANAGED BLOCK -->'
path.write_bytes(prefix + begin + b'\\nold\\n' + end + suffix)
assert upsert(path, 'new')
assert path.read_bytes() == prefix + begin + b'\\nnew\\n' + end + suffix
assert remove(path)
assert path.read_bytes() == prefix + suffix
for operation in (lambda: upsert(path, 'new'), lambda: remove(path)):
    broken = begin + b'\\nbroken'
    path.write_bytes(broken)
    try:
        operation()
    except ValueError:
        pass
    else:
        raise AssertionError('malformed block was accepted')
    assert path.read_bytes() == broken
""", str(helper)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
