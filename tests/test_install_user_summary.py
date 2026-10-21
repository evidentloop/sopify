# Test classification: distribution
"""Regressions for user-visible installation evidence and product names."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from installer.distribution import (
    DistributionRequest,
    DistributionSourceMetadata,
    _friendly_smoke_summary,
    render_distribution_user_result,
    run_distribution_install,
)
from scripts.install_sopify import run_install


def _cursor_summary(home_root: Path, language: str = "zh-CN") -> str:
    report = run_distribution_install(
        request=DistributionRequest(
            target=f"cursor:{language}",
            workspace=None,
            ref_override=None,
            interactive=False,
            source_channel="repo-local",
            source_metadata=DistributionSourceMetadata(
                resolved_ref="working-tree",
                asset_name="scripts/install_sopify.py",
            ),
        ),
        repo_root=REPO_ROOT,
        home_root=home_root,
        install_executor=run_install,
    )
    return render_distribution_user_result(report)


class InstallUserSummaryTests(unittest.TestCase):
    def test_old_python_stops_before_project_or_host_writes(self) -> None:
        runner = (
            "import runpy, sys; "
            "sys.version_info = (3, 9, 6); "
            "sys.argv = sys.argv[1:]; "
            "runpy.run_path(sys.argv[0], run_name='__main__')"
        )
        for script in ("install_sopify.py", "sopify_init.py"):
            for language in ("zh-CN", "en-US"):
                with self.subTest(script=script, language=language), tempfile.TemporaryDirectory() as temporary:
                    home = Path(temporary)
                    args = (
                        ["--target", f"qoder:{language}"] if script == "install_sopify.py"
                        else ["init", "--workspace", str(home), "--language", language]
                    )
                    completed = subprocess.run(
                        [sys.executable, "-c", runner, str(REPO_ROOT / "scripts" / script), *args],
                        env={**os.environ, "HOME": str(home), "LANG": "en_US.UTF-8"},
                        capture_output=True, text=True, check=False,
                    )
                    expected = (
                        "Sopify 需要 Python 3.11 或更新版本，当前为 3.9.6。"
                        if language == "zh-CN"
                        else "Sopify needs Python 3.11 or newer; current version: 3.9.6."
                    )
                    self.assertEqual(completed.returncode, 1)
                    self.assertEqual(completed.stderr.strip(), expected)
                    self.assertEqual(completed.stdout, "")
                    self.assertEqual(list(home.iterdir()), [])

    def test_passed_runtime_smoke_stays_translated(self) -> None:
        """A real passing smoke line is already translated; do not drop that branch."""
        self.assertEqual(
            _friendly_smoke_summary("Runtime smoke check passed: bundle ok\n", "zh-CN"),
            "运行时自检已通过。",
        )

    def test_empty_smoke_is_explicitly_not_run_in_both_languages(self) -> None:
        for empty in ("", " \n\t"):
            with self.subTest(output=empty):
                self.assertEqual(_friendly_smoke_summary(empty, "zh-CN"), "未执行运行时自检。")
                self.assertEqual(_friendly_smoke_summary(empty, "en-US"), "Runtime smoke check was not run.")
        self.assertEqual(
            _friendly_smoke_summary("Runtime smoke check passed: ok\n", "en-US"),
            "Runtime smoke check passed.",
        )

    def test_success_summary_does_not_print_empty_smoke_placeholder(self) -> None:
        """A finished install with no smoke output must not look like a missing check.

        Cursor has no smoke target, so every successful zh-CN install currently
        puts `(no smoke output)` under 诊断. The summary should not surface
        that English placeholder.
        """
        with tempfile.TemporaryDirectory() as home_dir:
            rendered = _cursor_summary(Path(home_dir))

        self.assertIn("Sopify 安装完成。", rendered)
        self.assertNotIn("(no smoke output)", rendered)
        self.assertIn("未执行运行时自检。", rendered)

    def test_cursor_summary_uses_the_product_display_name(self) -> None:
        """The next-step line should use the same Cursor name as the restart step.

        Both locales use the product name, never the raw adapter ID.
        """
        for language in ("zh-CN", "en-US"):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as home_dir:
                rendered = _cursor_summary(Path(home_dir), language)
                self.assertIn("打开 Cursor" if language == "zh-CN" else "Open Cursor", rendered)
                self.assertNotIn("打开 cursor", rendered)
                self.assertNotIn("Open cursor", rendered)
