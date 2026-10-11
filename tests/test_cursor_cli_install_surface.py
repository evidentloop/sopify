# Test classification: distribution
"""Regression tests for the Cursor CLI entry added in #73.

The installer change touched cursor_plugin.py, hosts/base.py, and
inspection.py. These tests lock the behaviors that a content-only README
assertion does not: the top-level Skill is part of the install contract,
Doctor fails closed when it is missing, and the CLI behavior check stays an
unverified best-effort recommendation.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from installer.cursor_plugin import install_cursor_user_plugin_assets
from installer.hosts.codex import CODEX_ADAPTER
from installer.hosts.cursor import CURSOR_ADAPTER
from installer.inspection import build_doctor_payload
from installer.models import InstallError


def _cursor_checks(home_root: Path) -> dict[str, dict[str, object]]:
    doctor = build_doctor_payload(home_root=home_root, workspace_root=None)
    return {
        check["check_id"]: check
        for check in doctor["checks"]
        if check.get("host_id") == "cursor"
    }


def _snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class CursorCliInstallSurfaceTests(unittest.TestCase):
    def test_cursor_contract_includes_top_level_cli_skill(self) -> None:
        """Dropping SKILL.md from the Cursor path list must fail this test.

        hosts/base.py added that file to global_skill_paths, and the user
        Plugin expected paths are built from the same list. Codex does not
        install this entry.
        """
        home = Path("/tmp/sopify-cursor-contract-home")
        cli_entry = home / ".cursor" / "skills" / "sopify" / "SKILL.md"
        self.assertIn(cli_entry, CURSOR_ADAPTER.global_skill_paths(home))
        self.assertIn(cli_entry, CURSOR_ADAPTER.expected_paths(home))
        self.assertNotIn(
            home / ".codex" / "skills" / "sopify" / "SKILL.md",
            CODEX_ADAPTER.expected_paths(home),
        )

    def test_doctor_fails_when_only_the_cli_entry_is_missing(self) -> None:
        """A Cursor install without the top-level Skill is not a healthy skill tree.

        Phase skills can all be present while SKILL.md is gone. Doctor must
        report that hole instead of treating the tree as installed.
        """
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)
            install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="CN",
            )
            cli_entry = home_root / ".cursor" / "skills" / "sopify" / "SKILL.md"
            cli_entry.unlink()

            skill_tree = _cursor_checks(home_root)["global_skill_tree_present"]

            self.assertEqual(skill_tree["status"], "fail")
            self.assertEqual(skill_tree["reason_code"], "MISSING_REQUIRED_FILE")
            self.assertTrue(
                any(str(cli_entry) in item for item in skill_tree.get("evidence", []))
            )

    def test_cli_behavior_recommendation_stays_best_effort(self) -> None:
        """The CLI check must not go back to claiming the entry is unsupported.

        inspection.py now tells the operator to run a managed-entry black box
        and to keep Skill selection separate from file installation. File
        presence still must not flip this check to pass.
        """
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)
            install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="CN",
            )
            checks = _cursor_checks(home_root)
            cli = checks["cursor_cli_behavior"]
            ide = checks["cursor_ide_behavior"]

            self.assertEqual(cli["status"], "skip")
            self.assertEqual(cli["reason_code"], "BLACK_BOX_NOT_VERIFIED")
            recommendation = str(cli.get("recommendation") or "")
            self.assertIn("managed-entry", recommendation)
            self.assertIn("best-effort", recommendation)
            self.assertIn("separate from file installation evidence", recommendation)
            self.assertNotIn("not a supported CLI entry", recommendation)
            self.assertIn(
                "file presence alone is not behavior evidence",
                str(ide.get("recommendation") or ""),
            )

    def test_language_switch_replaces_cli_entry(self) -> None:
        """A later cursor:en-US install must not leave the zh-CN CLI entry in place."""
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)
            install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="CN",
            )
            updated = install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="EN",
            )
            installed = (
                home_root / ".cursor" / "skills" / "sopify" / "SKILL.md"
            ).read_text(encoding="utf-8")
            canonical = (
                REPO_ROOT / "skills" / "en" / "cursor-cli-skill.md.template"
            ).read_text(encoding="utf-8")

            self.assertEqual(updated.action, "updated")
            self.assertEqual(installed, canonical)
            self.assertNotIn("顶层入口", installed)

    def test_missing_cli_skill_source_does_not_remove_existing_install(self) -> None:
        """Source checks happen before the plugin directory is replaced.

        A checkout that lost cursor-cli-skill.md.template must fail closed
        and leave the previous Plugin and Skill bytes untouched.
        """
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as repo_dir:
            home_root = Path(home_dir)
            install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="CN",
            )
            before = _snapshot(home_root / ".cursor")

            source = Path(repo_dir) / "skills" / "zh"
            source.mkdir(parents=True)
            for name in (
                "cursor-plugin-rule.mdc.template",
                "cursor-plugin-readme.md.template",
            ):
                shutil.copy(REPO_ROOT / "skills" / "zh" / name, source / name)

            with self.assertRaisesRegex(InstallError, "Missing source Cursor CLI Skill"):
                install_cursor_user_plugin_assets(
                    CURSOR_ADAPTER,
                    repo_root=Path(repo_dir),
                    home_root=home_root,
                    language_directory="CN",
                )

            self.assertEqual(_snapshot(home_root / ".cursor"), before)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "AUDIT-1: reinstall reports skipped while a required phase skill "
            "still differs from the packaged source tree"
        ),
    )
    def test_reinstall_restores_phase_skill_that_differs_from_source(self) -> None:
        """Rerunning the Cursor install must not claim the tree is current when it is not.

        analyze/SKILL.md is a required Doctor path. If its bytes diverge from
        the source tree, a repair install has to rewrite it. Skipping leaves
        the divergence in place while the host action is skipped.
        """
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)
            install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="CN",
            )
            phase_skill = home_root / ".cursor" / "skills" / "sopify" / "analyze" / "SKILL.md"
            source = (
                REPO_ROOT / "skills" / "zh" / "skills" / "sopify" / "analyze" / "SKILL.md"
            ).read_text(encoding="utf-8")
            phase_skill.write_text("truncated\n", encoding="utf-8")

            repaired = install_cursor_user_plugin_assets(
                CURSOR_ADAPTER,
                repo_root=REPO_ROOT,
                home_root=home_root,
                language_directory="CN",
            )

            self.assertNotEqual(repaired.action, "skipped")
            self.assertEqual(phase_skill.read_text(encoding="utf-8"), source)
