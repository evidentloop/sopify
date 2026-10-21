"""Installed entry instructions resolve against the same host payload."""

import json
from pathlib import Path
import re

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
