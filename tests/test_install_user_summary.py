# Test classification: distribution
"""User-visible install summary gaps found by running the documented installer.

These are the summary strings a zh-CN Cursor install prints. The assertions
are the behavior the summary should have; current output fails them.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

import pytest

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


def _cursor_zh_summary(home_root: Path) -> str:
    report = run_distribution_install(
        request=DistributionRequest(
            target="cursor:zh-CN",
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

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "AUDIT-2: zh-CN success summary prints the English placeholder "
            "(no smoke output) when smoke did not run"
        ),
    )
    def test_success_summary_does_not_print_empty_smoke_placeholder(self) -> None:
        """A finished install with no smoke output must not look like a missing check.

        Cursor has no smoke target, so every successful zh-CN install currently
        puts `(no smoke output)` under 诊断. The summary should not surface
        that English placeholder.
        """
        with tempfile.TemporaryDirectory() as home_dir:
            rendered = _cursor_zh_summary(Path(home_dir))

        self.assertIn("Sopify 安装完成。", rendered)
        self.assertNotIn("(no smoke output)", rendered)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "AUDIT-3: cursor is missing from the host display-name map, "
            "so the zh-CN summary says 打开 cursor"
        ),
    )
    def test_cursor_summary_uses_the_product_display_name(self) -> None:
        """The next-step line should use the same Cursor name as the restart step.

        Codex and Claude are mapped to product names. cursor falls through to
        the raw host id, so the summary says 打开 cursor next to 重启 Cursor.
        """
        with tempfile.TemporaryDirectory() as home_dir:
            rendered = _cursor_zh_summary(Path(home_dir))

        self.assertIn("重启 Cursor", rendered)
        self.assertIn("打开 Cursor", rendered)
        self.assertNotIn("打开 cursor", rendered)
