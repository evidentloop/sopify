"""Protocol state writer for Sopify P8 2-file model.

Manages only:
  - state/active_plan.json   (minimal plan_id pointer)
  - state/current_handoff.json (recovery + required_host_action)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sopify_contracts import RuntimeHandoff
from .io import read_json, read_runtime_handoff, write_json
from ._time import iso_now


class StateStore:
    """Read and write P8 protocol state files under `.sopify-skills/state/`."""

    def __init__(self, state_dir: Path) -> None:
        self.root = state_dir
        self.active_plan_path = self.root / "active_plan.json"
        self.current_handoff_path = self.root / "current_handoff.json"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def get_active_plan(self) -> Optional[dict]:
        return read_json(self.active_plan_path)

    def set_active_plan(self, *, plan_id: str) -> None:
        self.ensure()
        write_json(self.active_plan_path, {"plan_id": plan_id})

    def clear_active_plan(self) -> None:
        self.active_plan_path.unlink(missing_ok=True)

    def get_current_handoff(self) -> Optional[RuntimeHandoff]:
        return read_runtime_handoff(self.current_handoff_path)

    def set_current_handoff(self, handoff: RuntimeHandoff) -> None:
        self.ensure()
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
        self.current_handoff_path.unlink(missing_ok=True)
