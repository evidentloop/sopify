# Batch 1 Stop-Check: sopify-skills

## Scope

- Batch: `batch_1`
- Repo: `sopify-skills`
- Samples: `SOP-01` to `SOP-15`
- Role: `plan-core pilot`
- Decision target: whether Batch 2 and Batch 3 can continue
- Run mode: post-fix rerun after router/engine/test updates

## Interim Metrics

| Metric | Value | Notes |
| --- | ---: | --- |
| `expected_trigger_count` | `9` | `A1/A2/A3/A4` in Batch 1 |
| `expected_no_trigger_count` | `6` | `C1/C2` in Batch 1 |
| `intervention_count` | `9` | all `A*` samples now land in `consult_challenge_trigger` |
| `helpful_count` | `9` | all trigger samples now preserve the intended first-principles challenge route |
| `over_trigger_count` | `0` | no `C1/C2` sample was stretched into planning / checkpoint flow |
| `under_trigger_count` | `0` | no `A1/A2/A3/A4` sample fell back to plain direct consult |
| `helpfulness_rate` | `100%` | `9 / 9` |
| `false_positive_rate` | `0%` | `0 / 6` |
| `false_negative_rate` | `0%` | `0 / 9` |
| `median_extra_turns` | `0` | `consult_challenge_trigger` stays zero-turn in phase 1 |
| `quick_fix_regression` | `no` | `SOP-10`, `SOP-11`, `SOP-14` are back to `quick_fix` |

## Result

`pass`

Batch 1 now meets the current pilot target (`>=80% / <=10% / <=20% / <=1`). Batch 2 (`freyr-h5pages`) and Batch 3 (`rs-sdk`) may continue.

## Why It Passed

1. Active-plan execution-confirm interception is no longer stealing unrelated requests.
   `C1` and `C2` samples no longer collapse into `execution_confirm_pending`.
2. `A1/A2/A3/A4` question-form challenges are now preserved as `consult + analyze challenge`.
   The route stays lightweight, but the trigger intent is no longer lost.
3. Quick-fix control regression is gone.
   README/comment/typo style requests now stay in `quick_fix`.

## Residual Risk

- This round validates routing correctness, not consult answer-body quality.
  `consult` still writes handoff only; full consult body generation remains phase 2 scope.
- The new active-plan binding checkpoint only targets non-anchored complex planning requests.
  Future batches should still watch for medium-complexity edge cases in business repos.

## Next Action

1. Resume Batch 2 and Batch 3 using the same review template and rubric.
2. Keep the rerun evidence from this batch as the new baseline for future regressions.
3. If later batches regress, compare against this rerun before changing the pilot target threshold.
