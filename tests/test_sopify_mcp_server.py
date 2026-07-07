# Test classification: contract
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from sopify_contracts import RuntimeHandoff
from sopify_writer import ProtocolStore

from scripts.sopify_mcp_server import (
    _safe_tool,
    get_mcp_dependency_hint,
    protocol_check,
    read_active_plan,
    read_current_handoff,
    resolve_workspace_root,
    write_plan_receipt,
    workspace_status_lite,
)
from scripts.sopify_protocol_check import run_protocol_check


def _write_plan_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Test Plan",
                "",
                "## Context / Why",
                "Context.",
                "",
                "## Scope",
                "Scope.",
                "",
                "## Approach",
                "Approach.",
                "",
                "## Waves / Steps",
                "- [ ] Step.",
                "",
                "## Key Decisions",
                "- Decision.",
                "",
                "## Constraints / Not-in-scope",
                "- Constraint.",
                "",
                "## Status / Progress",
                "Draft.",
                "",
                "## Next",
                "Continue.",
                "",
            ]
        ),
        encoding="utf-8",
    )


class SopifyMcpServerCoreTests(unittest.TestCase):
    def test_resolve_workspace_root_rejects_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            with self.assertRaises(ValueError):
                resolve_workspace_root(missing)

    def test_active_plan_and_handoff_are_read_through_protocol_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            store = ProtocolStore(workspace / ".sopify")
            store.set_active_plan(plan_id="plan_001")
            store.set_current_handoff(
                RuntimeHandoff(
                    schema_version="1",
                    plan_id="plan_001",
                    required_host_action="continue_host_develop",
                )
            )

            self.assertEqual(read_active_plan(workspace), {"plan_id": "plan_001"})
            handoff = read_current_handoff(workspace)
            self.assertIsNotNone(handoff)
            self.assertEqual(handoff["plan_id"], "plan_001")
            self.assertEqual(handoff["required_host_action"], "continue_host_develop")

    def test_active_plan_returns_none_when_state_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertIsNone(read_active_plan(Path(temp_dir)))

    def test_current_handoff_returns_none_when_state_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertIsNone(read_current_handoff(Path(temp_dir)))

    def test_workspace_status_lite_reports_missing_sopify_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status = workspace_status_lite(Path(temp_dir))

            self.assertFalse(status["sopify_exists"])
            self.assertFalse(status["paths"]["blueprint"])
            self.assertFalse(status["paths"]["plan"])
            self.assertFalse(status["paths"]["history"])
            self.assertFalse(status["paths"]["state"])
            self.assertIsNone(status["active_plan"])
            self.assertIsNone(status["active_plan_dir_exists"])
            self.assertFalse(status["handoff_exists"])

    def test_workspace_status_lite_reports_active_plan_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            sopify = workspace / ".sopify"
            plan_id = "plan_001"
            (sopify / "blueprint").mkdir(parents=True)
            (sopify / "history").mkdir()
            (sopify / "plan" / plan_id).mkdir(parents=True)
            ProtocolStore(sopify).set_active_plan(plan_id=plan_id)

            status = workspace_status_lite(workspace)

            self.assertTrue(status["sopify_exists"])
            self.assertTrue(status["paths"]["blueprint"])
            self.assertTrue(status["paths"]["plan"])
            self.assertTrue(status["paths"]["history"])
            self.assertTrue(status["paths"]["state"])
            self.assertEqual(status["active_plan"], {"plan_id": plan_id})
            self.assertTrue(status["active_plan_dir_exists"])
            self.assertFalse(status["handoff_exists"])

    def test_protocol_check_function_matches_cli_result_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_id = "plan_001"
            sopify = workspace / ".sopify"
            ProtocolStore(sopify).set_active_plan(plan_id=plan_id)
            _write_plan_md(sopify / "plan" / plan_id / "plan.md")

            result = protocol_check(workspace, "new-plan")

            self.assertEqual(result["scenario"], "new-plan")
            self.assertEqual(result["verdict"], "PASS")
            self.assertEqual(result["failures"], [])
            self.assertEqual(result["evidence"], {"fixture": str(workspace)})
            self.assertEqual(result, run_protocol_check(workspace, "new-plan"))

    def test_protocol_check_reports_invalid_scenario_without_throwing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_protocol_check(Path(temp_dir), "bad")

            self.assertEqual(result["scenario"], "bad")
            self.assertEqual(result["verdict"], "FAIL")
            self.assertIn("Unsupported scenario", result["failures"][0])

    def test_mcp_dependency_hint_pins_stable_sdk_line(self) -> None:
        hint = get_mcp_dependency_hint()
        self.assertIn("mcp[cli]>=1.27,<2", hint)


class SopifyMcpServerWritePlanReceiptTests(unittest.TestCase):
    def test_write_plan_receipt_writes_current_active_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_id = "plan_001"
            sopify = workspace / ".sopify"
            ProtocolStore(sopify).set_active_plan(plan_id=plan_id)
            _write_plan_md(sopify / "plan" / plan_id / "plan.md")

            result = write_plan_receipt(
                workspace,
                plan_id,
                "exec_001",
                "PASS",
                {"ok": True},
                {"actor": "test"},
            )

            receipt_path = Path(result["path"])
            self.assertEqual(receipt_path.name, "exec_001.json")
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["verdict"], "PASS")
            self.assertEqual(payload["evidence"], {"ok": True})
            self.assertEqual(payload["provenance"]["actor"], "test")
            self.assertEqual(payload["provenance"]["plan_id"], plan_id)
            self.assertEqual(payload["provenance"]["receipt_id"], "exec_001")

    def test_write_plan_receipt_rejects_missing_active_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                write_plan_receipt(Path(temp_dir), "plan_001", "exec_001", "PASS")

    def test_write_plan_receipt_rejects_non_active_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            sopify = workspace / ".sopify"
            ProtocolStore(sopify).set_active_plan(plan_id="plan_001")
            _write_plan_md(sopify / "plan" / "plan_001" / "plan.md")

            with self.assertRaises(ValueError):
                write_plan_receipt(workspace, "plan_002", "exec_001", "PASS")

    def test_write_plan_receipt_rejects_existing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_id = "plan_001"
            sopify = workspace / ".sopify"
            ProtocolStore(sopify).set_active_plan(plan_id=plan_id)
            _write_plan_md(sopify / "plan" / plan_id / "plan.md")
            write_plan_receipt(workspace, plan_id, "exec_001", "PASS")

            with self.assertRaises(FileExistsError):
                write_plan_receipt(workspace, plan_id, "exec_001", "PASS")

    def test_write_plan_receipt_rejects_missing_plan_md(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_id = "plan_001"
            ProtocolStore(workspace / ".sopify").set_active_plan(plan_id=plan_id)

            with self.assertRaises(ValueError):
                write_plan_receipt(workspace, plan_id, "exec_001", "PASS")

    def test_write_plan_receipt_invalid_workspace_uses_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"

            result = _safe_tool(
                "write_plan_receipt",
                write_plan_receipt,
                missing,
                "plan_001",
                "exec_001",
                "PASS",
            )

            self.assertIsNone(result["write_plan_receipt"])
            self.assertEqual(result["error"]["code"], "ValueError")
            self.assertIn("workspace_root does not exist", result["error"]["message"])


class SopifyMcpServerScriptSmokeTests(unittest.TestCase):
    def test_main_explains_missing_sdk_when_mcp_is_not_installed(self) -> None:
        try:
            import mcp  # noqa: F401
        except ModuleNotFoundError:
            self.assertIn("mcp[cli]>=1.27,<2", get_mcp_dependency_hint())
        else:
            self.assertTrue(True)
