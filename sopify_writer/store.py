"""Unified writer for Sopify P8 protocol assets.

ProtocolStore is the single write entry point for all protocol state,
receipts, and finalize operations. It manages three directory trees under
the `.sopify/` root:

  state/
    active_plan.json      Minimal plan_id pointer.
    current_handoff.json  Recovery context + required_host_action.

  plan/<plan_id>/receipts/
    exec_NNN.json         Execution receipts.
    verify_NNN.json       Verification receipts.
    final.json            Final receipt written at plan completion.

  history/<YYYY-MM>/<plan_id>/
    receipt.md            Auditable Markdown receipt at finalize time.

Finalize moves a validated plan package into history before clearing state.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from sopify_contracts import RuntimeHandoff, inspect_plan_package
from .invariants import InvariantViolationError
from .io import read_json, read_runtime_handoff, write_json, write_json_exclusive
from ._time import iso_now

_RECEIPT_ID_RE = re.compile(r"^(exec_\d{3}|verify_\d{3}|final)$")
_PLAN_ID_RE = re.compile(r"^[a-zA-Z0-9_]+$")
_HISTORY_MONTH_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


class ProtocolStore:
    """Read and write P8 protocol assets under a `.sopify/` root.

    Constructor takes the `.sopify/` root directory. State files,
    plan receipts, and history receipts are all derived from this root.
    """

    def __init__(self, sopify_root: Path) -> None:
        self.root = sopify_root
        self.state_dir = self.root / "state"
        self.active_plan_path = self.state_dir / "active_plan.json"
        self.current_handoff_path = self.state_dir / "current_handoff.json"

    def _receipt_path(self, plan_id: str, receipt_id: str) -> Path:
        return self.root / "plan" / plan_id / "receipts" / f"{receipt_id}.json"

    def _history_receipt_path(self, plan_id: str, month: str) -> Path:
        return self.root / "history" / month / plan_id / "receipt.md"

    @staticmethod
    def _validated_plan_id(plan_id: str) -> str:
        if not isinstance(plan_id, str) or not _PLAN_ID_RE.fullmatch(plan_id):
            raise InvariantViolationError(
                "plan_id must contain only letters, numbers, and underscores"
            )
        return plan_id

    def _ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # -- Active plan (state/active_plan.json) --

    def get_active_plan(self) -> Optional[dict]:
        """Read active_plan.json if it exists."""
        return read_json(self.active_plan_path)

    def set_active_plan(self, *, plan_id: str) -> None:
        """Write active_plan.json with a minimal plan_id pointer."""
        plan_id = self._validated_plan_id(plan_id)
        self._ensure_state_dir()
        write_json(self.active_plan_path, {"plan_id": plan_id})

    def clear_active_plan(self) -> None:
        """Remove active_plan.json if it exists."""
        self.active_plan_path.unlink(missing_ok=True)

    # -- Current handoff (state/current_handoff.json) --

    def get_current_handoff(self) -> Optional[RuntimeHandoff]:
        """Read current_handoff.json if it exists."""
        return read_runtime_handoff(self.current_handoff_path)

    def set_current_handoff(self, handoff: RuntimeHandoff) -> None:
        """Write current_handoff.json with observability metadata injection."""
        self._validated_plan_id(handoff.plan_id)
        self._ensure_state_dir()
        payload = handoff.to_dict()
        observability = dict(payload.get("observability") or {})
        observability.update(
            {
                "state_kind": "current_handoff",
                "writer": "sopify_writer",
                "written_at": iso_now(),
            }
        )
        payload["observability"] = observability
        write_json(self.current_handoff_path, payload)

    def clear_current_handoff(self) -> None:
        """Remove current_handoff.json if it exists."""
        self.current_handoff_path.unlink(missing_ok=True)

    # -- Plan receipts (plan/<plan_id>/receipts/<receipt_id>.json) --

    def write_plan_receipt(
        self,
        *,
        plan_id: str,
        receipt_id: str,
        verdict: str,
        evidence: Optional[Mapping[str, Any]] = None,
        provenance: Optional[Mapping[str, Any]] = None,
        expected_plan_version: Optional[str] = None,
    ) -> Path:
        """Write a plan receipt to plan/<plan_id>/receipts/<receipt_id>.json.

        Validates:
          - receipt_id matches ^(exec_\\d{3}|verify_\\d{3}|final)$
          - the plan package is structurally valid
          - expected/provenance plan versions match the current package
          - provenance.plan_id matches the plan_id argument if present
          - provenance.receipt_id matches the receipt_id argument if present
          - verdict is non-empty
          - the target receipt does not already exist

        Returns the path of the written receipt file.
        """
        plan_id = self._validated_plan_id(plan_id)
        if not _RECEIPT_ID_RE.match(receipt_id):
            raise InvariantViolationError(
                f"receipt_id {receipt_id!r} does not match "
                f"pattern ^(exec_\\d{{3}}|verify_\\d{{3}}|final)$"
            )
        if not verdict or not verdict.strip():
            raise InvariantViolationError("verdict must be non-empty")

        plan_dir = self.root / "plan" / plan_id
        snapshot = inspect_plan_package(plan_dir)
        if not snapshot.valid or snapshot.version is None:
            raise InvariantViolationError(
                f"invalid plan package {plan_id!r}: {snapshot.error or 'unknown error'}"
            )
        if (
            expected_plan_version is not None
            and expected_plan_version != snapshot.version
        ):
            raise InvariantViolationError(
                f"expected_plan_version {expected_plan_version!r} does not match "
                f"current plan_version {snapshot.version!r}"
            )

        prov: dict[str, Any] = dict(provenance) if provenance else {}
        if "plan_id" in prov and prov["plan_id"] != plan_id:
            raise InvariantViolationError(
                f"provenance.plan_id {prov['plan_id']!r} conflicts "
                f"with plan_id {plan_id!r}"
            )
        if "receipt_id" in prov and prov["receipt_id"] != receipt_id:
            raise InvariantViolationError(
                f"provenance.receipt_id {prov['receipt_id']!r} conflicts "
                f"with receipt_id {receipt_id!r}"
            )
        if "plan_version" in prov and prov["plan_version"] != snapshot.version:
            raise InvariantViolationError(
                f"provenance.plan_version {prov['plan_version']!r} conflicts "
                f"with current plan_version {snapshot.version!r}"
            )
        prov["plan_id"] = plan_id
        prov["receipt_id"] = receipt_id
        prov["plan_version"] = snapshot.version

        payload = {
            "verdict": verdict,
            "evidence": dict(evidence) if evidence else {},
            "provenance": prov,
            "timestamp": iso_now(),
        }

        receipt_path = plan_dir / "receipts" / f"{receipt_id}.json"
        write_json_exclusive(receipt_path, payload)
        return receipt_path

    # -- History receipts (history/<YYYY-MM>/<plan_id>/receipt.md) --

    def write_history_receipt(
        self,
        *,
        plan_id: str,
        outcome: str,
        summary: str,
        key_decisions: Sequence[str],
        month: Optional[str] = None,
        plan_version: Optional[str] = None,
    ) -> Path:
        """Write a history receipt Markdown to history/<month>/<plan_id>/receipt.md.

        Validates:
          - outcome, summary are non-empty
          - key_decisions has at least one non-empty item
          - month defaults to current UTC YYYY-MM if not provided

        Returns the path of the written receipt file.
        """
        month = self._validated_history_month(
            plan_id=plan_id,
            outcome=outcome,
            summary=summary,
            key_decisions=key_decisions,
            month=month,
        )
        content = self._render_history_receipt(
            plan_id=plan_id,
            outcome=outcome,
            summary=summary,
            key_decisions=key_decisions,
            plan_version=plan_version,
        )

        receipt_path = self._history_receipt_path(plan_id, month)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(content, encoding="utf-8")
        return receipt_path

    @staticmethod
    def _validated_history_month(
        *,
        plan_id: str,
        outcome: str,
        summary: str,
        key_decisions: Sequence[str],
        month: Optional[str],
    ) -> str:
        ProtocolStore._validated_plan_id(plan_id)
        if not outcome or not outcome.strip():
            raise InvariantViolationError("outcome must be non-empty")
        if not summary or not summary.strip():
            raise InvariantViolationError("summary must be non-empty")
        if not key_decisions or not all(d.strip() for d in key_decisions):
            raise InvariantViolationError(
                "key_decisions must have at least one non-empty item"
            )
        resolved_month = (
            datetime.now(timezone.utc).strftime("%Y-%m") if month is None else month
        )
        if not isinstance(resolved_month, str) or not _HISTORY_MONTH_RE.fullmatch(
            resolved_month
        ):
            raise InvariantViolationError("month must match YYYY-MM")
        return resolved_month

    @staticmethod
    def _render_history_receipt(
        *,
        plan_id: str,
        outcome: str,
        summary: str,
        key_decisions: Sequence[str],
        plan_version: Optional[str],
    ) -> str:
        decisions_text = "\n".join(f"- {decision}" for decision in key_decisions)
        version_line = f"plan_version: {plan_version}\n" if plan_version else ""
        return (
            f"---\n"
            f"plan_id: {plan_id}\n"
            f"outcome: {outcome}\n"
            f"{version_line}"
            f"---\n\n"
            f"# {outcome}\n\n"
            f"## Summary\n\n"
            f"{summary}\n\n"
            f"## Key Decisions\n\n"
            f"{decisions_text}\n"
        )

    # -- Finalize (write final receipt + history receipt + clear state) --

    def finalize_plan(
        self,
        *,
        plan_id: str,
        outcome: str,
        summary: str,
        key_decisions: Sequence[str],
        evidence: Optional[Mapping[str, Any]] = None,
        provenance: Optional[Mapping[str, Any]] = None,
        month: Optional[str] = None,
        expected_plan_version: Optional[str] = None,
    ) -> dict[str, Path]:
        """Finalize and archive one valid plan, then clear its runtime state."""
        resolved_month = self._validated_history_month(
            plan_id=plan_id,
            outcome=outcome,
            summary=summary,
            key_decisions=key_decisions,
            month=month,
        )
        source_dir = self.root / "plan" / plan_id
        snapshot = inspect_plan_package(source_dir)
        if not snapshot.valid or snapshot.version is None:
            raise InvariantViolationError(
                f"invalid plan package {plan_id!r}: {snapshot.error or 'unknown error'}"
            )
        if (
            expected_plan_version is not None
            and expected_plan_version != snapshot.version
        ):
            raise InvariantViolationError(
                f"expected_plan_version {expected_plan_version!r} does not match "
                f"current plan_version {snapshot.version!r}"
            )

        active_plan = self.get_active_plan()
        if active_plan is not None and active_plan.get("plan_id") != plan_id:
            raise InvariantViolationError(
                f"active plan {active_plan.get('plan_id')!r} conflicts with "
                f"finalize plan {plan_id!r}"
            )
        handoff = self.get_current_handoff()
        if handoff is not None and handoff.plan_id != plan_id:
            raise InvariantViolationError(
                f"handoff plan {handoff.plan_id!r} conflicts with finalize plan {plan_id!r}"
            )

        archive_dir = self.root / "history" / resolved_month / plan_id
        if archive_dir.exists():
            raise FileExistsError(f"history plan already exists: {archive_dir}")
        history_source = source_dir / "receipt.md"
        if history_source.exists():
            raise FileExistsError(
                f"history receipt already exists in plan: {history_source}"
            )

        final_source = self._receipt_path(plan_id, "final")
        created_final = False
        created_history = False
        try:
            self.write_plan_receipt(
                plan_id=plan_id,
                receipt_id="final",
                verdict="finalized",
                evidence=evidence,
                provenance=provenance,
                expected_plan_version=snapshot.version,
            )
            created_final = True
            history_content = self._render_history_receipt(
                plan_id=plan_id,
                outcome=outcome,
                summary=summary,
                key_decisions=key_decisions,
                plan_version=snapshot.version,
            )
            history_source.write_text(
                history_content, encoding="utf-8", errors="strict"
            )
            created_history = True
            final_snapshot = inspect_plan_package(source_dir)
            if not final_snapshot.valid or final_snapshot.version != snapshot.version:
                raise InvariantViolationError(
                    "plan package changed while finalize evidence was being written"
                )
            archive_dir.parent.mkdir(parents=True, exist_ok=True)
            source_dir.rename(archive_dir)
        except Exception:
            # Generated finalize evidence is safe to remove; semantic plan files remain intact.
            if created_history:
                history_source.unlink(missing_ok=True)
            if created_final:
                final_source.unlink(missing_ok=True)
            raise

        final_receipt_path = archive_dir / "receipts" / "final.json"
        history_receipt_path = archive_dir / "receipt.md"
        # Runtime pointers are cleared only after the full directory is archived.
        self.clear_active_plan()
        self.clear_current_handoff()

        return {
            "final_receipt": final_receipt_path,
            "history_receipt": history_receipt_path,
            "archive_dir": archive_dir,
        }
