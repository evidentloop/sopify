---
name: kb
description: Manage long-lived `.sopify/` knowledge, including bootstrap, progressive materialization, reads, retention, and knowledge_sync policy.
---

# Knowledge Base Management

KB owns long-lived knowledge. It does not make Analyze, Design, or Develop decisions, and it does not manage the active plan, handoff, receipts, or finalize directly. Document structures come from Templates; protocol state is managed through `sopify_writer`.

## Directory responsibilities

```text
.sopify/
├── project.md              # reusable technical conventions
├── user/                   # long-term preferences and raw feedback
├── blueprint/              # long-term goals, design boundaries, open work, and index
├── plan/                   # current plan semantic files
├── history/                # archived plans and index
└── state/                  # local protocol state
```

`blueprint/README.md` keeps only status, maintenance guidance, current goal, current focus, and reading links. Put detailed content in the relevant blueprint file.

## Bootstrap and progressive materialization

`kb_init: full` creates `project.md`, `user/preferences.md`, `user/feedback.jsonl`, and the four blueprint files on first use. It does not pre-create plan content, history, or empty directories.

`kb_init: progressive` is the default:

- First real project use: create `project.md`, `user/preferences.md`, and `blueprint/README.md`.
- First plan lifecycle: add `blueprint/background.md`, `blueprint/design.md`, `blueprint/tasks.md`, and the current plan directory.
- First explicit `~go finalize`: let the protocol flow create `history/index.md` and the archive directory.
- First explicit long-term feedback: create `user/feedback.jsonl` when needed.

## Knowledge context reads

The host completes the governing Protocol entry for a managed plan, handoff, and receipts before invoking KB. This section defines only KB's long-lived context order:

1. `project.md`
2. `user/preferences.md`
3. `blueprint/README.md`
4. Relevant parts of `blueprint/background.md`, `design.md`, and `tasks.md`

Consult and quick fix do not fail when deep blueprint files are absent. Read `history/` only for trace-back or finalize.

## Retention and updates

Keep information only when it remains useful across tasks:

- `project.md`: reusable technical conventions.
- `background.md`: long-term goals, scope, and non-goals.
- `design.md`: module, host, directory, and consumption contracts.
- `tasks.md`: unfinished long-term work and explicit deferrals with a revisit condition.
- `preferences.md`: explicit long-term user preferences.

Do not store one-off implementation details, current-plan task breakdowns, temporary tradeoffs, completed tasks, or copies of history content. When code and documentation conflict, verify the code and then correct the documentation. Current user instructions override historical preferences.

## `knowledge_sync`

```yaml
knowledge_sync:
  project: skip|review|required
  background: skip|review|required
  design: skip|review|required
  tasks: skip|review|required
```

- `skip`: do not inspect that file for this plan.
- `review`: decide whether it needs an update before finalize.
- `required`: update it before the delivery candidate; block finalize while incomplete.

KB applies the plan's sync policy without changing the plan lifecycle. Update the narrowest long-lived location and avoid duplicating the same content across files.

## Output

After bootstrap or sync, state the actual result, list `Changes`, and end with `Next:`. Use `Changes: 0 files` when nothing changed.
