"""Antigravity and Trae share flat installs; every home here is disposable."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from installer.hosts import get_host_adapter, get_host_capability
from installer.hosts.base import install_host_assets
from installer.inspection import build_doctor_payload, build_status_payload
from installer.models import InstallError, parse_install_target
from scripts.install_sopify import run_install

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("antigravity", "trae")
STAGES = ("analyze", "design", "develop", "kb", "templates")
BEGIN = "<!-- BEGIN SOPIFY MANAGED BLOCK -->"
END = "<!-- END SOPIFY MANAGED BLOCK -->"


def install(host, home, language="zh-CN", repo=ROOT):
    return install_host_assets(
        get_host_adapter(host), repo_root=repo, home_root=home,
        language_directory=language,
    )


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("host", HOSTS)
def test_flat_registration_and_default_language(host):
    adapter = get_host_adapter(host)
    assert parse_install_target(host).language == "en-US"
    for language in ("zh-CN", "en-US"):
        assert parse_install_target(f"{host}:{language}").language == language
    capability = get_host_capability(host)
    assert capability.support_tier.value == "baseline_supported"
    assert [mode.value for mode in capability.entry_modes] == ["prompt_only"]
    assert adapter.flat_skills and not adapter.requires_workspace
    assert capability.declared_enhancements == ()


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("language", ("zh-CN", "en-US"))
def test_flat_install_repair_switch_and_preserve_user_content(tmp_path, host, language):
    adapter = get_host_adapter(host)
    root = adapter.destination_root(tmp_path)
    entry = root / adapter.header_filename
    # Shared rule prose must survive in both global AGENTS and entry Skill.
    entry.parent.mkdir(parents=True)
    metadata = (ROOT / adapter.entry_skill_template).read_bytes() if adapter.entry_skill_template else b""
    prefix, suffix = b"My instructions\r\n\r\n", b"\nMy trailing rule"
    entry.write_bytes(metadata + prefix)
    unrelated = {
        "skills/my-skill/SKILL.md": b"my own skill",
        "hooks.json": b'{"user_hook":true}',
        "traecli.toml": b"model = 'unchanged'",
        "settings.json": b'{"user_setting":true}',
    }
    if host == "trae":
        unrelated["AGENTS.md"] = b"My existing global rule"
    for rel, content in unrelated.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    install(host, tmp_path, language)
    entry.write_bytes(entry.read_bytes() + suffix)
    once = snapshot(root)
    assert install(host, tmp_path, language).action == "skipped"
    assert snapshot(root) == once
    assert entry.read_bytes().startswith(metadata + prefix)
    assert entry.read_bytes().endswith(suffix)
    assert entry.read_text().count(BEGIN) == entry.read_text().count(END) == 1
    assert not (root / "skills/sopify/analyze").exists()

    # Missing/edited resources and extra owned files must all repair, even when
    # the version and top-level Skill files still match.
    for rel in (
        "skills/sopify-design/assets/plan-template.md",
        "skills/sopify/references/output-contract.md",
        "skills/sopify-analyze/scripts/score_requirement.py",
    ):
        path = root / rel
        path.unlink()
    edited = root / "skills/sopify-develop/references/develop-rules.md"
    edited.write_text("corrupted", encoding="utf-8")
    extra = root / "skills/sopify-kb/stale.md"
    extra.write_text("stale", encoding="utf-8")
    if host == "trae":
        entry.write_bytes(entry.read_bytes().replace(b"name: sopify\n", b"name: damaged\n"))
    assert install(host, tmp_path, language).action == "updated"
    assert snapshot(root) == once

    other = "en-US" if language == "zh-CN" else "zh-CN"
    assert install(host, tmp_path, other).action == "updated"
    assert f"lang={other}" in entry.read_text()
    assert entry.read_bytes().startswith(metadata + prefix)
    assert entry.read_bytes().endswith(suffix)
    assert install(host, tmp_path, other).action == "skipped"
    for rel, content in unrelated.items():
        assert (root / rel).read_bytes() == content
    assert not (root / "sopify/helpers/cursor_hook.py").exists()
    if host == "trae":
        assert entry.read_text().startswith("---\nname: sopify\n")


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("language", ("zh-CN", "en-US"))
def test_installed_flat_references_and_scripts_resolve(tmp_path, host, language):
    adapter = get_host_adapter(host)
    install(host, tmp_path, language)
    skills = adapter.destination_root(tmp_path) / "skills"
    checked = 0
    for path in skills.rglob("*.md"):
        text = path.read_text()
        assert "skills/zh/skills/sopify/" not in text
        assert "skills/en/skills/sopify/" not in text
        if path.name == "SKILL.md":
            metadata = text.split("---", 2)[1]
            name = re.search(r"(?m)^name: (.+)$", metadata)[1]
            description = re.search(r"(?m)^description: (.+)$", metadata)[1]
            assert name == path.parent.name
            assert 0 < len(description) <= 1024
        # Resource paths in code spans; templates' future project links are
        # examples inside fences, not installed Skill resources.
        for ref in re.findall(r"`((?:\.\./|references/|assets/|scripts/)[^`\n]+)`", text):
            target = path.parent / ref
            assert list(target.parent.glob(target.name)), (path, ref)
            checked += 1
        for stage in re.findall(r"`(sopify-(?:analyze|design|develop|kb|templates))`", text):
            assert (skills / stage / "SKILL.md").is_file()
        for portable in re.findall(r"~/(?:\.gemini/config|\.trae)/skills/[A-Za-z0-9_./-]+", text):
            assert (tmp_path / portable.removeprefix("~/")).is_file(), (path, portable)
    assert checked >= 20
    assert len(list(skills.rglob("shared-writing-dna.md"))) == 1
    command = re.search(
        r"python3 (~/\S+/score_requirement.py)",
        (skills / "sopify-analyze/SKILL.md").read_text(),
    )[1]
    result = subprocess.run(
        [sys.executable, str(tmp_path / command.removeprefix("~/")),
         "--goal-clarity", "2", "--expected-outcome", "2",
         "--scope-boundary", "1", "--constraints", "1", "--require-score", "7"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)


@pytest.mark.parametrize("host", HOSTS)
def test_relative_cross_stage_links_are_rewritten_in_resources(tmp_path, host):
    repo, home = tmp_path / "repo", tmp_path / "home"
    shutil.copytree(ROOT / "skills", repo / "skills")
    resource = repo / "skills/en/skills/sopify/analyze/references/analyze-rules.md"
    with resource.open("a") as stream:
        stream.write("\n[Design](../../design/SKILL.md)\n`../../references/output-contract.md`\n")
    install(host, home, "en-US", repo)
    skills = get_host_adapter(host).destination_root(home) / "skills"
    installed = skills / "sopify-analyze/references/analyze-rules.md"
    text = installed.read_text()
    assert "../../sopify-design/SKILL.md" in text
    assert "../../sopify/references/output-contract.md" in text
    for ref in ("../../sopify-design/SKILL.md", "../../sopify/references/output-contract.md"):
        assert (installed.parent / ref).is_file()


@pytest.mark.parametrize("host", HOSTS)
def test_malformed_shared_entry_fails_before_any_host_write(tmp_path, host):
    install(host, tmp_path)
    adapter = get_host_adapter(host)
    entry = adapter.destination_root(tmp_path) / adapter.header_filename
    entry.write_text(entry.read_text().replace(END, ""), encoding="utf-8")
    before = snapshot(tmp_path)
    with pytest.raises(InstallError):
        install(host, tmp_path, "en-US")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("host", HOSTS)
def test_doctor_separates_installation_from_behavior(tmp_path, host):
    adapter = get_host_adapter(host)
    root = adapter.destination_root(tmp_path)
    root.mkdir(parents=True)
    (root / "settings.json").write_text("{}")

    def checks():
        return {c["check_id"]: c for c in build_doctor_payload(
            home_root=tmp_path, workspace_root=None,
        )["checks"] if c.get("host_id") == host}

    assert checks()["host_prompt_present"]["status"] == "skip"
    result = run_install(repo_root=ROOT, target_value=host, home_root=tmp_path, workspace_value=None)
    assert result.workspace_bootstrap is None
    installed = checks()
    for key in ("host_prompt_present", "global_skill_tree_present", "payload_present"):
        assert installed[key]["status"] == "pass"
    behavior = installed[f"{host}_cli_behavior"]
    assert (behavior["status"], behavior["reason_code"]) == ("skip", "BLACK_BOX_NOT_VERIFIED")
    assert not any("hooks" in key for key in installed)
    assert all((root / rel).is_file() for rel in ("sopify/payload-manifest.json", "sopify/helpers/bootstrap_workspace.py"))
    assert run_install(repo_root=ROOT, target_value=host, home_root=tmp_path, workspace_value=None).host_install.action == "skipped"
    (root / "skills/sopify/references/output-contract.md").unlink()
    assert checks()["global_skill_tree_present"]["status"] == "fail"
    state = next(h for h in build_status_payload(home_root=tmp_path, workspace_root=None)["hosts"] if h["host_id"] == host)
    assert state["state"]["installed"] == "no"
    assert not (tmp_path / ".sopify").exists()
