"""Minimal tests for sopify_writer StateStore (P8 2-file model).

Covers only the protocol-kernel state writer invariants:
  - set/clear active_plan.json
  - set/clear current_handoff.json
  - handoff required fields + observability metadata injection
  - no retired state files produced
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from sopify_contracts import RuntimeHandoff
from sopify_writer.store import StateStore

# Pre-P8 state files retired by the 2-file model (active_plan + current_handoff).
# StateStore must never produce these; if a new state file is added, add it here too.
_RETIRED_STATE_FILES = (
    "current_run.json",
    "current_plan.json",
    "current_clarification.json",
    "current_decision.json",
    "current_gate_receipt.json",
    "current_archive_receipt.json",
)


class StateStoreActivePlanTests(unittest.TestCase):
    def test_set_active_plan_writes_plan_id_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.set_active_plan(plan_id="test_001")

            payload = json.loads(store.active_plan_path.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"plan_id": "test_001"})

    def test_get_active_plan_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            self.assertIsNone(store.get_active_plan())

    def test_get_active_plan_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.set_active_plan(plan_id="round_trip_001")
            result = store.get_active_plan()
            self.assertEqual(result, {"plan_id": "round_trip_001"})

    def test_clear_active_plan_removes_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.set_active_plan(plan_id="to_clear")
            self.assertTrue(store.active_plan_path.exists())

            store.clear_active_plan()
            self.assertFalse(store.active_plan_path.exists())
            self.assertIsNone(store.get_active_plan())

    def test_clear_active_plan_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.clear_active_plan()


class StateStoreHandoffTests(unittest.TestCase):
    def _make_handoff(self, **overrides: object) -> RuntimeHandoff:
        defaults = {
            "schema_version": "1",
            "plan_id": "test_handoff_001",
            "required_host_action": "continue_host_develop",
        }
        defaults.update(overrides)
        return RuntimeHandoff(**defaults)

    def test_set_current_handoff_writes_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.set_current_handoff(self._make_handoff())

            payload = json.loads(store.current_handoff_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1")
            self.assertEqual(payload["plan_id"], "test_handoff_001")
            self.assertEqual(payload["required_host_action"], "continue_host_develop")

    def test_set_current_handoff_injects_observability_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.set_current_handoff(self._make_handoff())

            payload = json.loads(store.current_handoff_path.read_text(encoding="utf-8"))
            obs = payload.get("observability", {})
            self.assertEqual(obs["state_kind"], "current_handoff")
            self.assertEqual(obs["writer"], "sopify_writer")
            self.assertIn("written_at", obs)

    def test_get_current_handoff_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            self.assertIsNone(store.get_current_handoff())

    def test_get_current_handoff_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            original = self._make_handoff(
                required_host_action="answer_questions",
                artifacts={"questions": [{"q": "scope?"}]},
            )
            store.set_current_handoff(original)

            loaded = store.get_current_handoff()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.plan_id, "test_handoff_001")
            self.assertEqual(loaded.required_host_action, "answer_questions")
            self.assertEqual(loaded.artifacts, {"questions": [{"q": "scope?"}]})

    def test_clear_current_handoff_removes_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state")
            store.set_current_handoff(self._make_handoff())
            self.assertTrue(store.current_handoff_path.exists())

            store.clear_current_handoff()
            self.assertFalse(store.current_handoff_path.exists())
            self.assertIsNone(store.get_current_handoff())


class StateStoreNoRetiredFilesTests(unittest.TestCase):
    def test_writer_does_not_produce_retired_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / "state"
            store = StateStore(state_dir)

            store.set_active_plan(plan_id="no_retired_001")
            store.set_current_handoff(
                RuntimeHandoff(
                    schema_version="1",
                    plan_id="no_retired_001",
                    required_host_action="continue_host_develop",
                )
            )

            for name in _RETIRED_STATE_FILES:
                self.assertFalse(
                    (state_dir / name).exists(),
                    f"Retired state file {name} should not be produced by StateStore",
                )

    def test_state_dir_contains_only_two_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / "state"
            store = StateStore(state_dir)

            store.set_active_plan(plan_id="two_files_001")
            store.set_current_handoff(
                RuntimeHandoff(
                    schema_version="1",
                    plan_id="two_files_001",
                )
            )

            files = sorted(p.name for p in state_dir.iterdir())
            self.assertEqual(files, ["active_plan.json", "current_handoff.json"])


if __name__ == "__main__":
    unittest.main()
