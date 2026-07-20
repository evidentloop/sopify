# Analyze Rules

## Goal

Turn the request and accessible evidence into a stable objective, deliverable, and boundary for host routing or Design. Analyze decides what must be solved; it does not choose the implementation.

## 1. Read evidence first

1. Read the current request, material and links the user supplied, and confirmed long-term preferences.
2. As the task requires, read relevant evidence supplied by the user or available in the current environment, such as documents, API material, designs, code, tests, previous plans, and governing protocols. These examples are not an exhaustive source list. Do not ask for an answer already present in accessible evidence.
3. Separate the desired outcome, the deliverable for this task, and any suggested implementation path. A suggested path becomes a boundary only when the user states it as one.
4. When sources conflict, state the conflict, its effect on this delivery, and a recommendation. Do not block on differences that cannot change the result.

The `kb` skill owns knowledge-base loading and materialization. Analyze consumes only the context relevant to the current objective.

## 2. Assess completeness

The score totals 10 points: goal clarity 0–3, expected outcome 0–3, scope boundary 0–2, and constraints 0–2.

- `score >= require_score`: continue and prepare the handoff.
- Below the threshold with `auto_decide=true`: make only explicit assumptions that are low-risk, reversible, and do not change the objective.
- Below the threshold with `auto_decide=false`: stop and ask.

Ask only when the answer can change the objective, deliverable, scope, success criteria, or whether the current path is safe to execute. Explain the impact of each question. Let the evidence determine the number of questions.

## 3. Prepare the handoff

Analyze returns:

- A one-sentence objective and the current deliverable.
- Confirmed success criteria, scope, and constraints.
- The key material or code evidence behind the conclusion.
- Unknowns that can still change the result; omit this section when there are none.
- The reason to continue as a consult, quick fix, or Design task.

If the suggested path clearly adds cost or risk, Analyze may identify a safer direction and its tradeoff. Design still owns the technical choice.

## 4. Routing signal

- Clear, simple work, usually no more than 2 files: quick fix may be enough.
- Local work that needs a plan, usually 3–5 files: light plan.
- More than 5 files, a new feature, cross-module work, or architecture change: standard or architecture Design.

File count is a signal, not an override for safety, protocol, or actual complexity.

Workflow transition:

- In `strict` mode, render the Analyze summary and wait for confirmation before Design.
- In `adaptive` mode, return the routing signal to the host, which follows the current request and protocol state.

## Boundaries

- Do not generate a plan package or modify code.
- Do not add host intent types, keyword rules, or regex routing.
- The host handles `consult_readonly` through the existing protocol; Analyze does not turn a read-only request into a write path.
