# Pilot Round 1 Aggregation

## Scope

- Round: `pilot_round_1`
- Coverage target: `45` samples across `3` environment classes
- Current threshold role: `round-1 pilot target`, not final promotion threshold

## Aggregated Metrics

| Metric | Value | Notes |
| --- | ---: | --- |
| `expected_trigger_count` | `30` | `A1/A2/A3/A4` |
| `expected_no_trigger_count` | `15` | `C1/C2` |
| `intervention_count` | `30` | all expected trigger samples received first-principles intervention |
| `helpful_count` | `29` | only `FH5-14` remained `neutral` |
| `over_trigger_count` | `0` | no expected `no_trigger` sample was stretched |
| `under_trigger_count` | `0` | no expected `trigger` sample fell back to direct handling |
| `helpfulness_rate` | `96.7%` | `29 / 30` |
| `false_positive_rate` | `0%` | `0 / 15` |
| `false_negative_rate` | `0%` | `0 / 30` |
| `median_extra_turns` | `0` | only `4` intervention samples required `1` extra clarifying turn |
| `quick_fix_regression` | `no` | all `15` control samples remained lightweight |

## Threshold Comparison

- `helpfulness >= 80%`: `met` (`96.7%`)
- `false_positive <= 10%`: `met` (`0%`)
- `false_negative <= 20%`: `met` (`0%`)
- `median_extra_turns <= 1`: `met` (`0`)
- `quick_fix regression = no`: `met` (`no`)

## Calibration Outcome

The metrics-only pass is complete, and the later standalone decision pass is now closed.

- Final decision status: `propose-promotion`
- Decision role: terminal result of this plan's standalone `hold / review / propose-promotion` pass
- Decision interpretation: the current four-rule `analyze` subset is approved for promotion based on the completed round-1 evidence
- Constraint kept: `Batch 2/3` caution remains post-decision wording/example optimization; it does not reopen the `v1` layering decision or block this promotion result

## What Changed From Batch 1

- Business calibration:
  - `freyr-h5pages` proved the trigger boundary can stay useful in a business repo when existing flows, gateways, configs, and offline aliases are already present.
  - `A2/A3` were especially strong in business context because they exposed lower-cost paths instead of letting product requests drift into fresh-page or fresh-abstraction assumptions.
  - `A1` remained valid, but worked best as one factual clarifier first rather than a broad challenge.
  - `A4` stayed useful, but business-side wording needs caution when the repo does not already use the proposed abstraction language, as seen in `FH5-14`.
- sdk/tool calibration:
  - `rs-sdk` showed that `A4` becomes more consistently helpful when package, build, and documentation boundaries are already explicit in the codebase.
  - `A3` stayed valuable by rejecting weak “reuse for reuse's sake” proposals such as forcing CLI prompt work into the current `@rs-sdk/shared`.
  - `A1` still benefits from one narrowing question when the ask is experience-oriented rather than contract-oriented.
- control-sample calibration:
  - The combined `15` control samples across `sopify-skills`, `freyr-h5pages`, and `rs-sdk` now provide a materially stronger quick-fix and direct-consult confidence signal than Batch 1 alone.
  - No control sample regressed into a heavier challenge path.

## Recommended Next Step

1. Treat `propose-promotion` as the closed decision for this plan, rather than reopening a second approval loop inside the same archive.
2. Convert the Batch 2/3 calibration notes into wording/example updates for the first-principles trigger rules, especially around `A1` business clarifiers and `A4` abstraction overreach.
3. If future wording or threshold changes are material, run them as the next versioned optimization round instead of retroactively editing this round's decision basis.
