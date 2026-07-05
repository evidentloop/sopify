#!/usr/bin/env python3
"""Read-only MCP tool plane for Sopify protocol state.

S1 intentionally exposes only deterministic read/check operations. Workflow
decisions, checkpoint confirmation, installer setup, and all state writes stay
with the host prompt, CLI, and sopify_writer.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sopify_protocol_check import run_protocol_check  # noqa: E402
from sopify_writer import ProtocolStore  # noqa: E402

MCP_DEPENDENCY = "mcp[cli]>=1.27,<2"


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


def workspace_status_lite(workspace_root: str | Path) -> dict[str, Any]:
    """Return a minimal, dependency-light Sopify workspace status."""
    workspace = resolve_workspace_root(workspace_root)
    sopify_root = workspace / ".sopify"
    state_root = sopify_root / "state"
    active_plan = read_active_plan(workspace) if sopify_root.exists() else None
    active_plan_id = active_plan.get("plan_id") if isinstance(active_plan, dict) else None
    active_plan_dir = sopify_root / "plan" / str(active_plan_id) if active_plan_id else None

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
        "active_plan_dir_exists": active_plan_dir.is_dir() if active_plan_dir else None,
        "handoff_exists": (state_root / "current_handoff.json").is_file(),
    }


def protocol_check(workspace_root: str | Path, scenario: str) -> dict[str, Any]:
    return run_protocol_check(workspace_root, scenario)


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
