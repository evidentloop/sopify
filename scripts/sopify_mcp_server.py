#!/usr/bin/env python3
"""MCP tool plane for Sopify protocol state.

S1 exposes deterministic read/check operations. S2A adds one guarded low-level
write tool for plan receipts. Workflow decisions, required host actions,
installer setup, and higher-level finalization stay with the host prompt, CLI,
and sopify_writer.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sopify_protocol_check import run_protocol_check  # noqa: E402
from sopify_writer import ProtocolStore  # noqa: E402

MCP_DEPENDENCY = "mcp[cli]>=1.27,<2"
_PLAN_ID_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def resolve_workspace_root(workspace_root: str | Path) -> Path:
    """Resolve and validate the caller-provided workspace root."""
    candidate = Path(workspace_root).expanduser().resolve()
    if not candidate.exists():
        raise ValueError(f"workspace_root does not exist: {candidate}")
    if not candidate.is_dir():
        raise ValueError(f"workspace_root is not a directory: {candidate}")
    return candidate


def sopify_root_for(workspace_root: str | Path) -> Path:
    return resolve_workspace_root(workspace_root) / ".sopify"


def read_active_plan(workspace_root: str | Path) -> dict[str, Any] | None:
    """Return state/active_plan.json through ProtocolStore, or null."""
    return ProtocolStore(sopify_root_for(workspace_root)).get_active_plan()


def read_current_handoff(workspace_root: str | Path) -> dict[str, Any] | None:
    """Return state/current_handoff.json through ProtocolStore, or null."""
    handoff = ProtocolStore(sopify_root_for(workspace_root)).get_current_handoff()
    return handoff.to_dict() if handoff is not None else None


def _validated_plan_id(active_plan: Any) -> str:
    """Return a schema-compatible plan_id or reject invalid state."""
    if not isinstance(active_plan, dict):
        raise ValueError("active plan must be an object")
    plan_id = active_plan.get("plan_id")
    if not isinstance(plan_id, str) or not _PLAN_ID_RE.fullmatch(plan_id):
        raise ValueError("active plan plan_id is missing or invalid")
    return plan_id


def workspace_status_lite(workspace_root: str | Path) -> dict[str, Any]:
    """Return a minimal, dependency-light Sopify workspace status."""
    workspace = resolve_workspace_root(workspace_root)
    sopify_root = workspace / ".sopify"
    state_root = sopify_root / "state"
    active_plan_path = state_root / "active_plan.json"
    active_plan_file_exists = active_plan_path.is_file()
    active_plan = read_active_plan(workspace) if active_plan_file_exists else None
    active_plan_id = _validated_plan_id(active_plan) if active_plan_file_exists else None
    active_plan_dir = (
        _safe_child_path(sopify_root / "plan", active_plan_id)
        if active_plan_id is not None
        else None
    )
    handoff = read_current_handoff(workspace) if sopify_root.exists() else None
    raw_handoff_plan_id = handoff.get("plan_id") if isinstance(handoff, dict) else None
    handoff_plan_id = (
        raw_handoff_plan_id
        if isinstance(raw_handoff_plan_id, str) and raw_handoff_plan_id
        else None
    )
    handoff_matches_active_plan = (
        handoff_plan_id == active_plan_id
        if handoff_plan_id and active_plan_id
        else None
    )

    return {
        "workspace_root": str(workspace),
        "sopify_exists": sopify_root.is_dir(),
        "paths": {
            "blueprint": (sopify_root / "blueprint").is_dir(),
            "plan": (sopify_root / "plan").is_dir(),
            "history": (sopify_root / "history").is_dir(),
            "state": state_root.is_dir(),
        },
        "active_plan": active_plan,
        "active_plan_file_exists": active_plan_file_exists,
        "active_plan_dir_exists": active_plan_dir.is_dir() if active_plan_dir else None,
        "active_plan_md_exists": (
            (active_plan_dir / "plan.md").is_file() if active_plan_dir else None
        ),
        "handoff_exists": (state_root / "current_handoff.json").is_file(),
        "handoff_plan_id": handoff_plan_id,
        "handoff_matches_active_plan": handoff_matches_active_plan,
    }


def protocol_check(workspace_root: str | Path, scenario: str) -> dict[str, Any]:
    return run_protocol_check(workspace_root, scenario)


def _safe_child_path(root: Path, *parts: str) -> Path:
    """Build a child path and reject polluted ids that escape the expected root."""
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes expected root: {candidate}") from exc
    return candidate


def _active_plan_id(store: ProtocolStore) -> str:
    return _validated_plan_id(store.get_active_plan())


def _guard_write_plan_receipt(
    *,
    sopify_root: Path,
    store: ProtocolStore,
    plan_id: str,
    receipt_id: str,
) -> Path:
    """Enforce S2A write guards before delegating the actual write to ProtocolStore."""
    active_plan_id = _active_plan_id(store)
    if plan_id != active_plan_id:
        raise ValueError(f"plan_id must match active plan: {active_plan_id}")

    plan_dir = _safe_child_path(sopify_root / "plan", plan_id)
    if not (plan_dir / "plan.md").is_file():
        raise ValueError(f"active plan plan.md not found: {plan_dir / 'plan.md'}")

    receipt_path = _safe_child_path(plan_dir / "receipts", f"{receipt_id}.json")
    if receipt_path.exists():
        raise FileExistsError(f"plan receipt already exists: {receipt_path}")
    return receipt_path


def write_plan_receipt(
    workspace_root: str | Path,
    plan_id: str,
    receipt_id: str,
    verdict: str,
    evidence: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Write a receipt for the current active plan after S2A MCP guards pass."""
    workspace = resolve_workspace_root(workspace_root)
    sopify_root = workspace / ".sopify"
    store = ProtocolStore(sopify_root)
    _guard_write_plan_receipt(
        sopify_root=sopify_root,
        store=store,
        plan_id=plan_id,
        receipt_id=receipt_id,
    )
    receipt_path = store.write_plan_receipt(
        plan_id=plan_id,
        receipt_id=receipt_id,
        verdict=verdict,
        evidence=evidence,
        provenance=provenance,
    )
    return {"path": str(receipt_path)}


def _tool_error(exc: Exception) -> dict[str, str]:
    return {
        "code": type(exc).__name__,
        "message": str(exc),
    }


def _safe_tool(key: str, fn: Callable[..., Any], *args: Any) -> dict[str, Any]:
    try:
        return {key: fn(*args), "error": None}
    except Exception as exc:
        return {key: None, "error": _tool_error(exc)}


def get_mcp_dependency_hint() -> str:
    return f'Install the stable MCP Python SDK with: python3 -m pip install "{MCP_DEPENDENCY}"'


def create_mcp_server() -> Any:
    """Create the FastMCP server lazily so tests can run without the SDK."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:
        raise RuntimeError(get_mcp_dependency_hint()) from exc

    server = FastMCP("sopify", json_response=True)

    @server.tool(name="sopify.get_active_plan")
    def tool_get_active_plan(workspace_root: str) -> dict[str, Any]:
        """Read Sopify state/active_plan.json for a workspace."""
        return _safe_tool("active_plan", read_active_plan, workspace_root)

    @server.tool(name="sopify.get_current_handoff")
    def tool_get_current_handoff(workspace_root: str) -> dict[str, Any]:
        """Read Sopify state/current_handoff.json for a workspace."""
        return _safe_tool("current_handoff", read_current_handoff, workspace_root)

    @server.tool(name="sopify.workspace_status_lite")
    def tool_workspace_status_lite(workspace_root: str) -> dict[str, Any]:
        """Inspect only the lightweight .sopify/ workspace structure."""
        return _safe_tool("status", workspace_status_lite, workspace_root)

    @server.tool(name="sopify.protocol_check")
    def tool_protocol_check(workspace_root: str, scenario: str) -> dict[str, Any]:
        """Run the Sopify protocol checker for new-plan, continuation, or finalize."""
        return _safe_tool("protocol_check", protocol_check, workspace_root, scenario)

    @server.tool(name="sopify.write_plan_receipt")
    def tool_write_plan_receipt(
        workspace_root: str,
        plan_id: str,
        receipt_id: str,
        verdict: str,
        evidence: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Write a plan receipt only after the host has authorized the protocol write."""
        return _safe_tool(
            "write_plan_receipt",
            write_plan_receipt,
            workspace_root,
            plan_id,
            receipt_id,
            verdict,
            evidence,
            provenance,
        )

    return server


def main() -> int:
    try:
        create_mcp_server().run(transport="stdio")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
