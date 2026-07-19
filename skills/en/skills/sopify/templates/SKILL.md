---
name: templates
description: Document template collection; read when creating docs; includes all KB templates and plan file templates
---

# Document Template Collection

**Usage notes:**
1. Replace `{...}` with actual content.
2. Formal plan packages include the scoring block by default.
3. `blueprint/README.md` stays as a lightweight index only.
4. If extra long-lived topic docs exist at the `blueprint/` root, they must be linked explicitly from `blueprint/README.md`.
5. `blueprint/tasks.md` keeps only unfinished long-term items and explicit deferrals; completed items do not remain in that file.

## A1 | Knowledge Base Templates

### project.md

```markdown
# Project Technical Conventions

## Tech Stack
- Core: {language version} / {framework version}
- Build: {build tool}
- Test: {test framework}

## Working Agreement
- Keep this file focused on reusable technical conventions.
- Do not treat one-off implementation choices as project-wide rules.

## Document Boundaries
- `project.md`: reusable conventions
- `blueprint/background.md`: long-term goals, scope, non-goals
- `blueprint/design.md`: module / host / directory / consumption contracts
- `blueprint/tasks.md`: unfinished long-term items and explicit deferrals
```

### blueprint/README.md

```markdown
# Project Blueprint Index

Status: {current status}
Maintenance: keep only status, current goal, current focus, and read-next links on this page; move long explanations into other blueprint files

## Current Goal
- Project: `{project_name}`
- Long-term goals and scope live in `./background.md`

## Current Focus
- Active plan: {present/none}
- History archive: {status}

## Read Next
- [Technical Conventions](../project.md)
- [Blueprint Background](./background.md)
- [Blueprint Design](./design.md)
- [Blueprint Tasks](./tasks.md)
- [Blueprint Topic](./{extra_blueprint_doc}.md) # list each additional long-lived topic doc when present
- [Change History](../history/index.md)
```

### blueprint/background.md

```markdown
# Blueprint Background

## Long-Term Goals
- {goal1}
- {goal2}

## Scope
- In scope: {content}
- Out of scope: {content}

## Non-Goals
- {content}
```

### blueprint/design.md

```markdown
# Blueprint Design

## Formal Contracts
- `knowledge_sync` is the only formal sync contract.
- `state/active_plan.json` provides only `plan_id`; the active plan semantic entry is always `plan/<plan_id>/plan.md`.

## Consumption Contract

| Context Profile | Reads | Fail-open Rule | Notes |
|-----|------|------|------|
| `consult` | `project.md`, `preferences.md`, `blueprint/README.md` | missing deep blueprint does not fail | do not force plan materialization |
| `plan` | `L1` + `active_plan.json → plan.md` | materialize deep blueprint by lifecycle when missing | history is not default context |
| `finalize` | `active_plan.json → plan.md`, `knowledge_sync`, `blueprint/*`, `history/index.md` | create `history/index.md` on demand when missing | block when `required` sync is not satisfied |
```

### blueprint/tasks.md

```markdown
# Blueprint Tasks

Status: keep only unfinished long-term items and explicit deferrals; completed items do not remain in this file.

## Unfinished Long-Term Items
- [ ] {long-term item}

## Explicit Deferrals
- [-] {deferred item}
```

### history/index.md

```markdown
# Change History Index

| Timestamp | Feature | Status | Plan Package |
|-----------|---------|--------|--------------|
| {YYYYMMDD} | {feature} | ✓ | [Link](YYYY-MM/...) |
```

### user/preferences.md

```markdown
# Long-Term User Preferences

> Record only explicitly stated long-term preferences. One-off instructions stay out of this file.

No confirmed long-term preferences yet.
```

### user/feedback.jsonl

```json
{"timestamp":"2026-01-15T10:30:00Z","source":"chat","message":"Use the smallest change list by default going forward","scope":"planning","promote_to_preference":true,"preference_id":"pref-002"}
{"timestamp":"2026-01-15T11:10:00Z","source":"chat","message":"Make the output more detailed for this task","scope":"current_task","promote_to_preference":false}
```

## A2 | Plan Package Templates

Every level starts with a `plan.md` carrying `level` frontmatter. Standard adds `tasks.md`; architecture adds `design.md`. Create supporting ADRs, diagrams, and evidence only when needed, without empty directories.

### All Levels - plan.md

```markdown
---
title: {Feature Name}
plan_id: {YYYYMMDD_feature}
level: {light|standard|architecture}
---

# {Feature Name}

Scoring:
- Solution quality: {X}/10
- Implementation readiness: {Y}/10

## Context / Why
{Why this change is needed}

## Scope
{What this plan includes}

## Approach
{Smallest viable approach}

## Waves / Steps
- [ ] {Step 1}

## Key Decisions
- {Confirmed decision}

## Constraints / Not-in-scope
- {Explicit exclusion}

## Status / Progress
- [ ] {Current status}

## Next
{Next action or decision checkpoint}
```

### Standard / Architecture - tasks.md

```markdown
# Task List: {Feature Name}

Directory: `.sopify/plan/{YYYYMMDD}_{feature}/`

## 1. {Module Name}
- [ ] 1.1 Implement {feature} in `{file path}`
- [ ] 1.2 Implement {feature} in `{file path}`

## 2. Testing
- [ ] 2.1 {test task}

## 3. Documentation Update
- [ ] 3.1 Update `project.md / blueprint/background.md / blueprint/design.md / blueprint/tasks.md`
```

### Architecture - design.md

```markdown
# Technical Design: {Feature Name}

## Technical Solution
- {Implementation point}

## Architecture Boundaries
{Module relationships and responsibilities}

## Verification Strategy
- {Verification method}
```

## A3 | Task Markers

| Marker | Meaning |
|--------|---------|
| `[ ]` | Pending |
| `[x]` | Completed |
| `[-]` | Skipped |
| `[!]` | Blocked |
