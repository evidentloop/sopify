# Test classification: distribution
"""Regressions for user-visible installation evidence and product names."""

from __future__ import annotations

from pathlib import Path
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
