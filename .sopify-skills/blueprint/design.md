# 文档治理蓝图设计

状态: 文档已收口，部分已实现
创建日期: 2026-03-17

## 设计原则

1. 默认行为优先于用户配置
2. 工程化生命周期优先于语义化记忆
3. 索引与深层文档分层，避免首次触发写得过重
4. 单活动 plan 优先，历史归档延后到收口时
5. Blueprint 是长期真相；plan/history 是执行资产

## 目录契约

```text
.sopify-skills/
├── blueprint/              # 项目级长期蓝图，默认进入版本管理
│   ├── README.md           # 项目入口索引，首次触发即可创建
│   ├── background.md       # 长期目标、边界、约束、非目标
│   ├── design.md           # 模块边界、宿主契约、目录契约、关键数据流
│   └── tasks.md            # 长期演进项与待办
├── plan/                   # 当前活动方案，默认忽略
│   └── YYYYMMDD_feature/
├── history/                # 收口归档，默认忽略
│   ├── index.md
│   └── YYYY-MM/
│       └── YYYYMMDD_feature/
├── state/                  # 运行态状态，始终忽略
└── replay/                 # 可选回放能力，始终忽略
```

## 首次触发生命周期

### A. 首次 Sopify 触发

在 runtime 固定入口中执行 `ensure_blueprint_index(...)`：

- 不依赖用户命令是否进入 plan
- 不依赖咨询/设计/开发语义
- 只依赖“当前目录是否为真实项目仓库”的机器判定

真实项目仓库判定建议：

- 命中以下任一条件即视为真实项目：
  - 存在 `.git/`
  - 存在 `package.json / pyproject.toml / go.mod / Cargo.toml / pom.xml / build.gradle`
  - 存在 `src / app / lib / tests / scripts` 等目录

若命中且 `blueprint/README.md` 缺失：

- 只创建 `blueprint/README.md`
- 不在咨询场景强行创建 `background.md / design.md / tasks.md`

### B. 首次进入 plan 生命周期

进入 `plan_only / workflow / light_iterate` 时：

- 若 `blueprint/background.md / design.md / tasks.md` 缺失，则补齐
- 创建当前活动 `plan/`
- 写入本次方案的机器元数据

## Blueprint README 强约束模板

`blueprint/README.md` 是项目级全局索引，必须固定包含以下区块：

1. 当前目标
2. 项目概览
3. 架构地图
4. 关键契约
5. 当前焦点
6. 深入阅读入口

其中索引性区块采用托管标记，便于后续自动刷新：

```md
<!-- sopify:auto:goal:start -->
...
<!-- sopify:auto:goal:end -->
```

设计要求：

- 托管区块只写高密度摘要，不写长篇论证
- 非托管区块允许人工补充背景说明
- 自动刷新只更新托管区块，不覆盖人工说明

## Plan 元数据契约

不新增独立元数据文件，优先使用现有 plan 文件头部承载机器字段：

- `light`: 写入 `plan.md`
- `standard / full`: 写入 `tasks.md`

最小字段建议：

```yaml
plan_id:
feature_key:
level: light|standard|full
lifecycle_state: active|ready_for_verify|archived
blueprint_obligation: index_only|review_required|design_required
archive_ready: false
```

默认映射：

- `light` -> `index_only`
- `standard` -> `review_required`
- `full` -> `design_required`

说明：

- `standard` 是否真的需要更新深层 blueprint，不再完全依赖语义猜测，而是在收口阶段结合改动类型与 obligation 共同判断
- `full` 视为必须同步深层 blueprint
- 第一版 runtime 通过显式 `~go finalize` 执行收口事务；旧遗留 plan 不自动迁移，只支持 metadata-managed plan

## 主链路语义

第二阶段正式蓝图将主入口语义收敛为：

- 普通自然语言开发请求：默认按标准开发流自动推进
- `~go`：显式要求走标准开发流，但不绕过执行前确认
- `~go plan`：显式要求只生成或更新 plan，不进入代码执行
- `~go exec`：只作为恢复、调试、高级显式入口
- `~go finalize`：显式收口入口

关键约束：

1. 主链路的目标是自动推进到“执行前确认”，不是自动绕过确认直接写代码
2. `~go plan` 永远停在 plan
3. `~go exec` 不再是普通用户的必经步骤
4. `~go exec` 不能绕过 `clarification_pending / decision_pending / execution_confirm_pending`

## Plan 完成度与执行状态

需要明确区分以下概念：

- `plan generated`: plan 文件已生成
- `plan ready_for_execution`: plan 已通过机器执行门禁
- `plan accepted_for_execution`: 用户已明确回复 `继续 / next / 开始`

也就是说，plan 文件存在并不等于当前已经允许进入 develop。

## 第二阶段主链路状态机

第二阶段建议增加更清晰的主链路状态机：

```text
draft
  -> clarification_pending
  -> decision_pending
  -> ready_for_execution
  -> execution_confirm_pending
  -> executing
  -> ready_for_verify
  -> archived
```

状态语义：

- `clarification_pending`: 缺关键事实信息，继续澄清，不生成可执行 plan
- `decision_pending`: 存在长期契约分叉或未消解关键风险，需要用户拍板
- `ready_for_execution`: 机器执行门禁已通过
- `execution_confirm_pending`: plan 已完成，等待用户确认开始写代码
- `executing`: 已进入 develop
- `ready_for_verify`: develop 已完成，等待验证与显式 finalize

## 机器执行门禁

第二阶段的自动推进必须先经过统一的机器执行门禁。

只有同时满足以下条件，才允许从 plan 进入执行前确认：

1. 当前路由不是 `plan_only`
2. 当前不存在 pending decision
3. 当前不存在缺失的关键事实信息
4. plan 结构完整，且 tasks 已生成
5. 当前没有阻塞性任务或未消解关键风险
6. 原始路由语义允许进入执行

建议把门禁结果收敛为固定 machine contract，而不是靠 `Next:` 文案猜测：

```yaml
gate_status: blocked|decision_required|ready
blocking_reason: missing_info|unresolved_decision|destructive_change|auth_boundary|schema_change|scope_tradeoff|none
plan_completion: incomplete|complete
next_required_action: answer_questions|confirm_decision|confirm_execute|continue_host_develop
```

## 澄清与决策分流

第二阶段正式收敛为以下规则：

- 缺事实信息 -> `clarification_pending`
- 方案分叉、不可逆风险、权限/认证、数据/schema、范围取舍 -> `decision_pending`
- 风险已被 plan 吸收并给出缓解措施 -> 允许进入执行前确认，不再回到决策

这意味着：

- `clarification_pending` 与 `decision_pending` 都表示“plan 尚未完成”
- 只有两者都被消解后，plan 才可能变成 `ready_for_execution`

## 执行前用户确认

代码执行前必须再过一层统一的用户确认。

正式契约建议：

1. 机器执行门禁通过后，不直接进入 develop
2. runtime 或宿主输出“plan 已完成，可以 next”的统一提示
3. 用户可用自然语言 `继续 / next / 开始` 确认执行
4. 确认后才进入 `executing`

执行确认应最少展示：

- plan 路径
- 一句话方案摘要
- 任务数
- 风险级别与关键缓解

## `~go exec` 的降级定位

`~go exec` 在第二阶段正式降级为高级恢复入口：

- 用于中断恢复
- 用于宿主调试
- 用于高级用户显式接管

明确禁止：

- 不得作为普通主链路的必经步骤
- 不得绕过 `decision_pending`
- 不得绕过执行前用户确认
- 不得把 still-blocked 的 plan 强行推进到 develop

## 第二阶段里程碑蓝图

第二阶段建议按以下顺序落地，而不是并行散落实现：

### M1. 主链路状态骨架

目标：

- 先把 `clarification_pending / decision_pending / ready_for_execution / execution_confirm_pending / executing` 这些状态接入 runtime
- 先把路由、状态、输出、manifest、handoff 名称统一

为什么先做：

- 没有统一状态骨架，后面的 gate、confirm、resume 都只能继续散落在条件分支里

完成标准：

- runtime 内部可以稳定表达“待澄清”“待决策”“待执行确认”
- 普通请求、`~go`、`~go plan`、`~go exec` 的主链路分支已经固定

### M2. 机器执行门禁

目标：

- 引入统一 execution gate evaluator
- 让“plan 已生成”与“plan 已可执行”成为两个不同的 machine state
- 决策确认完成后，必须重新过 gate

为什么第二个做：

- 只有先把 gate 固化，后面的执行前确认才不会变成纯文案提示

完成标准：

- `blocked / decision_required / ready` 三类门禁结果已稳定
- decision confirmed 后不会直接跳进 develop

### M3. 执行前用户确认

目标：

- 在 gate 通过后统一进入 `execution_confirm_pending`
- 宿主与 runtime 统一消费 `confirm_execute`
- 用户通过自然语言 `继续 / next / 开始` 确认执行

为什么第三个做：

- 执行确认必须建立在 plan 已真正达到 `ready_for_execution` 的前提上

完成标准：

- 普通用户不需要记住 `~go exec`
- 代码执行前一定会出现一次轻量确认

### M4. `~go exec` 高级恢复入口化

目标：

- 彻底把 `~go exec` 从主链路中降级出去
- 只保留中断恢复、宿主调试、高级用户显式接管三类用途

为什么第四个做：

- 只有主链路和执行确认稳定后，才能准确限制 `~go exec` 的边界

完成标准：

- `~go exec` 不能绕过澄清、决策、执行确认
- 用户口径与宿主文档都不再把 `~go exec` 当默认下一步

### M5. 回归验证与外围评估

目标：

- 为第二阶段状态机补自动化测试
- 验证 repo-local runtime 与 vendored bundle 一致
- 最后再评估 compare / blueprint 刷新 / history 聚合等外围能力

为什么最后做：

- 外围能力不应在主链路门禁尚未稳定前扩张

完成标准：

- 第二阶段核心链路有回归保护
- 外围能力评估建立在稳定主链路之上

## 收口事务

不依赖 commit hook；使用固定的“收口事务”统一完成文档生命周期。

第一版实现边界：

- 触发入口固定为 `~go finalize`
- `~go finalize` 本身就是“准备交付验证”的显式收口信号
- 仅支持新 runtime 生成、带 front matter 元数据的活动 plan
- 若当前 plan 不满足 metadata-managed 前提，应直接拒绝，而不是隐式修复或自动迁移旧 plan

建议事务顺序：

1. 校验当前 plan 属于 metadata-managed；显式 finalize 时把本轮视为 ready-for-verify 收口点
2. 刷新 `blueprint/README.md` 托管区块
3. 根据 `blueprint_obligation` 判断是否要求更新 `background.md / design.md / tasks.md`
4. 归档当前 plan 到 `history/YYYY-MM/...`
5. 更新 `history/index.md`
6. 清理或更新 `current_plan / current_run / current_handoff`

## Blueprint 更新规则

### Light

- 不要求更新深层 blueprint
- 允许只刷新 `blueprint/README.md` 的索引摘要

### Standard

文档责任仍然针对以下变化类型：

- 模块边界变化
- 宿主接入契约变化
- manifest / handoff 契约变化
- 目录契约变化
- 长期技术约定变化

第一版 runtime 的工程化判定先收敛为：

- 若 `blueprint/background.md / design.md / tasks.md` 的修改时间晚于当前 plan 元数据文件，则视为“已完成深层 blueprint 更新”
- 若未命中，则输出 `review_required` 软提醒，但不阻断 finalize

### Full

- 必须更新 `background.md / design.md / tasks.md`
- `README.md` 同步刷新当前焦点、关键契约与阅读入口
- 第一版 runtime 对 `design_required` 采用硬阻断：未检测到 plan 创建后的深层 blueprint 更新时，不允许 finalize

## History 契约

`history/` 只在“本轮任务收口、准备交付验证”时写入：

- 平时不与当前 `plan/` 双写
- 不做实时镜像
- 不做多个 plan 自动归并

单次 plan 的归档规则：

- 一个活动 plan 对应一个归档目录
- `history/index.md` 只记录摘要索引
- 归档后 `plan/` 中不再保留该活动方案的工作态职责

## Replay 契约

- `replay/` 保持为可选能力
- 不作为“接入 Sopify 后必须完整支持”的基础文档治理要求
- 若启用 `workflow-learning`，仍可按独立能力写入本地 replay 资产

## 与决策确认能力的衔接

决策确认能力（decision checkpoint）应建立在本蓝图之上：

1. 仅在 design 阶段自动触发
2. 触发时先暂停正式 plan 生成
3. 将待确认状态写入 `state/current_decision.json`
4. 用户确认后再生成唯一正式 plan
5. 选择结果先写入当前 plan
6. 若形成长期稳定结论，再在收口时同步到 blueprint

这样可以同时满足：

- 不引入多份 draft plan
- 不要求用户额外配置
- 不把关键决策只留在聊天上下文里
- 决策完成后重新回到机器执行门禁，而不是直接跳进 develop

## 决策确认触发契约

### 自动触发条件

第一版 runtime 已按确定性规则落地自动触发：

- 仅在 `plan_only / workflow / light_iterate` 中生效
- 仅对显式多方案输入触发，当前识别符包括 `还是 / vs / or`
- 同时要求命中长期契约关键词（如 `runtime / payload / manifest / blueprint / 目录 / 宿主 / workspace`）

也就是说，第一版先优先保证“严谨可测”，而不是对所有隐式分叉都做激进猜测。

只有同时满足以下条件，才进入 decision checkpoint：

1. 当前已进入 `design` 阶段，而不是咨询、快速修复或 develop 收口
2. 至少存在 2 个都可实施的候选方案
3. 候选方案差异涉及长期契约，而不是局部实现细节
4. 不同选择会改变后续 plan 内容、任务拆分或 blueprint 写入结果
5. 现有 `project.md / blueprint / 当前活动上下文` 不能直接推导唯一答案

长期契约分叉典型包括：

- 宿主接入契约
- payload / manifest / handoff 结构
- 目录落点与生命周期
- 模块边界或职责切分
- 持久化格式与状态文件协议
- 依赖引入策略或验证链路

### 不触发条件

以下情况不应触发 decision checkpoint：

- 只是命名、注释、文案、排版等轻量差异
- 只有一个方案符合现有契约，其他候选明显无效
- 已被 `project.md` 或 blueprint 明确写死
- `light` 级任务内的局部实现细节
- 单纯为了给用户“看起来有选择”而构造伪分叉

## 决策状态机

决策确认采用单 pending 模型，每个仓库同一时刻只允许一个未完成决策：

```text
none
  -> pending      # design 识别到需拍板的分叉，写入 current_decision.json
  -> collecting   # 宿主已开始采集结构化表单，但尚未提交恢复
  -> confirmed    # 用户选定方案，但正式 plan 尚未完全物化
  -> consumed     # 已基于确认结果生成唯一正式 plan
  -> cancelled    # 用户取消，本轮 design 不继续产出正式 plan
  -> timed_out    # 宿主采集超时，需要用户重新恢复或重试
  -> stale        # 上下文已变化，原决策不再可信，需要重建
```

状态要求：

- `pending` 时，plan 不得提前生成
- `collecting` 时，宿主可继续编辑 submission，但 runtime 仍不得提前物化正式 plan
- `confirmed` 时，必须保留足够信息让 runtime 能幂等恢复 plan 物化
- `consumed` 后，应清理当前决策状态，避免后续误恢复
- `cancelled` 后，不生成正式 plan，由用户重新发起设计或修改需求
- `timed_out` 后，允许宿主提示用户重试，但 runtime 不应直接沿用未完成 submission
- `stale` 只表示状态失效，不等于用户已经完成选择

## `state/current_decision.json` 契约

第一版不新增多文件协议，统一落到：

```text
.sopify-skills/state/current_decision.json
```

建议最小字段：

```yaml
schema_version: "2"
decision_id:
feature_key:
phase: design
status: pending|collecting|confirmed|consumed|cancelled|timed_out|stale
decision_type:
question:
summary:
options:
  - id:
    title:
    summary:
    tradeoffs:
    impacts:
    recommended: true|false
checkpoint:
  checkpoint_id:
  title:
  message:
  primary_field_id:
  recommendation:
  fields:
    - field_id:
      field_type: select|multi_select|confirm|input|textarea
      label:
      description:
      required: true|false
      default_value:
      when:
      validations:
      options:
        - id:
          title:
          summary:
submission:
  status: empty|draft|collecting|submitted|confirmed|cancelled|timed_out
  source:
  answers:
  raw_input:
  message:
  submitted_at:
  resume_action:
recommended_option_id:
default_option_id:
context_files:
  - project.md
  - .sopify-skills/blueprint/README.md
resume_route:
selection:
  option_id:
  source: interactive|text|debug_override
  raw_input:
created_at:
updated_at:
confirmed_at:
consumed_at:
```

字段要求：

- `options` 应限制为 2-3 个高价值候选；超过 3 个时，design 先自行压缩 shortlist
- `checkpoint` 是宿主优先消费的主契约；`question/options/recommended_option_id` 继续作为 legacy projection 保留
- `submission` 是宿主回写结构化采集结果的唯一入口；runtime 恢复时优先消费它，而不是只靠自由文本解析
- `recommended_option_id` 必须存在，且推荐理由要能落到输出摘要
- `raw_input` 允许保留用户自由输入，但后续只进 plan，不直接写 blueprint
- `context_files` 用于恢复时提示模型优先读取哪些文件，而不是重新扫全仓

## 交互契约

### 主路径

第一版主路径只支持 design 自动触发：

1. design 识别到长期契约分叉
2. 写入 `current_decision.json`
3. 写入 `current_handoff.json`，其中 `required_host_action == confirm_decision`
4. 宿主优先读取 `artifacts.decision_checkpoint` 渲染交互，并将结果归一化为 `DecisionSubmission`
5. 宿主在同一工作区重新调用默认 runtime 入口
6. runtime 进入 `decision_resume`，消费 submission 或旧版文本输入
7. 用户确认后继续生成唯一正式 plan

### 交互形态

当前文档范围内，交互契约应收敛为 CLI 型宿主桥接，而不是并列设计 editor-side UI：

- CLI 型宿主
  - 当前默认使用内置 interactive renderer
  - richer terminal UI 仍只算宿主实现细节，缺少依赖时必须退化到纯文本桥接
- 旧版兼容
  - 对单选类 checkpoint，仍保留 `1 / 2 / ~decide choose <option_id>` 文本路径

统一要求：

- 宿主优先消费 handoff 中的 `artifacts.decision_checkpoint`
- 采集结果统一归一化为 `DecisionSubmission`
- 写回后仍通过默认 runtime 入口恢复，不新增新的主入口脚本
- 当前已通过内部 helper `scripts/decision_bridge_runtime.py` 落地 `inspect / submit / prompt`；它只服务 `confirm_decision`，不替代默认入口
- vendored bundle 通过 `.sopify-runtime/manifest.json -> limits.decision_bridge_entry / limits.decision_bridge_hosts` 暴露 helper 与宿主桥接提示

### `~decide` 边界

`~decide` 只作为调试或覆盖入口，不是第一版主路径：

- `~decide status`：查看当前 pending decision
- `~decide choose <option_id>`：直接选定某个候选
- `~decide cancel`：放弃本轮 decision checkpoint

它不负责：

- 主动发现是否需要决策
- 取代 design 阶段的自动触发
- 让用户绕过当前 blueprint / project 契约随意落 plan

## 模板与 Policy 分层

当前已经把“router/decision 里直接拼单选 checkpoint”的做法，拆成了更稳定的两层：

### `decision_templates.py`

负责：

- 输出 host-agnostic 的 `DecisionCheckpoint`
- 复用统一字段类型、推荐项、条件显示、校验规则
- 控制模板规模，避免 checkpoint 变成任意长度的动态表单

第一版模板约束：

- 至少先实现 `strategy_pick`
- 模板字段数控制在 3 个以内
- 主字段仍然是单选 `select`
- 可通过 `custom` 选项触发 `textarea` 或补充说明字段
- 允许额外 `confirm / input` 字段表达约束，但不把 checkpoint 扩成多页流程

### `decision_policy.py`

负责：

- 决定何时触发 decision checkpoint
- 决定使用哪个模板
- 决定何时可抑制 checkpoint

第一版 policy 约束：

- 保留当前 planning-request 语义触发作为基线
- 不在第一步推翻现有 `还是 / vs / or + 架构关键词` 规则
- 逐步把触发判断从“原始文本显式分叉”迁移到“design candidate tradeoff 明显且需要用户拍板”

## 与现有 `auto_decide` 的边界

`README/AGENTS` 中已有 `auto_decide`，但该能力属于需求分析阶段的缺口补全，不应越权替代 design 阶段的决策确认。

边界应固定为：

- `auto_decide`：当需求评分不足时，是否允许 AI 代为补齐分析缺口
- `decision checkpoint`：当 design 出现长期契约分叉时，是否需要用户拍板

第一版中：

- `auto_decide` 不绕过 decision checkpoint
- 出现 decision checkpoint 时，默认必须等待用户确认
- 不新增新的配置项去关闭这条主路径

## Plan 物化契约

decision checkpoint 通过前，不生成正式 `plan/` 目录。

用户确认后，runtime 才基于所选方案物化唯一正式 plan，并在 plan 元数据中补充决策字段：

```yaml
decision_checkpoint:
  required: true
  decision_id:
  selected_option_id:
  status: confirmed
```

同时在 plan 正文中保留完整决策块，至少包括：

- 问题定义
- 候选方案摘要
- 最终选择
- 推荐理由与用户确认结果
- 被放弃方案的关键取舍

这样可以保证：

- plan 是唯一正式执行入口
- 后续 develop / history 不必回头解析聊天记录
- 决策解释在 plan 中完整可追溯

## Blueprint / History 写入边界

写入分层固定如下：

- `plan`：写完整决策上下文、用户选择、被放弃方案的关键取舍
- `history`：写摘要级结论，便于之后追溯为什么走了该方案
- `blueprint`：只在形成稳定长期结论时写入，不写原始自由输入

blueprint 的典型落点：

- `blueprint/README.md` 的关键契约与当前焦点摘要
- `blueprint/design.md` 中的宿主契约、目录契约、状态协议
- `blueprint/background.md` 中新增的长期边界或非目标

## 恢复与幂等

决策确认必须支持中断恢复：

1. 若仓库存在 `current_decision.json` 且状态为 `pending / collecting / confirmed / cancelled / timed_out`，优先恢复，而不是重新生成新决策
2. 若用户修改了核心上下文，导致原候选不再可信，则标记为 `stale`
3. `stale` 后必须重新走 design 产出新的 decision packet，不能直接沿用旧选择
4. `confirmed` 到 plan 物化之间若中断，恢复后应能幂等继续，不重复创建多个 plan

单仓库单 pending 的限制，可以避免：

- 多个决策文件互相竞争
- 多份草稿 plan 并存
- 宿主在恢复时无法判断该优先处理哪一个 checkpoint

## 读取优先级建议

给宿主与 LLM 的默认读取顺序：

1. `project.md`
2. `blueprint/README.md`
3. `wiki/overview.md`
4. 当前活动 `plan/`
5. 按需进入 `blueprint/design.md / background.md`
6. 只有在需要追溯旧方案时才查看 `history/`

这样可以形成稳定的渐进式披露：

- 先读索引
- 再读当前任务
- 最后按需追溯历史

## 下一阶段优先级

在 blueprint 层，当前状态已经前移到：

1. `13.1` structured design-stage tradeoff policy 已落地
2. `7.7` replay 摘要增强已落地
3. `13.2` model-compare 与统一 checkpoint / submission 协议的衔接评估已以 facade 方式落地

在此基础上，后续最合理的推进顺序是：

1. 扩展更多通用 template，而不改变默认入口与 handoff 契约
2. 收口 compare facade 的边界，而不是提前并入共享 state 主链路
3. 继续补宿主产品级接入，而不改变 repo 内统一 CLI bridge contract

原因是：

- `decision_templates / decision_policy / host bridge helper / CLI bridge contract tests` 已经落地
- structured tradeoff policy、CLI interactive bridge、compare facade、scope clarify bridge 与 replay 摘要已证明现有 contract 可以继续复用
- 下一步瓶颈不再是“有没有桥”，而是“哪些场景该触发、compare facade 如何继续收口、各宿主产品如何消费现有 bridge contract”

## 近期切片：当前时间显示与 `~summary`

在 replay 能力上，当前主线不再继续扩张为“按天索引 + 多入口回放”。

近期切片收敛为两个直接面向用户的能力：

1. 每次进入技能包执行时，在输出中显示“当前本地时间”
2. 提供 `~summary`，默认总结“今天、当前 CLI 根目录（当前工作区）”内的思考链路与代码变更细节

### 用户显示口径

用户侧展示不强调工程字段名，不展示 `package_timestamp / activated_at` 这类内部术语。

用户看到的最小口径应为：

- `时间: 2026-03-19 21:21:41`

设计原则：

- 用户看到的是“现在几点”，而不是内部阶段字段
- 时间不应抢占正文主信息，也不应重复阶段标题
- 结构化内部字段继续保留给摘要生成使用

普通阶段输出示例建议：

```text
[sopify-skills-ai] 方案设计 ✓

方案: .sopify-skills/plan/20260319_task-168cb6
焦点: 当前时间显示 + ~summary 今日详细摘要

---
Changes: 3 files

Next: 继续评审方案或确认进入实现
时间: 2026-03-19 21:21:41
```

说明：

- 不展示 `技能: design`，因为标题里的“方案设计”已经表达当前阶段
- 不重复输出“已进入方案设计阶段”这类摘要句
- 时间作为尾注存在，提醒当前时间点即可

### 当前实现状态（2026-03-20）

- runtime 已补齐 `SkillActivation` 结构化事实，并在普通输出尾部统一展示 `时间: YYYY-MM-DD HH:MM:SS`
- replay `events.jsonl` 已写入 `metadata.activation`，包含 `skill_id / activated_at / activated_local_day / run_id / route_name`
- `~summary` 已作为显式命令接入 runtime，默认生成“今天、当前工作区”的详细摘要
- `~summary` 当前按“确定性收集 -> 写入 `summary.json` -> 渲染 `summary.md`”执行
- `~summary` 默认纳入未提交改动，并保持 read-only，不覆盖当前 active handoff
- 已补 `~summary` 首版 4 条硬化测试：同日重复运行 `revision` 递增、`git` 缺失 fallback、`current_run / last_route` 不污染、终端渲染与落盘产物一致
- 摘要产物当前写入 `.sopify-skills/replay/daily/YYYY-MM/YYYY-MM-DD/`

### `~summary` 的定位

`~summary` 是当前阶段唯一优先的 retrieval 入口。

默认行为：

- 默认作用域是“今天、当前工作区”
- 默认输出是“详细摘要”，而不是轻量目录页
- 目标是让用户可以直接复盘、学习、抽取可复用经验
- 预期使用频率通常是每天 1-2 次，因此首版更适合现算现出，而不是先维护中间索引

`~summary` 输出示例建议：

```text
[sopify-skills-ai] 今日详细摘要 ✓

范围: 2026-03-19 · 当前工作区
生成于: 2026-03-19T21:21:41+08:00
工作区: /Users/weixin.li/Desktop/vs-code-extension/sopify-skills
说明: 默认已纳入未提交改动；replay 仅作为增强输入。

## 今日概览
今天围绕当前方案推进了 4 项代码或文档变更，并同步沉淀到可复盘摘要。

---
Changes: 2 files
  - .sopify-skills/replay/daily/2026-03/2026-03-19/summary.json
  - .sopify-skills/replay/daily/2026-03/2026-03-19/summary.md

Next: 可再次运行 ~summary 刷新，或继续当前开发流
时间: 2026-03-19 21:21:41
```

### `~summary` 数据契约

`~summary` 不应直接依赖聊天记忆，也不应强依赖 replay，因为当前 replay events 使用率还不高。

推荐输入优先级：

1. 当天 `plan / handoff / state / decision / clarification` 的结构化事实
2. 当天 Git 事实：文件改动、diff 摘要、提交记录
3. 当天 replay session，作为可选增强输入

也就是说：

- replay 缺失时，`~summary` 仍然可生成
- replay 存在时，用它补时间线与解释细节

推荐 `summary.json` schema：

```json
{
  "schema_version": "1",
  "summary_key": "2026-03-19::/Users/weixin.li/Desktop/vs-code-extension/sopify-skills",
  "scope": {
    "local_day": "2026-03-19",
    "workspace_root": "/Users/weixin.li/Desktop/vs-code-extension/sopify-skills",
    "workspace_label": "当前工作区",
    "timezone": "Asia/Shanghai"
  },
  "revision": 2,
  "generated_at": "2026-03-19T21:21:41+08:00",
  "source_window": {
    "from": "2026-03-19T00:00:00+08:00",
    "to": "2026-03-19T21:21:41+08:00"
  },
  "source_refs": {
    "plan_files": [
      {
        "path": ".sopify-skills/plan/20260319_task-168cb6/design.md",
        "kind": "plan",
        "updated_at": "2026-03-19T20:58:00+08:00"
      }
    ],
    "state_files": [
      {
        "path": ".sopify-skills/state/current_plan.json",
        "kind": "state",
        "updated_at": "2026-03-19T21:10:00+08:00"
      }
    ],
    "handoff_files": [
      {
        "path": ".sopify-skills/state/current_handoff.json",
        "kind": "handoff",
        "updated_at": "2026-03-19T21:10:00+08:00"
      }
    ],
    "git_refs": {
      "base_ref": "HEAD",
      "changed_files": [
        ".sopify-skills/plan/20260319_task-168cb6/design.md"
      ],
      "commits": [
        {
          "sha": "abc1234",
          "title": "Refine summary contract",
          "authored_at": "2026-03-19T20:45:00+08:00"
        }
      ]
    },
    "replay_sessions": [
      {
        "run_id": "20260319T132141_14a099",
        "path": ".sopify-skills/replay/sessions/20260319T132141_14a099",
        "used_for": "timeline"
      }
    ]
  },
  "facts": {
    "headline": "今天完成了当前时间显示与 ~summary 主线收敛。",
    "goals": [
      {
        "id": "goal-1",
        "summary": "收窄当前切片，优先满足可复盘摘要需求。",
        "evidence_refs": [
          "plan_files[0]"
        ]
      }
    ],
    "decisions": [
      {
        "id": "decision-1",
        "summary": "本期不先做 daily index。",
        "reason": "~summary 一天通常只运行 1-2 次，现算现出更轻。",
        "status": "confirmed",
        "evidence_refs": [
          "plan_files[0]",
          "handoff_files[0]"
        ]
      }
    ],
    "code_changes": [
      {
        "path": ".sopify-skills/plan/20260319_task-168cb6/design.md",
        "change_type": "modified",
        "summary": "把 ~summary 数据契约收敛到可编码 schema。",
        "reason": "让后续实现不依赖聊天回忆。",
        "verification": "not_run",
        "evidence_refs": [
          "git_refs.changed_files[0]"
        ]
      }
    ],
    "issues": [
      {
        "id": "issue-1",
        "summary": "replay events 当前使用率不高。",
        "status": "open",
        "resolution": "",
        "evidence_refs": [
          "replay_sessions[0]"
        ]
      }
    ],
    "lessons": [
      {
        "id": "lesson-1",
        "summary": "摘要应优先绑定机器事实源，而不是自由聊天文本。",
        "reusable_pattern": "先确定性收集，再模板渲染。",
        "evidence_refs": [
          "state_files[0]",
          "handoff_files[0]"
        ]
      }
    ],
    "next_steps": [
      {
        "id": "next-1",
        "summary": "把 summary schema 映射到实际运行时实现。",
        "priority": "medium",
        "evidence_refs": [
          "plan_files[0]"
        ]
      }
    ]
  },
  "quality_checks": {
    "replay_optional": true,
    "summary_runs_per_day": "1-2",
    "required_sections_present": true,
    "missing_inputs": [],
    "fallback_used": []
  }
}
```

约束建议：

- `summary_key = local_day + "::" + workspace_root`
- 每个 `local_day + workspace_root` 只维护一份 canonical `summary.json`
- 同日再次运行 `~summary` 时，刷新同一份文件并递增 `revision`
- `summary.md` 只作为渲染产物，不作为机器事实源

### `~summary` 的稳定性策略

为了保证链路稳定，建议采用两段式生成：

1. 先做确定性收集，生成 `summary.json`
2. 再按固定模板渲染 `summary.md`

这意味着：

- 先抽取事实，再做表达
- 用户摘要与机器输入共用同一份事实基座
- 当摘要不符合预期时，可以直接回看 `summary.json`，而不是重新猜测

### 新增信息的落盘要求

为了让后续摘要稳定，新增信息优先写入结构化状态，而不是只留在聊天文本里。

推荐优先写入：

1. `plan / state / handoff` 中的关键节点事实
2. 代码改动事实与验证结果
3. replay 事件中的阶段时间、动作、原因摘要

首版输出栏目：

- 今日目标与上下文
- 关键决策与原因
- 代码变更详解
- 问题与风险
- 可复用经验
- 未完成事项与下一步

后续扩展栏目：

- 执行时间线
- 更细粒度验证结果
- 更强的知识复盘结构

### `daily index` 的降级定位

`daily index` 当前不再作为用户主能力。

降级后的定位是：

- 未来如需提速、稳定按天检索、或支持模型批量读取时，再引入轻量索引
- 在当前阶段，不要求先有 `daily index` 才能生成 `~summary`
- `~summary` 一天通常只运行 1-2 次，当前频率不足以支撑先做 `daily index` 的收益
- “本项目”在 monorepo 或子目录场景下语义不稳定，当前应以 `workspace_root` 作为唯一机器作用域

这意味着当前切片可以先采用：

- 直接扫描“今天”的结构化状态与代码改动
- 现场生成 digest
- 按需落盘摘要产物

### 后续延展

以下能力保留到后续，而不进入当前主线：

- `daily index`
- `~replay`
- 按指定日期读取的多入口检索
- 更重的日级导航页或统计页
- 摘要质量优化
- 验证结果摄取
- 基于 replay activation 的时间线增强

## 宿主偏好预载入（`preferences-preload-v1`）

### 定位

`preferences-preload-v1` 是宿主 preflight 的窄能力，不是 runtime 主链路的新阶段。

职责边界：

- 宿主负责在每次 Sopify 调用前尝试读取 `preferences.md`
- runtime 继续负责路由、状态、handoff 与 plan 生命周期
- `preferences.md` 代表 workspace-scope 的长期协作规则，不属于 active-flow recovery state

### 路径解析规则

宿主必须先按与 runtime 一致的配置优先级解析 `plan.directory`：

1. 项目根 `sopify.config.yaml`
2. 全局 `~/.codex/sopify.config.yaml`
3. 默认值 `.sopify-skills`

然后再计算：

```text
preferences_path = workspace_root / plan.directory / "user/preferences.md"
```

设计要求：

- 不允许宿主硬编码 `.sopify-skills/user/preferences.md`
- 不允许跳过 `plan.directory` 解析直接猜路径
- 解析失败时可降级到默认目录，但必须对宿主可见

### 载入时机

宿主在以下时机必须尝试读取：

- 每次原始用户请求准备进入 Sopify router 之前
- 每次需要恢复 Sopify 主链路之前
- 每次准备再次发起新的 Sopify LLM 回合之前

当前范围外：

- 纯 helper / bridge 的无 LLM 机器调用
- 与 Sopify 无关的普通宿主功能

### 失败策略

首版采用 `fail-open with visibility`：

- `loaded`: 文件存在且成功读取，注入 LLM
- `missing`: 文件不存在，继续主链路
- `invalid`: 文件存在但格式或编码异常，继续主链路
- `read_error`: 文件存在但读取失败，继续主链路

这里的关键约束是：

- `preferences` 不是门禁，不得像 checkpoint 一样 fail-closed
- 但宿主必须知道本轮是否成功载入，不能静默吞掉状态

### 注入格式

首版不做复杂解析，直接注入原文，并包一层稳定前缀：

```text
[Long-Term User Preferences]
Scope: current workspace
Priority: current task explicit request > this preferences file > default rules

Apply these as durable collaboration rules for this Sopify run.
If a rule conflicts with the current explicit task, follow the current task.

<raw preferences.md content>
```

设计要求：

- 首版不做自动归纳、自动提炼、标签分类
- 首版不做字段级结构化映射
- 先保证“稳定读到并注入”，再考虑更聪明的消费

### 优先级

固定优先级：

1. 当前任务明确要求
2. `preferences.md`
3. 默认规则

这意味着：

- 当前任务可以覆盖长期偏好
- 长期偏好可以稳定覆盖默认协作风格
- 不允许把 `preferences.md` 提升为强于当前任务的硬约束

### 为什么不进入 `RecoveredContext`

当前不建议把 `preferences.md` 塞进 `RecoveredContext`，原因是：

- `RecoveredContext` 的语义是 active-flow recovery
- `preferences.md` 的语义是 workspace-scope durable rules
- 二者层级不同，合并会降低状态模型清晰度

如果后续需要提高可观测性，更合理的方向是：

- runtime 独立暴露 `preferences_artifact`
- 宿主把它视为辅助事实，而不是 session 恢复态

### 后续延展

稳定版之后再评估：

- runtime 独立 `preferences_artifact`
- 轻量结构化解析
- 偏好分类、自动归纳、自动提炼

这些能力全部依赖首版“宿主稳定预载入”已经成立，不应反向抢占当前切片。
