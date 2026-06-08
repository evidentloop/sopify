# Decision Pending Fixture

## Context / Why

Test fixture for validating decision-pending handoff under P8 protocol.

## Scope

Verify `required_host_action=confirm_decision` handoff carries decision state via artifacts.

## Approach

Use `current_handoff.json` with `artifacts.decision_options` to carry decision state.

## Waves / Steps

Single wave: create fixture and validate.

## Key Decisions

Decision options and submission state live in `artifacts`, not separate state files.

## Constraints / Not-in-scope

Not a real plan. Only for testing.

## Status / Progress

Awaiting host decision on architectural choice.

## Next

Host selects an option, then handoff transitions to `continue_host_develop`.
