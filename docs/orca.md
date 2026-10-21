# Using Sopify with Orca

Orca dispatches and supervises agents. Sopify keeps the plan, decisions and
verification evidence in the repository. This is an optional way to execute an
existing plan; it adds no Skill, command, scheduler or state file.

## One owner, bounded workers

- **Owner ("brain"):** selects authorized work, supplies context, reviews the real
  diff and owns plan progress, knowledge sync and all protocol writes.
- **Executor:** changes only the assigned files and reports verification and
  limitations. It leaves `.sopify/` unchanged unless explicitly assigned a
  semantic document; it never takes ownership of state, handoff or receipts.
- **Reviewer:** independently checks scope, code quality and the acceptance
  evidence. Findings go back to the owner, not directly into a receipt.

These are roles, not fixed models or host products. Give overlapping files to
one executor at a time; independent work can run in parallel. Preserve other
workers' changes. A dispatch does not grant commit, push or publication authority.

## Before dispatch

Read the existing Sopify entry chain: `state/active_plan.json` →
`plan/<id>/plan.md` → `state/current_handoff.json` → `plan/<id>/receipts/`,
all under `.sopify/`. Verify the plan's level and current `plan_version`.
Check that the handoff names the same plan and that its checkpoint and next action
still agree with the plan and latest receipts. Reuse evidence only for the code
and scope it actually verified.

A mismatched subject, superseded checkpoint or changed recorded version means
the handoff is stale. The owner rereads the current files and corrects the
handoff through `sopify_writer` before dispatch. A different session ID alone is
not a conflict. Inspect the branch, commit and existing dirty files as well.

Use the same brief as a bounded implementation task or a one-file documentation
task. Supply the goal, checkout, allowed changes, checks and return instructions;
reference existing context rather than inventing another manifest. Resolve
`plan_id` and `plan_version` from the referenced plan, not from a new user form.

```text
Task: <task ID, goal and deliverable>
Repository / baseline: <path, branch, commit; existing changes to preserve>
Plan: <plan path and task section; include the plan_id / plan_version already read>
Allowed / protected: <write set, protected behavior, home and Git boundaries>
Check: <acceptance criteria and actual verification commands, where applicable>
References: <relevant prior work; evidence reusable for this baseline and what must be rechecked>
Report: <output path and required results>
Return: <the injected Orca reporting commands with this task's exact identifiers>
```

Use the installed Orca orchestration instructions (`orca skills get orchestration`)
to dispatch and wait. Workers use their injected Run/Task/Dispatch identifiers
and reporting commands; do not copy identifiers from another run.
If `worker-start` does not support the host label (as with Trae in the current
setup), use manual dispatch and include the actual return commands in the brief.

## Review and write back

1. The executor reports actual changed files, commands, results and untested
   boundaries, tied to a code revision (include the diff when uncommitted).
2. `worker_done` means the worker returned; **it is not a verify pass**. The
   reviewer examines the diff and evidence and separates `spec_compliance`
   from `code_quality`. Return bounded defects for correction without silently
   widening the task.
3. Before accepting or writing, the owner rereads the plan version and matching
   handoff. If they changed unexpectedly, reconcile the work first.
4. Only the owner uses the existing `sopify_writer` API to write receipts and
   update protocol state. Keep Orca run/task/dispatch IDs, code SHA, command,
   result, evidence location and reviewer in the existing `evidence` mapping.
   The writer binds the receipt to the plan version; code SHA is separate.

For a defect, use this compact finding; ordinary task results need no finding:

```text
Location:
Reproduce:
Expected / actual:
Test ID:
Code SHA (and uncommitted diff, if any):
Evidence level: executed test / observed session / static inspection / unverified
Evidence link and reviewer:
```

Retain failures and limits in the evidence. A local test does not prove a host
loaded a rule, and a completed review does not authorize a release.
