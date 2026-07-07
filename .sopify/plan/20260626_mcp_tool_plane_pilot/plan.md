---
title: MCP Tool Plane Pilot
plan_id: 20260626_mcp_tool_plane_pilot
status: active
level: standard
created: 2026-06-26
updated: 2026-07-07
knowledge_sync:
  project: skip
  background: review
  design: review
  tasks: review
archive_ready: false
---

# MCP Tool Plane Pilot

## Plan Snapshot

- **Goal**: Add a narrow MCP tool plane for deterministic Sopify protocol reads/checks and one guarded low-level plan receipt write, without replacing prompt workflow, CLI, installer, or host adapters.
- **Status**: Active. S1 read/check pilot and S2A `write_plan_receipt` are complete for Codex/Qoder observation; S2A go/no-go is `go`.
- **Next**: Enter S3.1 as a Codex-only design step: produce the Codex MCP config matrix and registration boundary, then stop for review before implementation.
- **Task**: Continue from `tasks.md` item 3.1; do not implement installer registration or enter finalize yet.

## Context / Why

Sopify is now Protocol-first and Convention-driven. Hosts read prompt/workflow rules, while deterministic protocol writes and receipts are handled by `sopify_writer` and local scripts. That keeps the system portable, but AI hosts still tend to invoke shell commands or hand-build file writes for protocol checks, state reads, and receipt writes.

This plan tests whether a small MCP tool plane can reduce protocol misuse without expanding Sopify back into a runtime. The pilot is intentionally narrow: it exposes deterministic local capabilities as tools, while workflow judgment, checkpoint behavior, and user-facing decisions remain in host prompt and skill logic.

This is a new plan because MCP sits at the boundary between CLI, prompt, hook, and protocol writer behavior. It needs its own pilot and go/no-go gates instead of being folded into a broad host-adapter rewrite.

## Scope

The current scope is:

- Add `scripts/sopify_mcp_server.py` as a single-file stdio MCP server.
- Expose S1 read/check tools: `sopify.get_active_plan`, `sopify.get_current_handoff`, `sopify.workspace_status_lite`, and `sopify.protocol_check`.
- Add S2A `sopify.write_plan_receipt` only, guarded by active plan, matching plan id, existing `plan.md`, and no receipt overwrite.
- Keep CLI, protocol checker, and `ProtocolStore` as the source of deterministic behavior.
- Record manual observation signals in `tasks.md`.

Out of scope for this plan stage:

- Installer-driven MCP registration.
- Host capability declaration changes.
- `write_history_receipt`, `finalize_plan`, `set_active_plan`, or `set_current_handoff` MCP tools.
- Rewriting analyze/design/develop workflow prompts as tools.

## Approach

Keep MCP as an AI tool plane, not as a workflow engine.

The server stays in one file for the pilot and is structured into workspace resolution, pure business functions, and MCP binding. Read/check behavior delegates to existing `ProtocolStore` and `scripts.sopify_protocol_check.run_protocol_check`. The write tool delegates to `ProtocolStore.write_plan_receipt` after MCP-layer guards pass.

S2A is intentionally smaller than the original S2 idea. It only exposes `write_plan_receipt` because finalize and history receipts need a clearer host-level decision boundary before they become safe tool operations.

## Waves / Steps

1. **S1 Build + Test**: Implement and validate read/check tools; observe Codex and Qoder behavior.
2. **S2A Write Plan Receipt**: Implement one guarded receipt-writing tool and verify it through tests, stdio smoke, and manual host observation.
3. **S3 Multi-host Registration**: Only after S2A proves useful and safe, design installer-assisted MCP config registration across supported hosts.

Current execution is between S2A and S3. S1 is complete for Codex and Qoder. S2A implementation, unit tests, stdio smoke, and Qoder manual observation are complete. S3.1 is the next step and is limited to Codex registration design.

## Key Decisions

- MCP tools must expose deterministic capabilities only; reasoning-heavy workflow stays in prompt/skill layers.
- S1 stays single-file and avoids a new `sopify_mcp/` package until the pilot proves value.
- S2A exposes only `write_plan_receipt`, not finalization or history receipt tools.
- `write_plan_receipt` must call `ProtocolStore.write_plan_receipt`; it must not hand-write JSON or Markdown.
- Missing `state/active_plan.json`, mismatched plan id, missing active `plan.md`, or an existing receipt must fail closed with a structured error envelope.
- S3 multi-host registration must start with a host-specific design step. Current next scope is Codex-only S3.1; other hosts remain matrix inputs, not implementation targets.

## Constraints / Not-in-scope

- Do not modify four host adapters in S1/S2A.
- Do not change installer behavior before S3.
- Do not add high-level workflow tools such as `approve_and_finalize` or `continue_and_finalize`.
- Do not write or clear `.sopify/state/active_plan.json` from the MCP tool.
- Do not treat Claude/Copilot compatibility observation as blocking S2A; record it as S3 input.
- Do not enter finalize until receipt evidence and knowledge sync decisions are explicit.

## Status / Progress

Completed:

- S1 read/check tool implementation and tests.
- Codex and Qoder main observations for read/check behavior.
- S2A scope reduction and guard design.
- S2A `write_plan_receipt` implementation.
- S2A unit coverage for success, missing active plan, non-active plan, duplicate receipt, missing `plan.md`, and invalid workspace error envelope.
- S2A MCP stdio smoke for `write_plan_receipt`.
- Qoder manual validation that the write tool does not encourage bypassing `required_host_action`, user instructions, or finalize intent branching.

Pending:

- Claude/Copilot compatibility observation as S3 input.
- S3.1 Codex MCP config matrix and registration boundary.
- S3 implementation, installer/doctor updates, and multi-host registration.

## Next

Start S3.1 with Codex only:

- Map current Codex MCP config location and expected JSON/TOML shape.
- Decide non-destructive registration behavior: opt-in, merge, backup, dry-run, and existing-server conflict handling.
- Decide the dependency boundary for launching `scripts/sopify_mcp_server.py` from Codex.
- Record the design in `design.md` / `tasks.md` and stop before code changes.
