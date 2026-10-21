# Sopify

<div align="center">

**Version AI coding plans and evidence in Git — resume work across tools, teammates, and agents.**

Installs into the AI coding tools you already use. Questions and small fixes are handled directly; plans start only when needed.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](./LICENSE) [![Version](https://img.shields.io/badge/version-2026--10--21.151943-orange.svg?style=for-the-badge)](#version-history)

[![Codex](https://img.shields.io/badge/Codex-4A9EFF.svg?style=for-the-badge)](#supported-hosts) [![Claude Code](https://img.shields.io/badge/Claude%20Code-CC785C.svg?style=for-the-badge)](#supported-hosts) [![Qoder](https://img.shields.io/badge/Qoder-7C3AED.svg?style=for-the-badge)](#supported-hosts) [![Copilot](https://img.shields.io/badge/Copilot-000000.svg?style=for-the-badge)](#supported-hosts) [![Cursor](https://img.shields.io/badge/Cursor-111827.svg?style=for-the-badge)](#supported-hosts) [![Antigravity](https://img.shields.io/badge/Antigravity-1A73E8.svg?style=for-the-badge)](#supported-hosts) [![Trae](https://img.shields.io/badge/Trae-00B96B.svg?style=for-the-badge)](#supported-hosts)

English · [简体中文](./README.zh-CN.md) · [Quick Start](#quick-start) · [Contributors](./CONTRIBUTORS.md)

</div>

<div align="center">
<img src="./assets/sopify-cover.jpg" width="660" alt="Sopify — plans, decisions and verification evidence saved as ordinary files in your repo" />
</div>

---

Sopify is a set of rules and Skills that installs into the AI coding tool you already use. When work needs a plan, it saves the plan, the decisions and the verification evidence as ordinary files under `.sopify/`, versioned in Git, so the next session — another tool, another person, another agent — resumes from the record instead of from memory.

## Quick Start

**1. Install into your tool.**

```bash
curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/install.sh | bash -s -- --target codex:en-US
```

| Your tool | `--target` |
|---|---|
| Codex | `codex:en-US` / `codex:zh-CN` |
| Claude Code | `claude:en-US` / `claude:zh-CN` |
| Qoder | `qoder:en-US` / `qoder:zh-CN` |
| Copilot | `copilot:en-US` / `copilot:zh-CN` |
| Cursor | `cursor:en-US` / `cursor:zh-CN` |
| Antigravity | `antigravity:en-US` / `antigravity:zh-CN` |
| Trae | `trae:en-US` / `trae:zh-CN` |

Python 3.11 or newer; the installer checks before downloading. It writes host instructions and Skills only.

**2. In your project, type one line into the chat box.**

```text
~go plan add input validation to the signup form
```

Sopify asks about anything still unresolved and writes `.sopify/plan/YYYYMMDD_signup_form_validation/plan.md` only after you answer in the conversation. In a non-interactive session (such as `-p` / `--print`) the question ends that turn — send the request again with your answers included. This step changes no business code.

**3. Run the plan, then archive it.**

```text
~go            # run or resume the current plan
~go finalize   # once all tasks are complete, archive the plan to .sopify/history/
```

`~go` works through the plan one task at a time: implement, then verify and review, mark the task done once checks pass, and move to the next. It pauses when a fact is missing or a decision requires your input, and continues after you answer. After an interruption, a tool switch, or a handover, type `~go` again: it reads the plan and its evidence, then continues with the next unfinished task that can proceed. In a fresh clone, if the target plan is unclear, it asks which one to continue. A finished plan stays in `plan/` until you run `~go finalize`. See [How Sopify Works](./docs/how-sopify-works.en.md#task-loop-and-modes) for the read order and pause rules.

### What lands in your repo

| Path | What it is | In Git? |
|---|---|---|
| `.sopify/sopify.json` | project marker | committed |
| `.sopify/plan/`, `.sopify/history/` | plans and verification evidence | committed |
| `.sopify/state/` | local pointers: active plan and resume hint | not committed; ignored by default through `.git/info/exclude` |

Windows uses the PowerShell installer instead of step 1:

```powershell
iwr https://github.com/evidentloop/sopify/releases/latest/download/install.ps1 -OutFile sopify-install.ps1
.\sopify-install.ps1 --target codex:en-US
```

## Where It Pays Off

**A long task gets interrupted.**
Before: the session ends and the reasoning ends with it. After: `~go` reads `.sopify/plan/` and resumes at the next unfinished task.

**Another tool or another person takes over.**
Before: paste the context again and hope nothing important was dropped. After: this release was built that way — a fresh Qoder session whose only input was `~go` resumed a plan written by Claude Code.

**Several agents split the work.**
Before: two agents edit the same files and overwrite each other. After: one owner holds the plan, workers take bounded tasks, and the evidence lands in one place. See [Using Sopify with Orca](./docs/orca.md).

<div align="center">
<img src="./assets/readme-visuals/sopify-scene-cross-host-en.jpg" width="720" alt="A plan written in Claude Code is resumed by a fresh Qoder session that reads .sopify/ after receiving only ~go" />
</div>

<div align="center">
<img src="./assets/readme-visuals/sopify-scene-decision-en.jpg" width="720" alt="Every decision traced — auditable and reviewable" />
</div>

## When Not to Use It

- Questions, code reading, and explanations
- Small fixes: a rename, a typo, a one-line style change
- Throwaway scripts and exploratory tries

These are handled directly and never enter the plan workflow. A plan starts only when you type `~go plan`, ask to continue work in progress, or when `~go` decides one is needed.

## Command Cheat Sheet

| Command | When to type it |
|---|---|
| `~go plan <request>` | New work that needs a plan — asks first when anything is unclear, writes `.sopify/plan/<id>/plan.md` only after you answer, and changes no code |
| `~go` | Run or resume the current plan; routine questions and small fixes are answered directly without resuming a plan |
| `~go finalize` | Close out the active plan and move it to `.sopify/history/` |

## Supported Hosts

| Host | Status | Install |
|---|---|---|
| Codex | Verified | `--target codex:en-US` / `codex:zh-CN` |
| Claude Code | Verified | `--target claude:en-US` / `claude:zh-CN` |
| Qoder | Verified | `--target qoder:en-US` / `qoder:zh-CN` |
| Copilot | Baseline | `--target copilot:en-US` / `copilot:zh-CN` |
| [Cursor](./docs/cursor-host.md) | Baseline | `--target cursor:en-US` / `cursor:zh-CN` |
| [Antigravity](./docs/antigravity-host.md) | Baseline; tested in real sessions | `--target antigravity:en-US` / `antigravity:zh-CN` |
| [Trae](./docs/trae-host.md) | Baseline | `--target trae:en-US` / `trae:zh-CN` |

Verified means the managed workflow has been run in a real session on that host, not only installed. Baseline means the installation is verified; real-session evidence varies by host — see each host's doc.

## A Real Case

This archived workflow ran inside Codex. A complex request became a tracked plan, an audit concern stopped the work for a user decision, and after the user approved a minimal fix the verification evidence was recorded and the plan was archived.

<p align="center">
  <img src="./assets/readme-visuals/codex-dogfood.gif" alt="Sopify in a real Codex workflow: a request becomes a plan, an audit concern stops for the user's decision, and the minimal fix and verification evidence are recorded before archive" width="900" />
</p>

- **Plan first** — Codex did not start coding immediately; it captured the goal, boundaries and verification steps in a tracked plan.
- **Stop for a decision** — the first audit found one concern; work paused for the user, then only a minimal identity check was added.
- **Close with evidence** — the second audit found no open risk; 5 protocol checks and 55 targeted tests with 48 subtests were recorded before archive.

The real task was an optional verifier integration. The animation shows how Sopify managed it; the archived files show what happened: [plan](./.sopify/history/2026-07/20260718_evidentloop_optional_audit_integration/plan.md) · [verification receipt](./.sopify/history/2026-07/20260718_evidentloop_optional_audit_integration/receipts/verify_001.json) · [final receipt](./.sopify/history/2026-07/20260718_evidentloop_optional_audit_integration/receipts/final.json).

## Further Reading

- [How Sopify Works](./docs/how-sopify-works.en.md) — workflow stages, checkpoints, the four files a new session reads first, the `.sopify/` layout, and the [product form](./assets/sopify-product-form-release-en.svg) and architecture diagrams
- [Getting Started](./docs/getting-started.md) — install details, inspecting the script before running it, host-specific setup, updating, removing, and the optional EvidentLoop companion
- [Using Sopify with Orca](./docs/orca.md) — owner, executor and reviewer roles for multi-agent work
- [Host Onboarding](./docs/host-onboarding.md) — how a new host adapter is probed and recorded
- [External Repo Quickstart](./examples/external-repo-quickstart/README.md) — step-by-step demo on a repo that is not Sopify's own
- [Configuration example](./examples/sopify.config.yaml) — optional `sopify.config.yaml` overrides; defaults work without it

## Version History

- See [CHANGELOG.md](./CHANGELOG.md) for the detailed history

## License

- Code and config: Apache 2.0, see [LICENSE](./LICENSE)
- Documentation: CC BY 4.0, see [LICENSE-docs](./LICENSE-docs)

## Contributing

For user-visible behavior changes, update both `README.md` and `README.zh-CN.md` when needed, then follow [CONTRIBUTING.md](./CONTRIBUTING.md) for validation.
