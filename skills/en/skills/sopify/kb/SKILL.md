---
name: kb
description: Knowledge base management skill; read during KB operations; includes init, update, sync strategies
---

# Knowledge Base Management - V2 Rules

**Goal:** manage the V2 layers in `.sopify/` so long-lived knowledge, the active plan, and finalized archives stay clearly separated.

## Knowledge Base Structure

```text
.sopify/
├── blueprint/
│   ├── README.md           # Pure index page with index-required sections only
│   ├── background.md       # Long-term goals, scope, non-goals
│   ├── design.md           # Module / host / directory / consumption contracts
│   └── tasks.md            # Unfinished long-term items and explicit deferrals
├── project.md              # Project technical conventions
├── user/
│   ├── preferences.md      # Long-term user preferences
│   └── feedback.jsonl      # Raw feedback events
├── plan/
│   └── YYYYMMDD_feature/   # Current active plan
├── history/
│   ├── index.md            # Archive index
│   └── YYYY-MM/
└── state/                  # Runtime machine truth
```

## Initialization Strategy

### Full mode (`kb_init: full`)

Create on the first bootstrap:

```yaml
Create:
  - .sopify/project.md
  - .sopify/user/preferences.md
  - .sopify/user/feedback.jsonl
  - .sopify/blueprint/README.md
  - .sopify/blueprint/background.md
  - .sopify/blueprint/design.md
  - .sopify/blueprint/tasks.md
```

Notes:

- Do not pre-create `plan/` content.
- Do not pre-create `history/index.md` or any archive.

### Progressive mode (`kb_init: progressive`) [default]

Materialize by lifecycle:

```yaml
First real-project trigger:
  - .sopify/project.md
  - .sopify/user/preferences.md
  - .sopify/blueprint/README.md

First plan lifecycle:
  - .sopify/blueprint/background.md
  - .sopify/blueprint/design.md
  - .sopify/blueprint/tasks.md
  - .sopify/plan/YYYYMMDD_feature/

First explicit ~go finalize:
  - .sopify/history/index.md
  - .sopify/history/YYYY-MM/YYYYMMDD_feature/

First explicit long-term preference:
  - .sopify/user/feedback.jsonl
```

## Read Order

1. `project.md`
2. `user/preferences.md`
3. `blueprint/README.md`
4. `blueprint/background.md`
5. `blueprint/design.md`
6. `blueprint/tasks.md`
7. `state/active_plan.json` → `plan/<plan_id>/plan.md`

Rules:

- consult / clarification routes prefer `L0/L1` and must not require deep blueprint files
- planning / develop may enter `L2 active plan`
- `active_plan.json` provides only `plan_id`; `plan.md` is the active plan's semantic entry. Read handoff and receipts only when continuation needs them, and never fall back to the retired current-plan projection.
- `history/` is not the default long-lived context source; read it only for finalize lookups or human traceability

## Update Rules

### L0 Index Guardrails

- `blueprint/README.md` keeps only `status / maintenance / current goal / current focus / read next`.
- Do not write absolute workspace paths, long-form architecture prose, or formal contract bodies into `blueprint/README.md`.
- If extra long-lived topic docs exist at the `blueprint/` root, `blueprint/README.md` must list them explicitly.

### `blueprint/tasks.md` Boundaries

- Keep only unfinished long-term items and explicit deferrals.
- `[x]` completed items must not remain in `blueprint/tasks.md`.

### Must update

- `project.md`: reusable technical conventions changed
- `blueprint/background.md`: long-term goals, scope, or non-goals changed
- `blueprint/design.md`: module, host, directory, or consumption contracts changed
- `blueprint/tasks.md`: unfinished long-term items or explicit deferrals changed
- `user/preferences.md`: the user explicitly stated a long-term preference

### Must not be written into long-lived knowledge

- one-off implementation details
- short-term task breakdown from the current plan
- temporary tradeoffs that belong only to this task
- completed task checklists lingering in `blueprint/tasks.md`
- copying history body text back into blueprint

## `knowledge_sync` Sync Contract

```yaml
knowledge_sync:
  project: skip|review|required
  background: skip|review|required
  design: skip|review|required
  tasks: skip|review|required
```

Execution rules:

- `skip`: no sync required for this round
- `review`: at least review before finalize
- `required`: finalize must block until updated

## Conflict Handling

- code vs docs: code is the source of truth, then update docs
- current task vs long-term preference: current explicit task > `user/preferences.md` > default rules

## Output Format

**Initialization complete:**

```text
[{BRAND_NAME}] Knowledge Base Init ✓

Created: {N} files
Strategy: {full/progressive}

---
Changes: {N} files
  - .sopify/project.md
  - .sopify/blueprint/README.md
  - ...

Next: KB is ready
```

**Sync complete:**

```text
[{BRAND_NAME}] Knowledge Base Sync ✓

Updated: {N} files

---
Changes: {N} files
  - .sopify/project.md
  - .sopify/blueprint/design.md
  - ...

Next: Docs updated
```
