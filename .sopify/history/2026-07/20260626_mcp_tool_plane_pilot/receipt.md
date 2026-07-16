---
plan_id: 20260626_mcp_tool_plane_pilot
outcome: completed
---

# completed

## Summary

Delivered the narrow MCP tool plane and Codex-first registration pilot. Two independent reviewers found four boundary gaps; each was fixed minimally, reverified, and documented without expanding the product scope.

## Key Decisions

- Keep MCP limited to deterministic protocol tools; workflow and user decisions remain in host prompt and skill layers.
- Treat Codex as the first validation target, not the only capable host.
- Delegate registration to the official host CLI; treat disabled or conflicting configuration as conflict and return structured startup errors.
- Require Python 3.11+ with mcp[cli]>=1.27,<2 and a usable FastMCP import.
- Use a stable archive-relative verification receipt reference.
- Keep dependency installation, doctor integration, locking, and multi-host abstraction out of this pilot.
