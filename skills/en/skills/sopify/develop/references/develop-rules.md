# Develop Rules

Implement, verify and review approved tasks before updating progress and `knowledge_sync`. Work is not complete without verification evidence.

## 1. Select and execute

Read pending `[ ]` items from the current plan's `tasks.md` (`plan.md` for light plans), then follow dependencies and task order. Locate files, understand the implementation, make the change, discover and run verification, handle failure and review. Update markers only after the quality contract below is satisfied.

- For a bug or shared-boundary change, inspect affected callers, fix the narrowest common root cause, and verify equivalent paths.
- Decide reversible implementation details inside approved boundaries; replan only when new facts change scope, the solution path or acceptance.
- A Quick Fix without a Design artifact needs only local choices for the current request; do not create a plan or copy the Design process.
- Claims such as `overbuild`, `underbuild` or "it should be fine" are not evidence. Never silently skip verification or retry indefinitely. Preserve compatibility, security and repository conventions.

### Bug investigation branch

For a bug, first capture a minimal reproduction and failure evidence on the same surface (UI, CLI or API). Inspect callers and observations to locate the common root cause, fix it, then rerun the same reproduction and affected equivalent paths. If it cannot be reproduced, record the environment, missing inputs or reason; do not claim a fix. A cheap, clear local regression may start with a failing test, but TDD is not required for every task, and unit tests do not replace verification on the original surface.

## 2. Verification record

Discover verification in this order: declared project contract (such as `verify` in `.sopify/project.md`) → native project commands → not configured. Use the project contract when present; do not create a configuration system for this task.

| Field | Constraint |
|---|---|
| `verification_source` | `project_contract` / `project_native` / `not_configured`; source only |
| `command` | Actual command; may be empty only when no stable command exists and the reason is recorded |
| `scope` | Tasks, files or modules covered |
| `result` | `passed` / `retried` / `failed` / `skipped` / `replan_required` |
| `reason_code` | Required for unavailable verification, downgrade, skip or return to plan review |
| `retry_count` | Only `0` or `1` |
| `root_cause` | Required for failure close-out or retry; values below |
| `review_result` | Separate `spec_compliance` and `code_quality` conclusions |

Keep these names, without aliases. Source is not result; missing verification cannot become a pass. `reason_code` stays internal; explain it in plain language to the user.

## 3. Failure handling

After the first failure, one automatic retry with failure context is allowed; stop automatic retries after a second failure. Record a root cause after that failure or when abandoning retry. Follow these boundaries without blind fixes or weakened acceptance.

| `root_cause` | Action |
|---|---|
| `logic_regression` | Fix with the failure evidence, then verify |
| `environment_or_dependency` | State that the environment cannot establish a pass |
| `missing_test_infra` | Keep the task unverified and name the missing checks |
| `scope_or_design_mismatch` | Return to plan review, a decision checkpoint or host confirmation |
| `human_action_required` | Mark `[!]`; describe the credential, migration or approval step a person must perform |

## 4. Review and task state

- `spec_compliance`: check the objective, scope and acceptance; identify excess work, omissions or a choice needing the user.
- `code_quality`: check existing style, compatibility, security, stability, maintainability, required tests and knowledge sync.

Mark `[x]` only when verification and both reviews satisfy the contract; use `[-]` for skipped, `[!]` for blocked, and keep pending work `[ ]`. Use `✓` only when every verification row has `result=passed` and `reason_code=—`; otherwise use `!`.

Follow the shared output contract and this Skill's output templates: success includes both review conclusions and verification; partial results also name incomplete work and reasons. Small fixes need only relevant verification, not forced tables. Check that status, evidence, Changes and Next agree.

## 5. Knowledge sync and completion

Call KB at close-out according to the plan's `knowledge_sync`; KB alone defines reading, retention and preference policy.
When tasks, verification and required sync are complete, set `plan.md` metadata to `lifecycle_state: ready_to_archive` and `archive_ready: true`, keeping the package in `.sopify/plan/`.
`ready_to_archive` is not automatic archiving. Only explicit `~go finalize` uses `sopify_writer` to validate the latest `plan_version`, move the package to history and update the index. Develop does not move it or simulate finalize.

On interruption, preserve completed markers, leave the current item `[ ]`, and hand off actual completed work, remaining work and evidence. On failure, mark `[!]`, retain root cause and review results, and continue only independent tasks. Use Git rollback only when explicitly requested; preserve traceability and keep the plan in `plan/`.
