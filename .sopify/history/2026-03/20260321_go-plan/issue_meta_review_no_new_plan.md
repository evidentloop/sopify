# Issue: 元评审问题不应生成新 Plan

## 问题定义

当用户对当前 plan 做评分、风险复核、方案追问或元讨论时，runtime 不应把这类请求识别成新的 workflow/planning 请求，也不应生成新的 scaffold plan。

当前已经观察到相反现象：

- 对现有方案做评分或追问，会生成新的 `plan/YYYYMMDD_*` 目录。
- 新 scaffold plan 会污染当前 active plan 语义，增加 handoff 和 state 的噪音。

## 影响

- 干扰当前活动 plan 的 machine truth。
- 让“评审现有 plan”和“新建 plan”混在一起。
- 增加 `current_handoff.json`、`current_run.json` 与 plan 目录的解释成本。

## 初步根因假设

1. runtime-first guard 命中“process semantic intent”后，过早把元评审请求送入 `workflow`。
2. `consult` / review 类意图识别发生得太晚，没能优先接住“对现有 plan 的讨论”。
3. 当前路由没有显式识别“active plan review / critique / meta discussion”这类中间态。

## 本 Issue 范围

包含：

- 为元评审请求增加独立识别规则或 guard 旁路
- 调整 `runtime/router.py` 的 guard / consultation 判定顺序
- 增加回归样本，防止 plan 评分、复核、追问再次新建 scaffold

不包含：

- `v1 preferences.md + analyze` 的主实现
- “所有问答两段式输出”
- consult/runtime 输出风格扩展

## 建议验收标准

以下请求在存在 active plan 时，不得创建新的 scaffold plan：

1. “分析下这个方案的评分和风险”
2. “这个 plan 还有什么优化点”
3. “这里还需要我决策什么”

同时要求：

- 若只是评审现有 plan，应优先复用当前 active plan 上下文
- `current_handoff.json` 不得把此类请求误写成新的 planning scaffold handoff
- 至少提供 3 条回归样本覆盖评分、追问、风险复核

## 建议交付

- 一个独立修复任务块
- 一组路由判定测试
- 一次人工 smoke，确认 active plan 不再被元评审污染
