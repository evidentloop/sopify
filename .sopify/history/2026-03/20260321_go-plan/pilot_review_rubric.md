# Pilot Review Rubric

## 目的

本文件定义首轮 promotion gate pilot 的人工评审 rubric 和记录模板，重点固定以下 3 个核心观察项：

1. 触发后是否有帮助
2. 是否误伤轻场景
3. 额外交互轮次是多少

它对应当前 plan 中的人工评审任务，不等同于最终门槛冻结文档。

## 评审维度

### 1. Trigger Correctness

判断这次请求是否被“正确地介入”：

- `correct_trigger`
  - 该触发时触发了，或该保持轻量时保持轻量了
- `over_trigger`
  - 不该触发却触发了，尤其是 `C1/C2` 被拉长
- `under_trigger`
  - 应该触发却没有触发，导致直接顺着问题路径推进

### 2. Helpfulness

只评价“这次介入是否真的提升了结果”，不评价措辞风格。

- `helpful`
  - 纠正了错误目标、暴露了更优路径、补齐了关键事实、或让方案更可验收
- `neutral`
  - 介入没有明显增益，但也没有造成明显损害
- `not_helpful`
  - 介入只增加了讨论成本，未带来实质性改进
- `n/a`
  - 没有发生实际介入，或该项不适用

### 3. Light-Scene Harm

只用于判断轻场景是否被误伤：

- `none`
  - 没有把轻场景拉长，也没有错误改路
- `minor`
  - 增加了轻微讨论成本，但没有改变最终路径
- `major`
  - 系统性拉长、错误改路，或让 quick-fix / consult 明显变重
- `n/a`
  - 非控制样本，或该项不适用

### 4. Extra Turns

记录由于第一性原理层介入而新增的额外交互轮次：

- `0`
- `1`
- `2`
- `3+`

说明：

- 只统计“本来可直接回答 / 直接执行，但因为介入而新增”的轮次
- 常规确认语、非关键寒暄不计入
- 对 `A1` 样本中的轻量 clarification，也计入额外交互

## 行为记录口径

`actual_behavior` 固定为以下 3 类：

- `deep_trigger`
  - 进入了明确的深度交互或替代路径挑战
- `light_clarification`
  - 只进行简短事实澄清，没有展开完整挑战
- `direct_no_trigger`
  - 直接回答 / 直接执行，没有显式介入

评审注意：

- `A1` 样本出现 `light_clarification` 不一定算失败；关键看它是否足以补齐事实，且没有把小问题过度拉长
- `C1/C2` 样本出现 `deep_trigger` 通常应优先判为 `over_trigger`

## 聚合指标口径

### 1. 有帮助率

```text
helpfulness_rate = helpful_count / intervention_count
```

其中：

- `intervention_count = deep_trigger + light_clarification`
- `helpful_count` 只统计 `helpful`

### 2. 误报率

```text
false_positive_rate = over_trigger_on_expected_no_trigger / expected_no_trigger_count
```

其中：

- `expected_no_trigger_count` 来自 `C1/C2`
- 对 `C1/C2` 样本，若 reviewer 判为 `over_trigger`，即计入误报

### 3. 漏报率

```text
false_negative_rate = under_trigger_on_expected_trigger / expected_trigger_count
```

其中：

- `expected_trigger_count` 来自 `A1/A2/A3/A4`
- 对 `A*` 样本，若 reviewer 判为 `under_trigger`，即计入漏报

### 4. 中位额外交互成本

```text
median_extra_turns = median(extra_turns for intervention samples)
```

其中 intervention samples 指：

- `deep_trigger`
- `light_clarification`
- `consult_challenge_trigger`

### 5. quick-fix 退化旗标

满足以下任一条件，应标记 quick-fix regression：

- 任一 `C1` 样本出现 `major` 级别误伤
- 多个 `C1` 样本稳定出现 `minor` 以上误伤
- `C1` 样本被错误改路到明显更重的分析/设计链路

## 单样本记录模板

建议每条样本至少记录以下字段：

| Field | Allowed Values / Example |
| --- | --- |
| `sample_id` | `SOP-01` / `FH5-07` / `RS-12` |
| `environment` | `runtime/infra` / `business` / `sdk/tool + quick-fix/control` |
| `repo` | `sopify-skills` / `freyr-h5pages` / `rs-sdk` |
| `label` | `A1/A2/A3/A4/C1/C2` |
| `signal_basis` | `S2` / `S1 (+S4)` / `N1` |
| `expected_behavior` | `trigger` / `no_trigger` |
| `candidate_request` | raw request text from the sample matrix |
| `actual_behavior` | `deep_trigger` / `light_clarification` / `consult_challenge_trigger` / `direct_no_trigger` |
| `trigger_correctness` | `correct_trigger` / `over_trigger` / `under_trigger` |
| `helpfulness` | `helpful` / `neutral` / `not_helpful` / `n/a` |
| `light_scene_harm` | `none` / `minor` / `major` / `n/a` |
| `extra_turns` | `0` / `1` / `2` / `3+` |
| `final_disposition` | `accepted` / `partially_accepted` / `rejected` |
| `evidence_path` | transcript / screenshot / log path |
| `notes` | free text |
| `reviewer` | name or id |
| `reviewed_at` | `YYYY-MM-DD` |

## Markdown 记录模板

```md
| sample_id | environment | repo | label | signal_basis | expected_behavior | candidate_request | actual_behavior | trigger_correctness | helpfulness | light_scene_harm | extra_turns | final_disposition | evidence_path | notes | reviewer | reviewed_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SOP-01 | runtime/infra | sopify-skills | A4 | S1 (+S4) | trigger | 把 `runtime_gate` 和 `preferences_preload` 的 helper 合并成一个统一入口，减少 manifest 里的 limits 配置重复。 | deep_trigger | correct_trigger | helpful | n/a | 1 | accepted | logs/pilot_round1/SOP-01.md | 明确指出 helper 合并会扩大 host contract 变更面。 | wxl | 2026-03-22 |
```

## Reviewer Guidance

1. 优先看结果质量，不要只看回答是否“像分析”
2. 不要因为表达强硬就自动判为 helpful；必须有实质收益
3. 对 control 样本更严格，尤其关注是否把轻场景拉长
4. 若样本本身标签选错，先记录重分类原因，再继续打分
5. 同一轮 pilot 中，尽量由固定 reviewer 集合评审，减少口径漂移
