# Batch 1 Observations: sopify-skills

## Setup

- Scope: `SOP-01` to `SOP-15`
- Role: `plan-core pilot`
- Runtime entry: repo-local `run_runtime(...)` with isolated workspaces
- Base workspace: copied from the current repo snapshot after the routing fix round
- Preserved state: `.sopify-skills/state/current_plan.json`
- Cleared before each sample: `current_run.json`, `current_handoff.json`, `current_clarification.json`, `current_decision.json`, `current_gate_receipt.json`, `last_route.json`
- Execution date: `2026-03-22`
- Batch note: this is the post-fix rerun used to verify whether Batch 1 still blocks Batch 2/3

## Route Summary

| sample_id | label | observed_route | required_host_action | run_stage | reviewer_note |
| --- | --- | --- | --- | --- | --- |
| `SOP-01` | `A4` | `consult` | `continue_host_consult` | - | Stayed in `consult`, but now carries `consult_mode=analyze_challenge` and `trigger_label=A4`. |
| `SOP-02` | `A4` | `consult` | `continue_host_consult` | - | Correctly identified as an `A4` machine-contract challenge instead of plain direct consult. |
| `SOP-03` | `A2` | `consult` | `continue_host_consult` | - | Correctly routed as `A2` challenge; no longer collapsed into active-plan execution confirm. |
| `SOP-04` | `A1` | `consult` | `continue_host_consult` | - | Ambiguous UX-improvement ask stayed lightweight and challenge-oriented. |
| `SOP-05` | `A3` | `consult` | `continue_host_consult` | - | Lower-cost alternative signal is now preserved as `A3` challenge. |
| `SOP-06` | `A4` | `consult` | `continue_host_consult` | - | Consult/runtime contract split is now surfaced as `A4` challenge instead of being swallowed by execution confirm. |
| `SOP-07` | `A4` | `consult` | `continue_host_consult` | - | Long-term reuse-strategy question is now tagged as `A4` challenge. |
| `SOP-08` | `A1` | `consult` | `continue_host_consult` | - | Vague responsibility-unification ask no longer jumps into planning or execution-confirm. |
| `SOP-09` | `A2` | `consult` | `continue_host_consult` | - | Path-first proposal is now challenged in `consult`, matching the agreed phase-1 scope. |
| `SOP-10` | `C1` | `quick_fix` | `continue_host_quick_fix` | - | README wording tweak returned to quick-fix; no active-plan hijack remains. |
| `SOP-11` | `C1` | `quick_fix` | `continue_host_quick_fix` | - | Typo fix returned to quick-fix; no design/runtime detour remains. |
| `SOP-12` | `C2` | `consult` | `continue_host_consult` | - | Pure explanation request stayed in direct consult. |
| `SOP-13` | `C2` | `consult` | `continue_host_consult` | - | State-explanation request stayed in direct consult. |
| `SOP-14` | `C1` | `quick_fix` | `continue_host_quick_fix` | - | Comment-only tweak returned to quick-fix; no over-stretch remains. |
| `SOP-15` | `C2` | `consult` | `continue_host_consult` | - | Existing plan meta-review bypass still works. |

## Sample Evidence

### SOP-01

- Request: 把 `runtime_gate` 和 `preferences_preload` 的 helper 合并成一个统一入口，减少 manifest 里的 limits 配置重复。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A4`
- Reviewer note: 已按约定落成“consult + analyze challenge”，重点从“直接开 plan”转为先挑战长期 contract/入口收敛假设。

### SOP-02

- Request: `current_handoff.json` 和 `current_run.json` 里都有 execution gate，是否应该收敛成一个唯一机器事实源？
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A4`
- Reviewer note: 不再被当成 plain consult 漏掉，已经显式识别为唯一机器事实源问题。

### SOP-03

- Request: 把 `~go exec` 改成普通开发主链路默认入口，省掉执行确认。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A2`
- Reviewer note: 现在先挑战“省掉 execution confirm”这条路径假设，符合 phase-1 先评后改的目标。

### SOP-04

- Request: 优化当前 decision checkpoint 体验，让用户觉得更顺一点。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A1`
- Reviewer note: 模糊体验诉求保持在轻量 challenge，不再被 active plan 的执行确认误伤。

### SOP-05

- Request: compare 结果现在读起来太重，想加更多解释文本；有没有更轻的改法？
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A3`
- Reviewer note: 现在能保住“更轻改法”的信号，不再直接落成普通问答。

### SOP-06

- Request: consult 路由要不要直接在 runtime 里生成正文回答，而不是只写 handoff？
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A4`
- Reviewer note: 已能把 consult/runtime contract 分叉显式暴露出来，符合这轮“先评后改，不做 consult body”的范围。

### SOP-07

- Request: `topic_key` 要不要重新参与 no-active-plan 自动复用？
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A4`
- Reviewer note: 不再漏掉长期复用策略层的问题。

### SOP-08

- Request: 想把 blueprint 和 `project.md` 的职责再统一一下，避免用户看不懂。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A1`
- Reviewer note: 仍保持轻量，不再错误跳到 execution-confirm 或正式 plan scaffold。

### SOP-09

- Request: 去掉 runtime gate，宿主直接调用默认 runtime 入口就行。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Route artifacts: `consult_mode=analyze_challenge`, `trigger_label=A2`
- Reviewer note: 现在先挑战“去掉 gate”这条 shortcut，而不是让 active plan 抢路。

### SOP-10

- Request: 补一行 README 里的 runtime gate helper 路径说明。
- Observed route: `quick_fix`
- Required host action: `continue_host_quick_fix`
- Runtime note: `Detected a bounded docs/tests wording tweak`
- Reviewer note: 典型 `C1` 已回到轻场景，不再触发 execution confirm 或 plan-binding decision。

### SOP-11

- Request: 修一个 `tests/test_runtime.py` 里断言文案的 typo。
- Observed route: `quick_fix`
- Required host action: `continue_host_quick_fix`
- Runtime note: `Detected a bounded docs/tests wording tweak`
- Reviewer note: typo fix 已稳定回到 quick-fix。

### SOP-12

- Request: 解释一下 `execution_confirm_pending` 和 `decision_pending` 的区别。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Reviewer note: 纯解释问题保持 direct consult，没有再被 checkpoint 拦截。

### SOP-13

- Request: 看下 `current_run.json` 当前状态是什么意思。
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Reviewer note: 纯状态解释问题保持 direct consult，没有再被 active plan 吃掉。

### SOP-14

- Request: 给 manifest 某个 limits 字段补一个简短注释。
- Observed route: `quick_fix`
- Required host action: `continue_host_quick_fix`
- Runtime note: `Detected a bounded docs/tests wording tweak`
- Reviewer note: 注释级别的小改动已回到 quick-fix。

### SOP-15

- Request: 这个 plan 现在还有哪些风险点？
- Observed route: `consult`
- Required host action: `continue_host_consult`
- Reviewer note: 原有 plan meta-review bypass 仍然成立，没有被这轮修复回归打坏。
