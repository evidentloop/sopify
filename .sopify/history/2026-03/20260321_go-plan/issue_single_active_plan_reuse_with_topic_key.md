# Issue: 严格单 Active Plan + Topic Key 元数据

## 问题定义

当前 runtime 的 planning 路径以“本次请求”为中心，而不是以“当前主题 / 当前活动 plan”为中心：

- 只要命中 `plan_only / workflow / light_iterate` 的 scaffold 分支，就会创建新的 `plan/YYYYMMDD_*` 目录。
- `current_plan.json` 只能表示单 active plan，但实现层会持续生成同级 sibling plan，导致 machine truth 与目录事实分裂。
- 元评审类请求一旦被误路由到 `workflow`，就会进一步放大这个问题。

## 本轮目标

把 runtime 收敛到以下规则：

1. 严格单 active plan。
2. 存在 active plan 时，默认复用该 plan，而不是再新建 scaffold。
3. 只有用户显式表达“新建 plan”或“切换到其他 plan”时，才允许偏离当前 active plan。
4. 无 active plan 时，默认创建新 plan；当前版本不启用 `topic_key` 自动匹配。
5. 本仓库现存重复 plan 先合并为一个 canonical active plan，再删除重复目录。

## Canonical Plan

当前 canonical active plan 定义为：

- `.sopify-skills/plan/20260321_go-plan`

当前应视为待合并或 superseded 的重复 plan：

- `.sopify-skills/plan/20260321_v1-preferences-md-analyze`
- `.sopify-skills/plan/20260321_task-a93812`
- `.sopify-skills/plan/20260321_task-ba2454`

## Merge Disposition

三份重复 plan 的处理方式不应等同于正式 history archive，而应先做“语义吸收”再删除目录：

- `20260321_v1-preferences-md-analyze`
  - 保留价值：`v1 只做 preferences.md + analyze`、深度交互默认强度、promotion gate、元评审独立 issue 的原始用户边界。
  - 已吸收位置：canonical `background.md / design.md / tasks.md`。
  - 删除理由：正文仍是默认 scaffold，没有独立可执行任务结构。
- `20260321_task-ba2454`
  - 保留价值：用户接受“平衡版门槛”，并要求把 `promotion gate` 写进主 plan、把“元评审不应生成新 plan”拆成独立 issue。
  - 已吸收位置：canonical `design.md` 的 promotion gate 与 `tasks.md` 的独立 issue 任务块。
  - 删除理由：只是对 canonical plan 的增量确认，不应继续作为 sibling plan 存在。
- `20260321_task-a93812`
  - 保留价值：对 canonical plan 做评分、优化点、待决策项、风险复核的元评审语义。
  - 已吸收位置：`issue_meta_review_no_new_plan.md` 与 router 回归样本约束。
  - 删除理由：这是对现有 plan 的 review，不是新的 plan。

## 选择策略

优先级固定如下：

1. 显式命令优先
2. 显式 plan 引用优先
3. 当前 active plan 复用
4. 创建新 scaffold

对应解释：

- 显式命令优先：若用户明确说“新建 plan / 另起一个 plan / 切到某个 plan”，runtime 必须尊重。
- 显式 plan 引用优先：若请求中出现具体 plan 路径或 plan id，则以该 plan 为目标。
- 当前 active plan 复用：若已有 active plan 且用户未明确要求切换，则默认继续在当前 plan 上操作。
- 无 active plan：直接创建新 scaffold，避免粗粒度 `topic_key` 误绑到旧主题。

## `topic_key` 定义

`topic_key` 不是自由文本 embedding，也不是模糊语义搜索；第一版只保留为可审计、可回放的 plan 元数据：

- 来源: 对请求主题做归一化 slug
- 存储方式: 写入 plan metadata 与 `PlanArtifact`
- 当前用途: 支持人工检查、重复 plan 语义合并、后续是否恢复自动复用的评估

这能保证后续持续迭代时：

- metadata 来源清晰
- 误绑定成本为零
- 规则容易版本化和回归测试

## 最近引入并放大的原因

这个问题不是单点 bug，而是三次收紧叠加后的结果：

1. `d92e668` 引入 runtime-backed plan scaffold，本身就是“命中 planning 就创建目录”，但当时还没有强 reuse 层。
2. `3bfdb27` 在 planning 主链路里直接固定 `create_plan_scaffold() -> set_current_plan()`，让“按请求新建”成为稳定默认路径。
3. `b310079` 把 runtime-first guard 提前到 consultation 之前，导致 plan 评分、追问、风险复核等元评审请求也更容易进入 planning 分支。

因此最近才表现为“几乎每次 plan 讨论都会新建一个 plan”。

另外，本轮验证后确认：

4. `topic_key` 的 slug 粒度过粗，像“补 runtime 骨架”和“优化 runtime”会同落 `runtime`，在无 active plan 场景下容易错误复用旧 plan。

## 交付范围

包含：

- `runtime/engine.py` 中的 plan reuse / switch / create 决策
- `runtime/plan_scaffold.py` 中的 `topic_key` 补充与 plan artifact 读取能力
- `runtime/router.py` 中 active-plan meta-review 的 consultation 旁路
- 当前工作区 state rebinding 到 canonical plan
- 重复 plan 的 superseded/merge/delete 策略
- 回归测试

不包含：

- 跨工作区全局 plan 检索
- 基于 embedding 的模糊 topic match

## 验收标准

1. 存在 active plan 且用户未显式要求切换时，`~go plan` 或相关 planning 请求不得创建新的 scaffold 目录。
2. “分析下这个方案的评分/风险/优化点/还需要我决策什么”这类元评审请求，不得生成新 plan。
3. 用户显式给出 plan 路径或 plan id 时，runtime 能切换并绑定到对应 plan。
4. 没有 active plan 时，runtime 默认创建新的 scaffold；即使存在同 `topic_key` 的旧 plan，也不自动复用。
5. 当前工作区的 `current_plan.json / current_run.json / current_handoff.json` 被重新绑定到 `20260321_go-plan`。
6. 重复 plan 目录在完成 merged provenance 记录后被删除，不写入正式 `history/index.md`。

## 当前建议

- 第一版不要做“多 active plan 池化”。
- 第一版不要做模糊语义匹配。
- 当前版本先把规则收敛到“单 active plan + 显式切换 + topic_key 元数据”，后续只有在 promotion gate 满足时才考虑恢复 no-active-plan 自动复用。
- 重复 scaffold 不应走 finalize，也不应进入正式 history；git 历史与 canonical plan 的 merged provenance 足以保留可追溯性。
