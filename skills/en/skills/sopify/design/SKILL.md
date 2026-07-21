---
name: design
description: Design phase entry. Aggregates plan-level selection, task breakdown, and package output rules; loads references/assets/scripts on demand.
---

# Design (Entry)

> Check the current system first, then choose the smallest sufficient path.

## When to activate

- Entering the design phase (`workflow` / `plan_only` / `light_iterate`).
- Need to convert requirements into a plan package and task list.

## Execution skeleton

1. Load `references/design-rules.md`.
2. Check existing implementation, governing contracts, applicable platform capabilities, and installed dependencies.
3. Choose the smallest sufficient path and select `light/standard/architecture`.
4. Generate the plan files from the matching `assets/` templates.
5. Produce tasks with explicit dependencies and verification.
6. Report `Ready` or `Needs decision` with evidence using `assets/output-summary.md`.

## Resource navigation

- Long rules: `references/design-rules.md`
- Shared writing standards: `../references/shared-writing-dna.md` (apply to all output)
- Output contract: `../references/output-contract.md` (required sections, conditional enhancement, self-check)
- Templates: `assets/*.md`
- Deterministic level selector: `scripts/select_plan_level.py`

## Deterministic logic first

Use the selector when `plan.level=auto` must be auditable:

```bash
python3 skills/en/skills/sopify/design/scripts/select_plan_level.py \
  --file-count 6 \
  --new-feature \
  --cross-module
```

The script returns JSON with the suggested level and explicit reasons.

## Boundaries

- This skill does not execute code changes directly; hand off to `develop`.
- This skill does not handle routing or protocol state writes; it defines the plan structure and task contract only.
