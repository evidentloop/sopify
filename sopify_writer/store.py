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

Boundary: ProtocolStore writes files into existing directories. It does not
move, delete, or archive plan directories. Archive lifecycle is outside
scope (deferred to W3/W3.6 blueprint sync).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from sopify_contracts import RuntimeHandoff
from .invariants import InvariantViolationError
from .io import read_json, read_runtime_handoff, write_json
from ._time import iso_now

_RECEIPT_ID_RE = re.compile(r"^(exec_\d{3}|verify_\d{3}|final)$")


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

    def _ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # -- Active plan (state/active_plan.json) --

    def get_active_plan(self) -> Optional[dict]:
        """Read active_plan.json if it exists."""
        return read_json(self.active_plan_path)

    def set_active_plan(self, *, plan_id: str) -> None:
        """Write active_plan.json with a minimal plan_id pointer."""
        if not plan_id or not plan_id.strip():
            raise InvariantViolationError("plan_id must be non-empty")
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
        self._ensure_state_dir()
        payload = handoff.to_dict()
        observability = dict(payload.get("observability") or {})
        observability.update({
            "state_kind": "current_handoff",
            "writer": "sopify_writer",
            "written_at": iso_now(),
        })
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
    ) -> Path:
        """Write a plan receipt to plan/<plan_id>/receipts/<receipt_id>.json.

        Validates:
          - receipt_id matches ^(exec_\\d{3}|verify_\\d{3}|final)$
          - provenance.plan_id matches the plan_id argument if present
          - provenance.receipt_id matches the receipt_id argument if present
          - verdict is non-empty

        Returns the path of the written receipt file.
        """
        if not plan_id or not plan_id.strip():
            raise InvariantViolationError("plan_id must be non-empty")
        if not _RECEIPT_ID_RE.match(receipt_id):
            raise InvariantViolationError(
                f"receipt_id {receipt_id!r} does not match "
                f"pattern ^(exec_\\d{{3}}|verify_\\d{{3}}|final)$"
            )
        if not verdict or not verdict.strip():
            raise InvariantViolationError("verdict must be non-empty")

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
        prov["plan_id"] = plan_id
        prov["receipt_id"] = receipt_id

        payload = {
            "verdict": verdict,
            "evidence": dict(evidence) if evidence else {},
            "provenance": prov,
            "timestamp": iso_now(),
        }

        receipt_path = self._receipt_path(plan_id, receipt_id)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(receipt_path, payload)
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
    ) -> Path:
        """Write a history receipt Markdown to history/<month>/<plan_id>/receipt.md.

        Validates:
          - outcome, summary are non-empty
          - key_decisions has at least one non-empty item
          - month defaults to current UTC YYYY-MM if not provided

        Returns the path of the written receipt file.
        """
        if not plan_id or not plan_id.strip():
            raise InvariantViolationError("plan_id must be non-empty")
        if not outcome or not outcome.strip():
            raise InvariantViolationError("outcome must be non-empty")
        if not summary or not summary.strip():
            raise InvariantViolationError("summary must be non-empty")
        if not key_decisions or not all(d.strip() for d in key_decisions):
            raise InvariantViolationError("key_decisions must have at least one non-empty item")

        if month is None:
            month = datetime.now(timezone.utc).strftime("%Y-%m")
        if not month.strip():
            raise InvariantViolationError("month must be non-empty")

        decisions_text = "\n".join(f"- {d}" for d in key_decisions)
        content = (
            f"---\n"
            f"plan_id: {plan_id}\n"
            f"outcome: {outcome}\n"
            f"---\n\n"
            f"# {outcome}\n\n"
            f"## Summary\n\n"
            f"{summary}\n\n"
            f"## Key Decisions\n\n"
            f"{decisions_text}\n"
        )

        receipt_path = self._history_receipt_path(plan_id, month)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(content, encoding="utf-8")
        return receipt_path

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
    ) -> dict[str, Path]:
        """Finalize a plan: write final receipt, history receipt, clear state.

        Performs three operations in order:
          1. Write plan/<plan_id>/receipts/final.json
          2. Write history/<month>/<plan_id>/receipt.md
          3. Clear active_plan.json and current_handoff.json

        Does not move or delete the plan directory.

        Returns a dict with keys 'final_receipt' and 'history_receipt'
        pointing to the written file paths.
        """
        final_receipt_path = self.write_plan_receipt(
            plan_id=plan_id,
            receipt_id="final",
            verdict="finalized",
            evidence=evidence,
            provenance=provenance,
        )
        history_receipt_path = self.write_history_receipt(
            plan_id=plan_id,
            outcome=outcome,
            summary=summary,
            key_decisions=key_decisions,
            month=month,
        )

        # Clear state after both receipts are written successfully.
        self.clear_active_plan()
        self.clear_current_handoff()

        return {
            "final_receipt": final_receipt_path,
            "history_receipt": history_receipt_path,
        }
