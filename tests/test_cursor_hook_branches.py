# Test classification: distribution
"""Branches in installer/cursor_hook.py that tests/test_cursor_hooks.py does not lock.

The helper copies the plan-package rules instead of calling inspect_plan_package.
These tests keep sessionStart aligned with that contract, and keep the write
guard on the tool and shell shapes the existing file does not execute.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from installer.cursor_hook import handle, main
from sopify_contracts import PLAN_FILES_BY_LEVEL, inspect_plan_package


def _enable_workspace(root: Path) -> Path:
    (root / ".sopify").mkdir(parents=True, exist_ok=True)
    return root


def _write_package(plan_dir: Path, level: str, *, plan_md: str | None = None) -> None:
    plan_dir.mkdir(parents=True, exist_ok=True)
    if plan_md is None:
        plan_md = f"---\nlevel: {level}\n---\n# Plan\n"
    (plan_dir / "plan.md").write_text(plan_md, encoding="utf-8")
    for name in PLAN_FILES_BY_LEVEL[level][1:]:
        (plan_dir / name).write_text(f"# {name}\n", encoding="utf-8")


def _point_at(workspace: Path, plan_id: str) -> None:
    state = workspace / ".sopify" / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "active_plan.json").write_text(
        json.dumps({"plan_id": plan_id}),
        encoding="utf-8",
    )


def _session(workspace: Path) -> dict[str, object]:
    return handle(
        {
            "hook_event_name": "sessionStart",
            "workspace_roots": [str(workspace)],
        }
    )


class CursorHookUncoveredBranchTests(unittest.TestCase):
    def test_session_start_follows_plan_package_contract(self) -> None:
        """sessionStart must accept exactly the packages inspect_plan_package accepts.

        The hook reimplements the level and semantic-file rules. A standard or
        architecture package, or a light package that also has background.md,
        must not drift from the writer contract.
        """
        for level in PLAN_FILES_BY_LEVEL:
            with self.subTest(level=level):
                with tempfile.TemporaryDirectory() as workspace_dir:
                    workspace = _enable_workspace(Path(workspace_dir))
                    plan_id = f"plan_{level}"
                    plan_dir = workspace / ".sopify" / "plan" / plan_id
                    _write_package(plan_dir, level)
                    _point_at(workspace, plan_id)

                    self.assertTrue(inspect_plan_package(plan_dir).valid)
                    self.assertIn(
                        f"active_plan: {plan_id}",
                        _session(workspace)["additional_context"],
                    )

                    (plan_dir / "background.md").write_text("legacy\n", encoding="utf-8")
                    self.assertFalse(inspect_plan_package(plan_dir).valid)
                    self.assertEqual(_session(workspace), {})

    def test_session_start_rejects_incomplete_or_unclosed_frontmatter(self) -> None:
        """A standard plan without tasks.md, or an unclosed frontmatter, is not active."""
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            plan_dir = workspace / ".sopify" / "plan" / "plan_std"
            _write_package(plan_dir, "standard")
            (plan_dir / "tasks.md").unlink()
            _point_at(workspace, "plan_std")

            self.assertFalse(inspect_plan_package(plan_dir).valid)
            self.assertEqual(_session(workspace), {})

            (plan_dir / "tasks.md").write_text("# Tasks\n", encoding="utf-8")
            (plan_dir / "plan.md").write_text("---\nlevel: standard\n# no close\n", encoding="utf-8")
            self.assertEqual(_session(workspace), {})

    def test_session_start_accepts_one_quoted_level_only(self) -> None:
        """Quoted level tokens are part of the package contract; two levels are not."""
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            plan_dir = workspace / ".sopify" / "plan" / "plan_std"
            _write_package(
                plan_dir,
                "standard",
                plan_md='---\nlevel: "standard"\n---\n# Plan\n',
            )
            _point_at(workspace, "plan_std")

            self.assertIn("active_plan: plan_std", _session(workspace)["additional_context"])

            (plan_dir / "plan.md").write_text(
                "---\nlevel: light\nlevel: standard\n---\n# Plan\n",
                encoding="utf-8",
            )
            self.assertEqual(_session(workspace), {})

    def test_session_start_ignores_plan_id_outside_the_token_pattern(self) -> None:
        """The active pointer has to be the same token the writer accepts.

        A value that is not letters, digits, and underscores must not be
        injected as an active plan.
        """
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            _point_at(workspace, "plan.std")
            plan_dir = workspace / ".sopify" / "plan" / "plan.std"
            _write_package(plan_dir, "light")

            self.assertEqual(_session(workspace), {})

    def test_session_start_orders_zulu_timestamps_ahead_of_older_offsets(self) -> None:
        """A Zulu timestamp is a real receipt time, not a missing timestamp."""
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            plan_dir = workspace / ".sopify" / "plan" / "plan_a"
            receipts = plan_dir / "receipts"
            _write_package(plan_dir, "light")
            receipts.mkdir()
            (receipts / "exec_001.json").write_text(
                json.dumps({"timestamp": "2026-08-19T09:00:00+00:00", "provenance": {"receipt_id": "exec_001"}}),
                encoding="utf-8",
            )
            (receipts / "exec_002.json").write_text(
                json.dumps({"timestamp": "2026-08-19T10:00:00Z", "provenance": {"receipt_id": "exec_002"}}),
                encoding="utf-8",
            )
            _point_at(workspace, "plan_a")

            self.assertIn("latest_receipt: exec_002", _session(workspace)["additional_context"])

            (receipts / "exec_002.json").write_text(
                json.dumps({"timestamp": "not-a-date", "provenance": {"receipt_id": "exec_002"}}),
                encoding="utf-8",
            )
            self.assertIn("latest_receipt: exec_001", _session(workspace)["additional_context"])

    def test_pre_tool_use_denies_delete_and_notebook_edits_of_machine_truth(self) -> None:
        """Delete and notebook edits are mutating tools; Read is not.

        Dropping delete or notebook_path from the guard would let those tools
        rewrite handoff or receipt files while StrReplace stayed blocked.
        """
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            deleted = handle(
                {
                    "hook_event_name": "preToolUse",
                    "cwd": str(workspace),
                    "tool_name": "Delete",
                    "tool_input": {"path": ".sopify/state/current_handoff.json"},
                }
            )
            notebook = handle(
                {
                    "hook_event_name": "preToolUse",
                    "cwd": str(workspace),
                    "tool_name": "EditNotebook",
                    "tool_input": {
                        "notebook_path": ".sopify/plan/plan_a/receipts/exec_001.json",
                        "new_source": "x",
                    },
                }
            )
            read = handle(
                {
                    "hook_event_name": "preToolUse",
                    "cwd": str(workspace),
                    "tool_name": "Read",
                    "tool_input": {"path": ".sopify/state/active_plan.json"},
                }
            )

            self.assertEqual(deleted["permission"], "deny")
            self.assertEqual(notebook["permission"], "deny")
            self.assertEqual(read, {"permission": "allow"})

    def test_pre_tool_use_uses_tool_input_cwd_for_a_relative_path(self) -> None:
        """Some events put cwd only inside tool_input. The relative path still resolves."""
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            result = handle(
                {
                    "hook_event_name": "preToolUse",
                    "tool_name": "Write",
                    "tool_input": {
                        "path": ".sopify/state/active_plan.json",
                        "cwd": str(workspace),
                        "contents": "{}",
                    },
                }
            )

            self.assertEqual(result["permission"], "deny")

    def test_before_shell_denies_rm_tee_and_absolute_redirects(self) -> None:
        """Obvious deletes and redirects stay denied beyond the echo-with-space case.

        rm, tee, an absolute path that contains a space, and a stderr redirect
        are write shapes the existing shell test does not execute.
        """
        with tempfile.TemporaryDirectory() as parent_dir:
            workspace = _enable_workspace(Path(parent_dir) / "ws dir")
            absolute = f"{workspace}/.sopify/state/active_plan.json"
            cases = {
                "rm": "rm -f .sopify/state/active_plan.json",
                "tee": "echo '{}' | tee .sopify/state/current_handoff.json",
                "absolute": f"echo '{{}}' > '{absolute}'",
                "stderr": "cmd 2>.sopify/state/current_handoff.json",
            }
            for name, command in cases.items():
                with self.subTest(command=name):
                    result = handle(
                        {
                            "hook_event_name": "beforeShellExecution",
                            "cwd": str(workspace),
                            "command": command,
                        }
                    )
                    self.assertEqual(result["permission"], "deny")

            self.assertEqual(
                handle(
                    {
                        "hook_event_name": "beforeShellExecution",
                        "cwd": str(workspace),
                        "command": "rm -f README.md",
                    }
                ),
                {"permission": "allow"},
            )
            self.assertEqual(
                handle(
                    {
                        "hook_event_name": "beforeShellExecution",
                        "command": "rm -f .sopify/state/active_plan.json",
                    }
                ),
                {"permission": "allow"},
            )

    def test_main_emits_one_json_line_for_a_valid_session(self) -> None:
        """The success path must print the handler result, not the fail-open object."""
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = _enable_workspace(Path(workspace_dir))
            plan_dir = workspace / ".sopify" / "plan" / "plan_a"
            _write_package(plan_dir, "light")
            _point_at(workspace, "plan_a")
            raw = json.dumps(
                {
                    "hook_event_name": "sessionStart",
                    "workspace_roots": [str(workspace)],
                }
            )
            with patch("sys.stdin", io.StringIO(raw)), patch("sys.stdout", io.StringIO()) as out:
                exit_code = main()

            rendered = out.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertEqual(rendered.count("\n"), 1)
            payload = json.loads(rendered)
            self.assertIn("active_plan: plan_a", payload["additional_context"])
