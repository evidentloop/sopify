"""Tests for sopify_writer ProtocolStore (P8 protocol asset writer).

Covers:
  - State management: set/clear active_plan.json, set/clear current_handoff.json
  - Handoff observability metadata injection
  - Plan receipts: write, validate receipt_id pattern, plan_id/receipt_id conflict
  - History receipts: write Markdown, validate required fields
  - Finalize: write final receipt + history receipt + clear state
  - No retired state files produced
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import tempfile
import unittest
from unittest.mock import patch

from sopify_contracts import RuntimeHandoff
from sopify_writer import InvariantViolationError, ProtocolStore
from sopify_writer.io import write_json_exclusive

# Pre-P8 state files retired by the 2-file model (active_plan + current_handoff).
# ProtocolStore must never produce these; if a new state file is added, add it here too.
_RETIRED_STATE_FILES = (
    "current_run.json",
    "current_plan.json",
    "current_clarification.json",
    "current_decision.json",
    "current_gate_receipt.json",
    "current_archive_receipt.json",
)


def _write_plan_package(sopify_root: Path, plan_id: str, level: str = "light") -> Path:
    plan_dir = sopify_root / "plan" / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "plan.md").write_text(
        f"---\nlevel: {level}\n---\n\n# Test plan\n",
        encoding="utf-8",
    )
    if level in {"standard", "architecture"}:
        (plan_dir / "tasks.md").write_text("# Tasks\n", encoding="utf-8")
    if level == "architecture":
        (plan_dir / "design.md").write_text("# Design\n", encoding="utf-8")
    return plan_dir


class ProtocolStoreActivePlanTests(unittest.TestCase):
    def test_set_active_plan_writes_plan_id_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.set_active_plan(plan_id="test_001")

            payload = json.loads(store.active_plan_path.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"plan_id": "test_001"})

    def test_get_active_plan_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            self.assertIsNone(store.get_active_plan())

    def test_get_active_plan_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.set_active_plan(plan_id="round_trip_001")
            result = store.get_active_plan()
            self.assertEqual(result, {"plan_id": "round_trip_001"})

    def test_clear_active_plan_removes_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.set_active_plan(plan_id="to_clear")
            self.assertTrue(store.active_plan_path.exists())

            store.clear_active_plan()
            self.assertFalse(store.active_plan_path.exists())
            self.assertIsNone(store.get_active_plan())

    def test_clear_active_plan_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.clear_active_plan()

    def test_set_active_plan_empty_plan_id_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            for bad_id in ("", "   ", "../escape", "bad-id", "bad/name"):
                with self.subTest(plan_id=bad_id):
                    with self.assertRaises(InvariantViolationError):
                        store.set_active_plan(plan_id=bad_id)


class ProtocolStoreHandoffTests(unittest.TestCase):
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
            store = ProtocolStore(Path(temp_dir))
            store.set_current_handoff(self._make_handoff())

            payload = json.loads(store.current_handoff_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1")
            self.assertEqual(payload["plan_id"], "test_handoff_001")
            self.assertEqual(payload["required_host_action"], "continue_host_develop")

    def test_set_current_handoff_injects_observability_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.set_current_handoff(self._make_handoff())

            payload = json.loads(store.current_handoff_path.read_text(encoding="utf-8"))
            obs = payload.get("observability", {})
            self.assertEqual(obs["state_kind"], "current_handoff")
            self.assertEqual(obs["writer"], "sopify_writer")
            self.assertIn("written_at", obs)

    def test_get_current_handoff_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            self.assertIsNone(store.get_current_handoff())

    def test_get_current_handoff_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
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
            store = ProtocolStore(Path(temp_dir))
            store.set_current_handoff(self._make_handoff())
            self.assertTrue(store.current_handoff_path.exists())

            store.clear_current_handoff()
            self.assertFalse(store.current_handoff_path.exists())
            self.assertIsNone(store.get_current_handoff())


class ProtocolStorePlanReceiptTests(unittest.TestCase):
    def _store(self, temp_dir: str, plan_id: str = "plan_001") -> ProtocolStore:
        store = ProtocolStore(Path(temp_dir))
        _write_plan_package(store.root, plan_id)
        return store

    def test_write_exec_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            path = store.write_plan_receipt(
                plan_id="plan_001",
                receipt_id="exec_001",
                verdict="pass",
                evidence={"files_changed": 3},
            )

            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["verdict"], "pass")
            self.assertEqual(payload["evidence"], {"files_changed": 3})
            self.assertEqual(payload["provenance"]["plan_id"], "plan_001")
            self.assertEqual(payload["provenance"]["receipt_id"], "exec_001")
            self.assertRegex(
                payload["provenance"]["plan_version"], r"^sha256:[0-9a-f]{64}$"
            )
            self.assertIn("timestamp", payload)

    def test_write_verify_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            path = store.write_plan_receipt(
                plan_id="plan_001",
                receipt_id="verify_002",
                verdict="pass",
            )

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["provenance"]["receipt_id"], "verify_002")

    def test_existing_receipt_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            path = store.write_plan_receipt(
                plan_id="plan_001",
                receipt_id="verify_001",
                verdict="pass",
                evidence={"source": "first"},
            )
            original = path.read_bytes()

            with self.assertRaises(FileExistsError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="verify_001",
                    verdict="fail",
                    evidence={"source": "second"},
                )

            self.assertEqual(path.read_bytes(), original)

    def test_concurrent_receipt_writes_create_exactly_one_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            barrier = Barrier(2)
            original_write = write_json_exclusive

            def synchronized_write(path: Path, payload: dict[str, object]) -> None:
                barrier.wait()
                original_write(path, payload)

            def write(source: str) -> str:
                try:
                    store.write_plan_receipt(
                        plan_id="plan_001",
                        receipt_id="verify_001",
                        verdict="pass",
                        evidence={"source": source},
                    )
                except FileExistsError:
                    return "exists"
                return "created"

            with (
                patch(
                    "sopify_writer.store.write_json_exclusive",
                    side_effect=synchronized_write,
                ),
                ThreadPoolExecutor(max_workers=2) as pool,
            ):
                results = list(pool.map(write, ("first", "second")))

            self.assertCountEqual(results, ["created", "exists"])
            receipt = json.loads(
                (
                    Path(temp_dir)
                    / "plan"
                    / "plan_001"
                    / "receipts"
                    / "verify_001.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn(receipt["evidence"]["source"], {"first", "second"})

    def test_receipt_id_pattern_rejects_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            for bad_id in ("exec_1", "exec_0001", "final_001", "EXEC_001", "", "foo"):
                with self.subTest(receipt_id=bad_id):
                    with self.assertRaises(InvariantViolationError):
                        store.write_plan_receipt(
                            plan_id="plan_001",
                            receipt_id=bad_id,
                            verdict="pass",
                        )

    def test_receipt_id_pattern_accepts_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            for valid_id in (
                "exec_001",
                "exec_999",
                "verify_001",
                "verify_100",
                "final",
            ):
                with self.subTest(receipt_id=valid_id):
                    path = store.write_plan_receipt(
                        plan_id="plan_001",
                        receipt_id=valid_id,
                        verdict="pass",
                    )
                    self.assertTrue(path.exists())

    def test_empty_verdict_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="exec_001",
                    verdict="",
                )

    def test_empty_plan_id_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="",
                    receipt_id="exec_001",
                    verdict="pass",
                )

    def test_provenance_plan_id_conflict_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="exec_001",
                    verdict="pass",
                    provenance={"plan_id": "wrong_plan"},
                )

    def test_provenance_receipt_id_conflict_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="exec_001",
                    verdict="pass",
                    provenance={"receipt_id": "wrong_receipt"},
                )

    def test_provenance_passthrough_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            path = store.write_plan_receipt(
                plan_id="plan_001",
                receipt_id="exec_001",
                verdict="pass",
                provenance={"session_id": "sess_abc", "host": "codex"},
            )

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["provenance"]["session_id"], "sess_abc")
            self.assertEqual(payload["provenance"]["host"], "codex")
            self.assertEqual(payload["provenance"]["plan_id"], "plan_001")

    def test_expected_plan_version_conflict_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)

            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="exec_001",
                    verdict="pass",
                    expected_plan_version="sha256:stale",
                )

    def test_invalid_plan_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self._store(temp_dir)
            (store.root / "plan" / "plan_001" / "background.md").write_text(
                "legacy", encoding="utf-8"
            )

            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="exec_001",
                    verdict="pass",
                )


class ProtocolStoreHistoryReceiptTests(unittest.TestCase):
    def test_write_history_receipt_default_month(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            path = store.write_history_receipt(
                plan_id="plan_001",
                outcome="completed",
                summary="All tasks done.",
                key_decisions=["Use protocol-first approach"],
            )

            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertIn("outcome: completed", content)
            self.assertIn("## Summary", content)
            self.assertIn("All tasks done.", content)
            self.assertIn("## Key Decisions", content)
            self.assertIn("- Use protocol-first approach", content)

    def test_write_history_receipt_explicit_month(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            path = store.write_history_receipt(
                plan_id="plan_001",
                outcome="completed",
                summary="Done.",
                key_decisions=["Decision A"],
                month="2026-06",
            )

            expected = (
                Path(temp_dir) / "history" / "2026-06" / "plan_001" / "receipt.md"
            )
            self.assertEqual(path, expected)

    def test_empty_outcome_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            with self.assertRaises(InvariantViolationError):
                store.write_history_receipt(
                    plan_id="plan_001",
                    outcome="",
                    summary="Done.",
                    key_decisions=["A"],
                )

    def test_empty_summary_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            with self.assertRaises(InvariantViolationError):
                store.write_history_receipt(
                    plan_id="plan_001",
                    outcome="completed",
                    summary="",
                    key_decisions=["A"],
                )

    def test_empty_key_decisions_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            with self.assertRaises(InvariantViolationError):
                store.write_history_receipt(
                    plan_id="plan_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=[],
                )

    def test_key_decisions_with_empty_item_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            with self.assertRaises(InvariantViolationError):
                store.write_history_receipt(
                    plan_id="plan_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A", ""],
                )

    def test_empty_plan_id_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            for bad_id in ("", "   "):
                with self.subTest(plan_id=bad_id):
                    with self.assertRaises(InvariantViolationError):
                        store.write_history_receipt(
                            plan_id=bad_id,
                            outcome="completed",
                            summary="Done.",
                            key_decisions=["A"],
                        )

    def test_empty_month_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            for bad_month in ("", "2026-7", "2026-13", "../../escaped"):
                with self.subTest(month=bad_month):
                    with self.assertRaises(InvariantViolationError):
                        store.write_history_receipt(
                            plan_id="plan_001",
                            outcome="completed",
                            summary="Done.",
                            key_decisions=["A"],
                            month=bad_month,
                        )

    def test_multiple_key_decisions_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            path = store.write_history_receipt(
                plan_id="plan_001",
                outcome="completed",
                summary="Done.",
                key_decisions=["Decision A", "Decision B", "Decision C"],
                month="2026-06",
            )

            content = path.read_text(encoding="utf-8")
            self.assertIn("- Decision A", content)
            self.assertIn("- Decision B", content)
            self.assertIn("- Decision C", content)


class ProtocolStoreFinalizeTests(unittest.TestCase):
    def _setup_active_plan(self, store: ProtocolStore, plan_id: str) -> None:
        _write_plan_package(store.root, plan_id)
        store.set_active_plan(plan_id=plan_id)
        store.set_current_handoff(
            RuntimeHandoff(
                schema_version="1",
                plan_id=plan_id,
                required_host_action="continue_host_develop",
            )
        )

    def test_finalize_writes_both_receipts_and_clears_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            self._setup_active_plan(store, "finalize_001")

            result = store.finalize_plan(
                plan_id="finalize_001",
                outcome="completed",
                summary="All waves delivered.",
                key_decisions=["Protocol-first cutover"],
                evidence={"waves_completed": 3},
                month="2026-06",
            )

            # Final receipt written
            self.assertTrue(result["final_receipt"].exists())
            final_payload = json.loads(
                result["final_receipt"].read_text(encoding="utf-8")
            )
            self.assertEqual(final_payload["verdict"], "finalized")
            self.assertEqual(final_payload["evidence"], {"waves_completed": 3})
            self.assertEqual(final_payload["provenance"]["plan_id"], "finalize_001")
            self.assertEqual(final_payload["provenance"]["receipt_id"], "final")

            # History receipt written
            self.assertTrue(result["history_receipt"].exists())
            history_content = result["history_receipt"].read_text(encoding="utf-8")
            self.assertIn("outcome: completed", history_content)

            # State cleared
            self.assertIsNone(store.get_active_plan())
            self.assertIsNone(store.get_current_handoff())

    def test_finalize_clears_state_even_when_no_prior_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            _write_plan_package(store.root, "no_state_001")

            result = store.finalize_plan(
                plan_id="no_state_001",
                outcome="completed",
                summary="Done.",
                key_decisions=["A"],
                month="2026-06",
            )

            self.assertTrue(result["final_receipt"].exists())
            self.assertTrue(result["history_receipt"].exists())
            self.assertIsNone(store.get_active_plan())
            self.assertIsNone(store.get_current_handoff())

    def test_finalize_receipt_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            _write_plan_package(store.root, "paths_001")

            result = store.finalize_plan(
                plan_id="paths_001",
                outcome="completed",
                summary="Done.",
                key_decisions=["A"],
                month="2026-06",
            )

            expected_final = (
                Path(temp_dir)
                / "history"
                / "2026-06"
                / "paths_001"
                / "receipts"
                / "final.json"
            )
            expected_history = (
                Path(temp_dir) / "history" / "2026-06" / "paths_001" / "receipt.md"
            )
            self.assertEqual(result["final_receipt"], expected_final)
            self.assertEqual(result["history_receipt"], expected_history)
            self.assertEqual(
                result["archive_dir"],
                Path(temp_dir) / "history" / "2026-06" / "paths_001",
            )

    def test_finalize_version_conflict_preserves_plan_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            self._setup_active_plan(store, "conflict_001")

            with self.assertRaises(InvariantViolationError):
                store.finalize_plan(
                    plan_id="conflict_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A"],
                    month="2026-06",
                    expected_plan_version="sha256:stale",
                )

            self.assertTrue((store.root / "plan" / "conflict_001").is_dir())
            self.assertIsNotNone(store.get_active_plan())
            self.assertIsNotNone(store.get_current_handoff())
            self.assertFalse(
                (store.root / "history" / "2026-06" / "conflict_001").exists()
            )

    def test_finalize_rejects_history_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            self._setup_active_plan(store, "escape_001")

            with self.assertRaises(InvariantViolationError):
                store.finalize_plan(
                    plan_id="escape_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A"],
                    month="../../escaped",
                )

            self.assertTrue((store.root / "plan" / "escape_001").is_dir())
            self.assertIsNotNone(store.get_active_plan())
            self.assertFalse((store.root.parent / "escaped" / "escape_001").exists())

    def test_finalize_archive_failure_preserves_plan_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            self._setup_active_plan(store, "failure_001")

            with patch("pathlib.Path.rename", side_effect=OSError("rename failed")):
                with self.assertRaises(OSError):
                    store.finalize_plan(
                        plan_id="failure_001",
                        outcome="completed",
                        summary="Done.",
                        key_decisions=["A"],
                        month="2026-06",
                    )

            plan_dir = store.root / "plan" / "failure_001"
            self.assertTrue(plan_dir.is_dir())
            self.assertFalse((plan_dir / "receipts" / "final.json").exists())
            self.assertFalse((plan_dir / "receipt.md").exists())
            self.assertIsNotNone(store.get_active_plan())
            self.assertIsNotNone(store.get_current_handoff())

    def test_finalize_rejects_mismatched_active_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            _write_plan_package(store.root, "target_001")
            store.set_active_plan(plan_id="other_001")

            with self.assertRaises(InvariantViolationError):
                store.finalize_plan(
                    plan_id="target_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A"],
                    month="2026-06",
                )

            self.assertTrue((store.root / "plan" / "target_001").is_dir())
            self.assertEqual(store.get_active_plan(), {"plan_id": "other_001"})


class ProtocolStoreNoRetiredFilesTests(unittest.TestCase):
    def test_writer_does_not_produce_retired_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sopify_root = Path(temp_dir)
            store = ProtocolStore(sopify_root)
            _write_plan_package(sopify_root, "no_retired_001")

            store.set_active_plan(plan_id="no_retired_001")
            store.set_current_handoff(
                RuntimeHandoff(
                    schema_version="1",
                    plan_id="no_retired_001",
                    required_host_action="continue_host_develop",
                )
            )
            store.write_plan_receipt(
                plan_id="no_retired_001",
                receipt_id="exec_001",
                verdict="pass",
            )
            store.finalize_plan(
                plan_id="no_retired_001",
                outcome="completed",
                summary="Done.",
                key_decisions=["A"],
                month="2026-06",
            )

            state_dir = sopify_root / "state"
            for name in _RETIRED_STATE_FILES:
                self.assertFalse(
                    (state_dir / name).exists(),
                    f"Retired state file {name} should not be produced by ProtocolStore",
                )

    def test_state_dir_contains_only_two_files_during_active_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sopify_root = Path(temp_dir)
            store = ProtocolStore(sopify_root)

            store.set_active_plan(plan_id="two_files_001")
            store.set_current_handoff(
                RuntimeHandoff(
                    schema_version="1",
                    plan_id="two_files_001",
                )
            )

            state_dir = sopify_root / "state"
            files = sorted(p.name for p in state_dir.iterdir())
            self.assertEqual(files, ["active_plan.json", "current_handoff.json"])

    def test_state_dir_empty_after_finalize(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sopify_root = Path(temp_dir)
            store = ProtocolStore(sopify_root)
            _write_plan_package(sopify_root, "clear_after_001")

            store.set_active_plan(plan_id="clear_after_001")
            store.set_current_handoff(
                RuntimeHandoff(
                    schema_version="1",
                    plan_id="clear_after_001",
                )
            )
            store.finalize_plan(
                plan_id="clear_after_001",
                outcome="completed",
                summary="Done.",
                key_decisions=["A"],
                month="2026-06",
            )

            state_dir = sopify_root / "state"
            if state_dir.exists():
                files = list(state_dir.iterdir())
                self.assertEqual(files, [], "State dir should be empty after finalize")


if __name__ == "__main__":
    unittest.main()
