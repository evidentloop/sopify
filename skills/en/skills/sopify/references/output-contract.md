# Sopify Output Contract

The final response should make the result, evidence, and next step easy to find. Phase templates define required information, not empty sections that must always be rendered.

## Output path

- A gate summary reports routing, current state, and the next action only.
- After a skill or consult finishes, the host renders the final response from the actual outcome. Gate text is not a delivery report.

## Required content

| Output | Required content | Status rule |
|--------|------------------|-------------|
| `analyze/success` | Objective, deliverable, completeness score, confirmed evidence, explicit assumptions when used, material gaps, next step | Do not mark incomplete input as complete |
| `analyze/question` | A few decision-relevant questions, their impact, `Next` | `?` |
| `design/summary` | Approach, task count, `Ready` or `Needs decision` with evidence, `Changes`, `Next` | Do not use `Ready` while a material choice remains |
| `develop/success` | Result, review conclusion, verification summary, `Changes`, `Next` | Use `✓` only when all checks pass |
| `develop/partial` | Incomplete work, reason, completed verification, `Changes`, `Next` | `!` |
| `develop/quick-fix` | Result, relevant verification, `Changes`, `Next` | Use `✓` only when all checks pass |
| `consult` | Conclusion, necessary evidence, `Changes`, `Next` | Match the actual state |

`consult_readonly` writes no code, plan, state, knowledge base, audit, receipt, or Git index. Give the conclusion and necessary evidence first; include blockers or decisions only when they exist, then stop.

## Structure and density

- Use short paragraphs for a simple answer or one-file change. Do not add a table merely to fill a template.
- Use a comparison table for several options, numbered steps for a process, or a tree for a directory relationship. Choose at most one main structure per response.
- Group repeated results by deliverable instead of listing the same “passed” line for every task.
- Put `Changes` before the final `Next:` line. Use `Changes: 0 files` when nothing changed.

## Before sending

1. Does the opening answer the current question?
2. Does the status symbol match the verification result?
3. Does `Ready / Needs decision` follow the Design rule?
4. Have empty sections, repeated conclusions, and internal fields been removed?
5. Are paths, commands, numbers, and references verifiable?
6. Are `Changes` and the final `Next:` line present?
