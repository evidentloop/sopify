"""Installed entry instructions resolve against the same host payload."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from installer.hosts import get_host_adapter
from installer.hosts.base import install_host_assets
from installer.payload import install_global_payload

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("host", ("claude", "codex", "qoder", "antigravity", "trae", "cursor", "copilot"))
@pytest.mark.parametrize("language", ("zh-CN", "en-US"))
def test_installed_entry_payload_paths(tmp_path, host, language):
    adapter = get_host_adapter(host)
    workspace = tmp_path / "project"
    workspace.mkdir()
    install_host_assets(
        adapter, repo_root=ROOT, home_root=tmp_path,
        workspace_root=workspace, language_directory=language,
    )
    if adapter.is_workspace_scope:
        entry = workspace / adapter.destination_dirname / adapter.header_filename
    elif adapter.is_user_plugin_scope:
        entry = tmp_path / adapter.instruction_file_relpath
    else:
        entry = adapter.destination_root(tmp_path) / adapter.header_filename
    text = entry.read_text(encoding="utf-8")
    if host == "copilot":
        assert "/sopify/helpers" not in text
        assert "payload-manifest.json" not in text
        assert "bundle_template_dir" not in text
        assert "from sopify_writer import ProtocolStore" not in text
        return

    install_global_payload(adapter, repo_root=ROOT, home_root=tmp_path)
    helper = re.search(r"python3 (~/\S+/sopify/helpers/bootstrap_workspace\.py)", text)[1]
    manifest = re.search(r"`(~/[^`]+/sopify/payload-manifest\.json)`", text)[1]
    helper_path = tmp_path / helper.removeprefix("~/")
    manifest_path = tmp_path / manifest.removeprefix("~/")
    assert helper_path.is_file()
    assert helper_path.parent.parent == manifest_path.parent
    bundle = manifest_path.parent / json.loads(manifest_path.read_text())["bundle_template_dir"]
    assert (bundle / "sopify_writer/__init__.py").is_file()
    assert "bundle_template_dir" in text and "sys.path" in text
    assert "from sopify_writer import ProtocolStore" in text
    assert "git check-ignore -q .sopify/state/active_plan.json" in text


def test_cloned_marker_repairs_local_ignores_with_existing_helper(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(HOME=str(home), GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def git(workspace, *args, check=True):
        return subprocess.run(
            ["git", *args], cwd=workspace, env=env,
            capture_output=True, text=True, check=check,
        )

    adapter = get_host_adapter("qoder")
    install_host_assets(adapter, repo_root=ROOT, home_root=home, language_directory="en-US")
    payload = install_global_payload(adapter, repo_root=ROOT, home_root=home)

    def bootstrap(workspace):
        result = subprocess.run(
            [sys.executable, str(payload.root / "helpers/bootstrap_workspace.py"),
             "--workspace-root", str(workspace), "--request", "~go",
             "--interaction-mode", "interactive"],
            env=env, capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-q")
    assert bootstrap(source)["action"] == "bootstrapped"
    git(source, "add", ".sopify/sopify.json")
    git(source, "-c", "user.name=Sopify Test", "-c", "user.email=sopify@example.invalid",
        "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}",
        "commit", "-qm", "fixture marker")
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(source), str(clone))
    marker = clone / ".sopify/sopify.json"
    marker_before = marker.read_bytes()
    state_path = ".sopify/state/active_plan.json"
    assert git(clone, "check-ignore", "-q", state_path, check=False).returncode == 1
    (clone / ".sopify/state").mkdir()
    (clone / state_path).write_text('{"plan_id":"fixture"}\n', encoding="utf-8")
    assert state_path in git(clone, "status", "--porcelain", "--untracked-files=all").stdout
    exclude = clone / ".git/info/exclude"
    exclude.write_text(exclude.read_text(encoding="utf-8") + "\n.local-only/\n", encoding="utf-8")

    assert bootstrap(clone)["action"] == "updated"
    assert git(clone, "check-ignore", "-q", state_path).returncode == 0
    assert git(clone, "status", "--porcelain", "--untracked-files=all").stdout == ""
    assert git(clone, "check-ignore", "-q", ".sopify/plan/new/plan.md", check=False).returncode == 1
    assert marker.read_bytes() == marker_before
    assert ".local-only/" in exclude.read_text(encoding="utf-8")
    assert exclude.read_text(encoding="utf-8").count("# BEGIN sopify-managed") == 1
    before_repeat = (exclude.read_bytes(), exclude.stat().st_mtime_ns)
    assert bootstrap(clone)["action"] == "skipped"
    assert (exclude.read_bytes(), exclude.stat().st_mtime_ns) == before_repeat
