# Design Rules

## Goal

Turn the objective and boundaries confirmed by Analyze into the smallest executable, verifiable solution. Design owns technical tradeoffs and task breakdown. It does not manage protocol state or implement code.

## 1. Check the current system

Before proposing new implementation, inspect the existing code, callers, and tests; governing protocol, public contracts, and compatibility boundaries; applicable language or platform capabilities; and dependencies already installed and used by the project.

This is not a fixed technology ladder. The goal is to avoid duplicate capability and unnecessary dependencies without weakening correctness, safety, or user value.

## 2. Choose the smallest sufficient solution

- State the recommended path, its material tradeoffs, and explicit non-goals.
- Prefer the narrowest shared boundary; explain why a cross-module change is necessary when it is.
- Do not build frameworks, state, or extension points for hypothetical future work.
- Ask the user only about choices that can change scope, the solution path, or acceptance. Develop may decide reversible implementation details within the approved boundary.

## 3. Select the plan level

- `light`: `plan.md` for clear local work.
- `standard`: `plan.md + tasks.md` for a feature, cross-module work, or substantial delivery.
- `architecture`: `plan.md + tasks.md + design.md` only for an actual architecture change, new system, or major refactor.

Create ADRs, diagrams, assets, and receipts only when evidence requires them. Plan-body templates come only from this skill's `assets/` directory.

## 4. Determine readiness

- `Ready`: no unresolved user choice can still change scope, the solution path, or acceptance. State the supporting evidence.
- `Needs decision`: list the concrete options, their impact, and a recommendation, then stop.

A dynamic version, Git delivery, release, or another irreversible action is an execution checkpoint. It does not make a settled plan `Needs decision` by itself.

Workflow transition:

- In `strict` mode, render the Design summary and wait for confirmation before Develop.
- In `adaptive` mode, `~go` may continue through the host workflow; `~go plan` stops after the summary.

## 5. Break down tasks

Each task needs a clear deliverable, dependency, and acceptance method. Follow real boundaries instead of splitting work to fit an arbitrary duration. Include documentation and knowledge sync only when the plan's `knowledge_sync` requires them.

Task markers: `[ ]` pending, `[x]` completed, `[-]` skipped, `[!]` blocked.

## Protocol boundary

Design creates or updates plan semantic files only. The host writes `active_plan`, handoff, and receipts through `sopify_writer` under the governing protocol.
