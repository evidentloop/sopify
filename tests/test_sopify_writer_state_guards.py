# Test classification: distribution
"""Protocol-state regressions for sopify_writer.

Covers active_plan, current_handoff, and receipt writes that the existing
writer tests do not execute: handoff/plan disagreement, an occupied history
slot, and a provenance plan_version that does not match the package.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pytest

from sopify_contracts import RuntimeHandoff, inspect_plan_package
from sopify_writer import InvariantViolationError, ProtocolStore


def _write_light_plan(sopify_root: Path, plan_id: str) -> Path:
    plan_dir = sopify_root / "plan" / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "plan.md").write_text(
        "---\nlevel: light\n---\n\n# Test plan\n",
        encoding="utf-8",
    )
    return plan_dir


def _handoff(plan_id: str, **overrides: object) -> RuntimeHandoff:
    fields: dict[str, object] = {
        "schema_version": "1",
        "plan_id": plan_id,
        "required_host_action": "continue_host_develop",
    }
    fields.update(overrides)
    return RuntimeHandoff(**fields)


class ProtocolStoreStateGuardTests(unittest.TestCase):
    def test_set_active_plan_does_not_retarget_handoff(self) -> None:
        """Moving the active pointer must not silently rewrite the handoff plan.

        Resume reads both files. Coupling the writes would make a pointer
        switch look like the old handoff belongs to the new plan.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.set_active_plan(plan_id="plan_a")
            store.set_current_handoff(_handoff("plan_a", notes=("先问再写",)))
            store.set_active_plan(plan_id="plan_b")

            self.assertEqual(store.get_active_plan(), {"plan_id": "plan_b"})
            handoff = store.get_current_handoff()
            self.assertIsNotNone(handoff)
            self.assertEqual(handoff.plan_id, "plan_a")
            self.assertEqual(handoff.notes, ("先问再写",))
            raw = store.current_handoff_path.read_text(encoding="utf-8")
            self.assertIn("先问再写", raw)
            self.assertNotIn("\\u5148", raw)

    def test_handoff_preserves_caller_observability_and_overwrites_writer(self) -> None:
        """Caller observability keys survive; the writer identity does not.

        The store injects state_kind, writer, and written_at. Replacing the
        whole observability object would drop host-supplied keys, and leaving
        a caller-supplied writer would hide who wrote the file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            store.set_current_handoff(
                _handoff(
                    "plan_obs",
                    observability={"source": "host", "writer": "not-the-writer"},
                )
            )

            observability = json.loads(
                store.current_handoff_path.read_text(encoding="utf-8")
            )["observability"]
            self.assertEqual(observability["source"], "host")
            self.assertEqual(observability["writer"], "sopify_writer")
            self.assertEqual(observability["state_kind"], "current_handoff")
            self.assertIn("written_at", observability)

    def test_provenance_plan_version_conflict_writes_no_receipt(self) -> None:
        """A stale provenance plan_version must not create a receipt file.

        expected_plan_version is already rejected. provenance.plan_version is
        a second hash gate and has to fail before the exclusive create.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            plan_dir = _write_light_plan(store.root, "plan_001")
            current = inspect_plan_package(plan_dir).version

            with self.assertRaises(InvariantViolationError):
                store.write_plan_receipt(
                    plan_id="plan_001",
                    receipt_id="exec_001",
                    verdict="pass",
                    provenance={"plan_version": "sha256:stale"},
                )

            self.assertFalse((plan_dir / "receipts" / "exec_001.json").exists())

            written = store.write_plan_receipt(
                plan_id="plan_001",
                receipt_id="exec_001",
                verdict="pass",
                provenance={"plan_version": current},
                evidence={"note": "收据"},
            )
            payload = json.loads(written.read_text(encoding="utf-8"))
            self.assertEqual(payload["provenance"]["plan_version"], current)
            self.assertEqual(payload["evidence"]["note"], "收据")
            self.assertIn("收据", written.read_text(encoding="utf-8"))

    def test_finalize_rejects_mismatched_handoff_without_archiving(self) -> None:
        """Finalize must stop when the handoff still names another plan.

        The active pointer can match while the handoff does not. Archiving
        in that state would clear a handoff that does not belong to the plan.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            _write_light_plan(store.root, "target_001")
            store.set_active_plan(plan_id="target_001")
            store.set_current_handoff(_handoff("other_001"))

            with self.assertRaises(InvariantViolationError):
                store.finalize_plan(
                    plan_id="target_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A"],
                    month="2026-06",
                )

            self.assertTrue((store.root / "plan" / "target_001").is_dir())
            self.assertFalse((store.root / "history").exists())
            self.assertEqual(store.get_active_plan(), {"plan_id": "target_001"})
            self.assertEqual(store.get_current_handoff().plan_id, "other_001")
            self.assertFalse(
                (store.root / "plan" / "target_001" / "receipts" / "final.json").exists()
            )

    def test_finalize_does_not_replace_an_existing_history_plan(self) -> None:
        """An occupied history slot must stay byte-for-byte, including its marker.

        Finalize checks the archive directory before writing the final receipt.
        A retry against an existing archive must not delete that archive or
        clear the live pointer.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            _write_light_plan(store.root, "target_001")
            store.set_active_plan(plan_id="target_001")
            store.set_current_handoff(_handoff("target_001"))
            archive = store.root / "history" / "2026-06" / "target_001"
            archive.mkdir(parents=True)
            (archive / "keep.txt").write_text("keep\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                store.finalize_plan(
                    plan_id="target_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A"],
                    month="2026-06",
                )

            self.assertEqual((archive / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            self.assertTrue((store.root / "plan" / "target_001").is_dir())
            self.assertFalse(
                (store.root / "plan" / "target_001" / "receipts" / "final.json").exists()
            )
            self.assertEqual(store.get_active_plan(), {"plan_id": "target_001"})
            self.assertIsNotNone(store.get_current_handoff())

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "AUDIT-4: non-object active_plan.json makes finalize raise "
            "AttributeError instead of a protocol error"
        ),
    )
    def test_finalize_rejects_non_object_active_plan(self) -> None:
        """A non-object active pointer must be a protocol error, and must not archive.

        get_active_plan returns the raw JSON value. Finalize then calls .get
        on it. A list payload currently escapes as AttributeError instead of
        InvariantViolationError. The plan directory still has to stay put.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProtocolStore(Path(temp_dir))
            _write_light_plan(store.root, "target_001")
            store.set_active_plan(plan_id="target_001")
            store.active_plan_path.write_text("[]\n", encoding="utf-8")

            with self.assertRaises(InvariantViolationError):
                store.finalize_plan(
                    plan_id="target_001",
                    outcome="completed",
                    summary="Done.",
                    key_decisions=["A"],
                    month="2026-06",
                )

            self.assertTrue((store.root / "plan" / "target_001").is_dir())
            self.assertFalse((store.root / "history").exists())
