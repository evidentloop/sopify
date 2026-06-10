# 技术设计: 第一性原理规则分层落地

## 决策确认
- 问题: 第一性原理规则应先写入当前仓库的长期偏好，还是直接下沉为所有 Sopify 接入仓库共享的底层默认能力。
- 结果: 先选择 `option_1`，即写入当前 workspace 的长期偏好层，再从中提炼稳定子集下沉到 `analyze`。
- 决策 ID: `decision_0b7675d8`
- 候选方案:
  - `option_1`: 当前 workspace preference 先试运行，再提炼通用子集下沉到底层分析规则。推荐。
  - `option_2`: 直接下沉为所有 Sopify 仓库默认行为。不推荐作为第一步。

## 技术方案
- 核心技术:
  - workspace-scoped preference preload
  - analyze prompt-layer rules
  - promotion gate and evaluation criteria
  - single-active-plan reuse and topic-key metadata
- 实现要点:
  - 把“协作风格”与“稳定分析能力”分开管理。
  - 把“目标是否正确”与“路径是否最优”前置到分析阶段。
  - 把最终方案、任务、风险与验收继续按 SMART 收口。
  - 把升级条件写成可重复执行的准入门槛，而不是靠主观感觉提升。
  - 把 plan 生命周期从“按请求新建”修正为“按活动主题复用”。

### 0. 当前 Plan Canonicalization

本轮先固定一个 canonical active plan：

- `20260321_go-plan`

以下目录已完成语义吸收并删除，视为同一主题下误生成的重复 scaffold：

- `20260321_v1-preferences-md-analyze`
- `20260321_task-a93812`
- `20260321_task-ba2454`

machine state 也必须重新绑定到 canonical plan，避免 `current_plan.json` 与实际人工评审上下文继续分裂。

### 0.1 严格单 Active Plan 规则

默认规则：

1. 当前存在 active plan 时，planning 相关请求默认复用该 plan。
2. 只有用户显式说“新建一个 plan / 这是另一个 plan / 切到某个 plan”时，才允许切换或新增。
3. 如果没有 active plan，则默认新建 scaffold，不做 `topic_key` 自动复用。
4. `topic_key` 先只保留为元数据，用于可观测性、人工合并和后续是否晋升为默认规则的评估。

这样做的原因：

- `current_plan.json` 本身就是单 active plan 模型。
- blueprint / KB / finalize / handoff 都假设“当前 plan”是唯一机器事实源。
- 若 runtime 继续按请求生成 sibling plan，后续 execution gate、handoff、history 都会被污染。
- `topic_key` 的粗粒度 slug 在无 active plan 场景下容易误绑，例如多个“runtime”类请求会被错误视为同一主题。

### 0.2 Plan 选择优先级

本轮固定为：

1. 显式新建
2. 显式 plan 引用
3. 当前 active plan
4. 新建 scaffold

说明：

- “显式新建”是强信号，必须覆盖默认复用。
- “显式 plan 引用”包括 plan path 和 plan id。
- 若没有 active plan 且没有显式 plan 引用，则直接新建 scaffold。
- `topic_key` 当前只做元数据，不参与运行时自动选择。

### 0.3 `topic_key` 规则

第一版 `topic_key` 是 plan-level 元数据，不是自由发挥的语义标签，也不是当前运行时的自动复用依据。

定义：

- 从请求主题生成稳定 slug
- 写入 `PlanArtifact` 和 plan front matter
- 作为后续人工合并、观测统计和 potential promotion gate 的输入

边界：

- 它不是替代 active plan 的主决策依据
- 它在当前版本不参与“当前没有 active plan”时的自动匹配
- 若未来考虑恢复自动复用，必须先通过独立 promotion gate，并证明误绑风险可控

### 0.4 重复 Plan 合并策略

本仓库先采用保守合并：

1. 声明 `20260321_go-plan` 为 canonical active plan
2. 把重复 plan 中已确认的设计结论合并回 canonical plan
3. 重新绑定 `current_plan.json / current_run.json / current_handoff.json`
4. 在 canonical plan 中保留 merged provenance 后，删除重复 plan 目录

不做的事：

- 本轮不把重复 scaffold 伪装成正式 finalize history
- 本轮不额外创建 superseded archive 命名空间污染 `history/` 语义
- 本轮不做多 active plan registry
- 本轮不引入 clarification 专属 plan 池；仍坚持单 active plan 语义

### 0.5 最近引入问题的因果链

该问题是最近几轮 runtime 收紧后被放大的，不是旧设计自然就合理：

- `d92e668` 引入 `runtime/plan_scaffold.py`，默认行为就是命中 planning 后创建新 scaffold。
- `3bfdb27` 把 planning 主路径固定成 `create_plan_scaffold() -> set_current_plan()`，没有先做 reuse 判断。
- `b310079` 把 runtime-first guard 提前到 consultation 前，元评审问题更容易误入 planning。

结论：

- plan 重复生成的根因在 `engine + plan_scaffold`
- “元评审也被放进 planning”则是 `router` 新近放大的次级原因
- “无 active plan 时按 `topic_key` 自动复用”则是本轮确认需要收紧的第三个风险点
- 三者必须一起修，单修其一仍会残留噪音

### 0.6 从 7/10 提升到 8.5+ 的最小修补方案

当前已完成修复能解决：

- active-plan meta-review 不再误生成 scaffold
- decision resume 会复用 active plan

但若按工程质量继续打分，当前仍只能算 `7/10`，原因是还有两条残留边界：

1. clarification 分支仍会无条件清空 `current_plan`
2. `explicit new plan` 的文案匹配仍把 `其他 plan` 这类高歧义表述视作强信号

因此，最小修补只补三件事：

#### A. clarification 期间保留 active plan

- 把 clarification 分支的 `clear_current_plan()` 改成与 decision 分支一致的 preserve / rebind 逻辑
- 默认保留当前 active plan
- 只有显式新建或显式切到其他 plan 时才允许偏离

#### B. 收紧 explicit new-plan 文案边界

- 删除或收紧 `其他 plan` 这类歧义模式
- 保留真正的强信号：`new plan / create new plan / 新 plan / 另起一个 plan / 新增一个 plan`
- “比较其他 plan”必须继续落在 review / consult，而不是 scaffold

#### C. 把验证门槛补齐

- 新增 clarification reuse 回归测试
- 新增 `其他 plan` 文案边界测试
- 保留显式新建的正向测试
- 本轮允许安装 `pytest`，把 `python3 -m unittest` 之外的 `pytest` 跑通，避免只在一种测试入口下成立

这三项完成后，当前 issue 的目标分数可提升到 `8.5+/10`，且仍然保持“最小补丁、不扩模型”的策略。

### 1. 分层结论

#### A. `preferences.md` 层
适合承载：
- 两段式输出偏好：`直接执行` + `深度交互`
- 挑战用户路径的语气强度与默认态度
- “不要顺着模糊需求直接实现”这类当前 workspace 协作风格

不适合承载：
- 机器执行门禁
- route classifier 规则
- 全仓库共享的默认行为

原因：
- 现有 runtime preload 本来就是以 workspace 为边界注入长期偏好。
- 这类规则目前仍带有明显个人协作风格属性，直接全局化风险过大。

#### B. `analyze` 层
适合下沉的稳定子集：
- 先区分“用户给的是目标还是路径”
- 目标模糊时先停下补充关键事实
- 路径明显次优时，给出更低成本替代方案
- 在进入 design 之前，用 SMART 风格写出成功标准、边界和约束

不适合直接放入 `analyze` 的内容：
- 所有问答强制分成两段输出
- 默认持续质疑用户动机
- 对 `consult`、`quick_fix` 这类轻场景也强制展开深度挑战

原因：
- `analyze` 只覆盖 planning/workflow 相关链路，不覆盖纯 `consult` 问答。
- 因此把“两段式回答”只塞进 `analyze`，无法实现“所有问题都分两段”的目标。

#### C. `project.md` / blueprint 层
不建议承载此类规则。

原因：
- `project.md` 和 `blueprint/*` 的职责是项目技术约定、长期目标和知识布局。
- 这类文件不应用来存储“用户偏好的协作方式”。

#### D. runtime / host 输出层
只有在未来确认“所有问答都需要两段式输出”时，才应进入这一层。

对应能力会落在：
- `runtime/output.py`
- `runtime/router.py`
- 宿主 bridge 的输出契约

建议：
- 作为二期能力，且必须配置化，不应直接变成硬默认。
- 当前 `v1` 明确不进入该层。

### 2. 第一性原理与 SMART 的结合方式

第一性原理负责纠偏，SMART 负责收口。

- Specific:
  - 第一性原理先追问“真实目标是什么、当前方案是不是把路径误当目标”。
  - SMART 再把确认后的目标压缩成明确交付物与边界。
- Measurable:
  - 深度交互要输出为什么当前路径次优，以及替代方案的代价差异。
  - design/tasks 要输出可验证完成标准。
- Achievable:
  - 第一性原理负责找更低成本路径。
  - SMART 负责确保任务粒度和资源投入可执行。
- Relevant:
  - 深度交互优先检查 XY 问题和目标偏移。
  - 设计文档继续约束方案与原始目标强相关。
- Time-bound:
  - SMART 约束任务颗粒度、下一步动作与停点。
  - 第一性原理只负责前置判断，不无限扩展讨论。

结论：
- 第一性原理决定“做对的事”。
- SMART 决定“把事做成且能验收”。
- 两者不是替代关系，而是前后串联关系。

### 3. Skills 组合方式

#### `analyze`
增强点：
- 在需求评分前后加入“目标 vs 路径”检查。
- 当目标模糊时优先触发 clarification，而不是靠主观补全。
- 当路径明显非最优时，在分析摘要中给 1 个更短或更低成本替代方案。
- 在 Phase B 结尾显式产出 SMART 风格成功标准。
- 深度交互只在“明显信号”命中时触发，不把挑战式交互变成默认冗长输出。

#### `design`
增强点：
- 在方案摘要中区分“用户当前要求的路径”和“推荐路径”。
- 对推荐方案补一行 tradeoff 理由，避免只给结论不给依据。
- tasks 保留 SMART 粒度与验收，不负责“挑战用户动机”。

#### `develop`
增强点：
- 执行时延续“若实现路径偏离目标则回推 checkpoint”的意识。
- 不主动展开新的大段挑战；只有命中 scope/risk fork 时再进入 checkpoint。

#### `kb`
增强点：
- 保持 `preferences.md` 只记录明确长期偏好。
- 不把本轮一次性提示或临时挑战语气回写为长期规则。

#### `workflow-learning`
增强点：
- 记录“原路径 / 推荐替代路径 / 最终选路理由”。
- 让未来回放能解释为什么当时没有顺着用户字面要求直接执行。

### 3.1 明显信号定义

深度交互默认不常开，只有在满足以下条件时才触发：

- 命中 `1` 个强信号；或
- 同时命中 `2` 个弱信号。

强信号：
- 用户明确在多个方案、策略或长期契约之间选路。
- 用户给出的内容明显是“实现路径”，而非“真实目标”。
- 已知存在更短、更低成本或更低风险的替代路径。
- 当前路径与显式约束冲突。

弱信号：
- 需求评分不足，尤其目标、边界或约束缺失。
- 请求涉及跨模块或较大改动，但没有成功标准。
- 当前路径成本偏高，但还不足以直接判定为错误。

默认不触发场景：
- 纯 `quick_fix`
- 纯 `consult` 且问题目标清晰、无明显分叉
- 已明确给出目标、边界、约束、且路径已基本最优的请求

### 3.2 Promotion Gate

`workspace pilot -> analyze 默认规则` 的升级必须通过固定门槛，不允许基于“感觉有效”直接提升。

#### A. 可升级范围

只允许升级以下 4 条 analyze 子规则：

1. 区分目标与路径
2. 目标模糊时优先澄清
3. 路径明显次优时给出低成本替代
4. 用 SMART 风格收口成功标准

明确禁止升级的内容：

- “所有问题都分成直接执行 + 深度交互”
- 持续质疑用户动机的默认语气
- 任何只属于当前 workspace 的个人表达风格

#### B. 必备前置产物

在申请提升前，必须先具备：

1. 明显信号定义与 trigger matrix
2. 至少 1 组正例和 1 组反例样本
3. pilot 反馈记录与人工评审摘要
4. quick-fix 控制样本结果
5. 可复现的版本说明，能说明本轮规则与上一轮差异

#### C. 样本要求

最小样本集：

- 总样本数 `>= 45`
- analyze 适用样本 `>= 30`
- 控制样本 `>= 15`

控制样本必须覆盖：

- `quick_fix`
- 纯 `consult`
- 目标和路径都已清晰、且无需挑战的请求

pilot 覆盖仓库至少 3 类：

- 业务应用仓库
- runtime / infra 仓库
- quick-fix 高频仓库或等价控制样本仓库

#### D. 通过阈值

建议采用平衡版门槛：

- 人工评审“触发后有帮助”的比例 `>= 80%`
- 不该触发却触发的误报率 `<= 10%`
- 该触发却未触发的漏报率 `<= 20%`
- 中位额外交互成本 `<= 1` 轮
- `quick_fix` 控制样本中，不允许出现系统性拉长或错误改路

只有全部满足，才允许把对应子规则提升为 `analyze` 默认规则。

#### E. 回滚条件

任一条件命中即回滚为 workspace-only：

- 升级后 2 周内误报率升到 `> 15%`
- quick-fix 出现稳定退化趋势
- 用户反馈集中指向“对轻场景过重”
- 中英文 prompt-layer 或 Codex/Claude 镜像出现语义漂移

#### F. 持续迭代方式

promotion gate 不是一次性审批，而是每轮都重复执行：

1. 记录本轮规则版本
2. 跑固定样本集和控制样本
3. 记录阈值结果、正反例与用户反馈
4. 只调整触发信号、示例和阈值，不混入新的风格性规则
5. 若规则变化较大，重新按 pilot 身份观察，不继承旧版本通过资格

这能保证后续优化是“可持续收紧/放宽”的演进，而不是一次通过后永久放行。

#### G. Round 1 Decision Pass

在完整 `45` 样本 / `3` 类环境聚合完成后，本 plan 单独执行一次 `hold / review / propose-promotion` decision pass，最终结论固定为：

- `propose-promotion`

该结论的正式含义：

- 当前四条 `analyze` 稳定子规则已经具备从 workspace pilot 升级为默认能力的证据基础。
- `Batch 2/3` 的 caution 继续保留，但只进入后续 wording/examples 优化，不再作为本轮 promotion 决策的前置阻断项。
- “所有问答都两段式输出”仍然保留在二期，不因本轮 decision pass 被提前并入 `consult/runtime` 默认契约。
- 后续若继续调 trigger wording、正反例或阈值，属于正常迭代，不回退本轮已经完成的 promotion 决策。

### 4. 跨仓库接入场景

#### 场景 A: 应用业务仓库
收益：
- 用户常给出实现路径而不是真正目标，第一性原理检查能有效减少错误重构。
- SMART 收口能让交付更容易验收。

风险：
- 若深度交互过重，会拖慢简单需求迭代。

建议：
- 默认启用 analyze 子集。
- 两段式输出保持在 preference 或可选配置。

#### 场景 B: runtime / infra 仓库
收益：
- 更容易识别“想修现象还是想修系统根因”。
- 对架构取舍和长期契约讨论价值高。

风险：
- 频繁挑战会让 checkpoint 过多。

建议：
- analyze 中保留强目标校验。
- runtime 全局化前先做显式开关。

#### 场景 C: SDK / 工具仓库
收益：
- 可避免把接口实现手段误当产品目标。
- 替代方案提示能压缩实现范围。

建议：
- 重点启用“目标/路径分离”和“更低成本路径建议”。

#### 场景 D: quick-fix 高频仓库
风险最大：
- 如果默认要求两段式深度交互，会显著增加轻量修复成本。

建议：
- quick-fix 只保留很轻的目标校验，不强制两段式。

#### 场景 E: 以咨询为主的仓库
关键结论：
- 若真要实现“所有问题必须分成直接执行 + 深度交互”，必须补到 consult/host 输出层。
- 仅修改 analyze 不会覆盖这一类请求。

### 5. 独立 Issue: 元评审不应生成新 Plan

该问题不纳入 `v1 preferences.md + analyze` 的主实现范围，但需要独立跟踪。

问题定义：

- 用户对现有 plan 做评分、追问、复核或元讨论时，不应被 route classifier 误判为新的 workflow / plan 生成请求。
- 当前行为会污染 active plan，并制造多余的 scaffold plan。

初步判断：

- 触发点位于 runtime-first guard 与 consultation 判定之间。
- 需要单独评估 `runtime/router.py` 的 guard 顺序、关键词与已有 active plan 上下文恢复逻辑。

交付方式：

- 以独立 issue 文件和独立任务块跟踪。
- 等 `v1` 主体落地后再修，不与主方案耦合发布。

## 架构设计
建议采用三层演进：

1. `preferences.md` pilot
2. `analyze` 提炼通用子集
3. `consult/runtime` 配置化扩展

职责边界：
- `preferences.md`: 当前 workspace 的长期协作风格
- `analyze`: planning 路由的通用分析能力
- `design`: 推荐方案与任务拆分
- `develop`: 执行中发现偏航时回调 checkpoint
- `runtime/output`: 若未来要覆盖所有问答，则在这一层定义输出形态

## 安全与性能
- 安全:
  - 一次性任务指令不自动回写为长期偏好。
  - 不把个人风格直接固化为所有仓库默认规则。
- 性能:
  - 轻问答和 quick-fix 不应默认触发完整深度交互。
  - 只把稳定子集下沉到 `analyze`，避免每条请求都增加高成本推理。
- 兼容性:
  - `Codex/Skills/{CN,EN}` 继续作为 prompt-layer 真源。
  - `Claude/Skills/{CN,EN}` 通过 sync 生成镜像，避免双份手改漂移。
