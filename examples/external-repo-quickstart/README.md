# External Repo Quickstart

Use Sopify in an existing repository to keep a plan, decisions and verification evidence with the work.

## Install and check

Follow [Getting Started](../../docs/getting-started.md) for prerequisites, the current host target, installation and diagnostics. Use its real installer output; this example does not carry a frozen bundle version or a workspace-marker JSON to copy.

## Start a bounded task

Open the target repository in the installed host and ask, for example:

```text
~go plan Add an empty-state message to the results page.
Keep the current filtering behavior; include the acceptance check.
```

Review the proposed scope and acceptance before implementation. Ordinary questions and small fixes do not automatically resume a managed plan.

## Continue from repository evidence

For a new session or supported host, keep the tracked `.sopify/plan/`, `history/` and relevant blueprint files. Ask explicitly to continue the named plan. The host reads the plan as semantic truth and uses local state only as a resume hint, following the [protocol entry](../../docs/how-sopify-works.en.md#protocol-entry-4-step-read-chain).

If the local pointer is absent, select the intended plan rather than inventing state. Confirm what the recorded evidence actually verified, rerun checks for changed code, and record unresolved decisions. A fresh session consuming files is distinct from a successful end-to-end continuation; retain the commands or session evidence for the latter.

## Keep the evidence

When authorized work and verification finish, use explicit `~go finalize` to archive. Do not delete `.sopify/` to uninstall the prompt entry; follow [Removing Sopify](../../docs/getting-started.md#removing-sopify), which preserves plans, history and user instructions outside managed blocks.

For supervised multi-agent work, see the optional [Orca handoff guide](../../docs/orca.md). No additional runtime directory or marker example is required.
