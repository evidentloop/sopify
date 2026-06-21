---
title: Codex W1a S4 Standard Plan Evidence
plan_id: w1a_codex_s4_standard
status: draft
level: standard
created: 2026-06-13
owner: codex
---

# Codex W1a S4 Standard Plan Evidence

## Context / Why

This isolated workspace exists only to prove that Codex can create a compliant standard plan and preserve both `plan.md` and `tasks.md` for W1a S4.

## Scope

- Audit Python imports across Sopify modules.
- Normalize relative imports to package-root absolute imports where appropriate.
- Preserve behavior while improving import consistency.

## Approach

1. Inventory every Python module with relative imports.
2. Group refactors by package boundary to avoid partial breakage.
3. Validate each group with targeted tests before broad rollout.

## Waves / Steps

Wave 1: collect import inventory and risk notes.
Wave 2: refactor low-risk modules first.
Wave 3: refactor remaining modules and run regression coverage.

## Key Decisions

- Treat this as a standard plan because execution would span many files and require task tracking.
- Keep the evidence workspace write-only for plan artifacts; no source edit is performed here.

## Constraints / Not-in-scope

- `tasks.md` must exist alongside `plan.md` to satisfy the standard-plan artifact boundary.
- This workspace proves planning artifacts only, not code execution.

## Status / Progress

- [x] `active_plan.json` written for the standard plan pointer.
- [x] compliant `plan.md` created with all required sections.
- [x] companion `tasks.md` created and preserved.
- [ ] implementation intentionally not started in this evidence workspace.

## Next

- Run `sopify_protocol_check.py check --scenario new-plan` against this workspace.
- Confirm `tasks.md` exists explicitly because protocol_check does not validate it.
