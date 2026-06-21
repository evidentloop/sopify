---
title: Codex W1a S5 Same-Host Recovery Session A
plan_id: w1a_codex_s5_host_docstrings
status: draft
level: light
created: 2026-06-13
owner: codex
---

# Codex W1a S5 Same-Host Recovery Session A

## Context / Why

This isolated workspace exists only to leave a valid same-host recovery anchor for Codex W1a S5.

## Scope

- Create one compliant light plan in an isolated workspace.
- Leave state and receipt anchors for a future Codex Session B.
- Do not execute source edits.

## Approach

1. Create the plan and state files in an isolated workspace.
2. Run protocol `new-plan` validation before stopping.
3. Preserve the anchor artifacts without declaring any verdict.

## Waves / Steps

Wave 1: create `active_plan.json` and compliant `plan.md`.
Wave 2: add optional handoff and Session A receipt.
Wave 3: validate the workspace and stop before continuation.

## Key Decisions

- Use a host-specific `plan_id` so later audits can distinguish Codex from Qoder.
- Stop after anchor creation; do not simulate Session B in the same conversation.

## Constraints / Not-in-scope

- No source code changes are performed in this workspace.
- No finalize flow is attempted.
- No S5 verdict is declared during Session A.

## Status / Progress

- [x] `state/active_plan.json` created.
- [x] compliant light `plan.md` created.
- [x] optional `current_handoff.json` created.
- [x] Session A receipt anchor created.
- [ ] Session B continuation intentionally deferred to a future Codex session.

## Next

- Run `sopify_protocol_check.py check --scenario new-plan` against this workspace.
- Copy Session A artifacts back to the P9 asset directory.
- Wait for a future Codex session to continue the same `plan_id`.
