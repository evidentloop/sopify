---
name: templates
description: Knowledge-base document templates, loaded when long-lived knowledge files are created or materialized.
---

# Knowledge Base Templates

The Templates skill defines stable knowledge-base document structures. It does not decide when to write, how to apply `knowledge_sync`, or how a plan moves through its lifecycle.

- For knowledge-base policy and `knowledge_sync`, read the `kb` skill.
- For `light / standard / architecture` levels and plan-body templates, read Design `assets/`.
- For active-plan, handoff, and receipt reads and writes, follow the governing Protocol.

Replace placeholders and remove empty optional sections. Do not store one-off implementation detail as long-lived knowledge.

## `project.md`

```markdown
# Project Conventions

## Technology
- Core: {language or framework version}
- Build: {build tool}
- Test: {test framework}

## Conventions
- {reusable technical convention}

## Document boundaries
- `project.md`: technical conventions
- `blueprint/background.md`: long-term goals, scope, and non-goals
- `blueprint/design.md`: module, host, directory, and consumption contracts
- `blueprint/tasks.md`: unfinished long-term work and explicit deferrals
```

## `blueprint/README.md`

```markdown
# Project Blueprint Index

Status: {current status}
Maintenance: keep only status, current goal, current focus, and reading links

## Current goal
- {long-term goal summary}

## Current focus
- Active plan: {none / link to plan.md}
- Archive status: {status}

## Read next
- [Project conventions](../project.md)
- [Background](./background.md)
- [Design](./design.md)
- [Tasks](./tasks.md)
- [History](../history/index.md)
```

List each long-lived topic document in “Read next” when the `blueprint/` root contains one.

## `blueprint/background.md`

```markdown
# Blueprint Background

## Long-term goals
- {goal}

## Scope
- In scope: {content}
- Out of scope: {content}

## Non-goals
- {content}
```

## `blueprint/design.md`

```markdown
# Blueprint Design

## Governing contracts
- {contract that remains valid across plans}

## Module and consumption boundaries
- {module, host, or directory responsibility}
```

## `blueprint/tasks.md`

```markdown
# Blueprint Tasks

## Unfinished long-term work
- [ ] {item}

## Explicit deferrals
- [-] {item and revisit condition}
```

Keep only unfinished long-term work and explicit deferrals. Remove `[x]` items.

## `history/index.md`

```markdown
# Change History Index

| Date | Feature | Status | Plan package |
|------|---------|--------|--------------|
| {YYYY-MM-DD} | {feature} | {status} | [link](YYYY-MM/...) |
```

## `user/preferences.md`

```markdown
# Long-term User Preferences

- {explicit preference that applies across tasks}
```

## `user/feedback.jsonl`

```json
{"timestamp":"{ISO-8601}","source":"chat","message":"{raw feedback}","scope":"{scope}","promote_to_preference":false}
```
