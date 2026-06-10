# 技术设计: 从 HelloAGENTS / Superpowers 对比收口 Sopify 的学习路径与实施顺序

## 技术方案

- 核心目标:
  - 用一份 steering plan 把“学什么”和“怎么做”从对比结论落成可执行顺序；
  - 把下一轮重心从 control plane 调整到 execution plane；
  - 保留 Sopify 已有的 runtime 机器契约与 plan 生命周期优势。
- 实现要点:
  - 学习“用户收益”和“执行纪律”，而不是照搬其他项目的实现形式；
  - 区分“学习优先级”和“实施顺序”；
  - 把 composite 方向拆成独立、可验证、可交付的 follow-up plan。

## 设计原则

### 1. 先保住 Sopify 的差异化资产

本轮不应动摇以下基础：

1. `manifest-first`
2. `handoff-first`
3. `checkpoint_request`
4. `execution_gate`
5. `plan lifecycle`

因此所有借鉴都必须满足：

1. 不把核心决策退回 prompt-only 约定；
2. 不用 hooks 或子智能体编排替代现有 runtime contract；
3. 不为追求“看起来更强”牺牲可审计、可恢复和可测试性。

### 2. 学习优先级按“对写代码能力的提升”排序

本轮判断的学习优先级如下：

1. `Superpowers`：两阶段复审纪律
   - 学的是 `implement -> spec review -> code quality review` 的执行纪律；
   - 不需要先做完整 subagent 平台，也不需要复制 worktree 工作流。
2. `HelloAGENTS`：开发态验证循环与用户可观测性
   - 学的是验证命令发现、失败重试、break-loop 根因分类、`status/doctor` 这类只读诊断命令；
   - 不需要先做 6 宿主覆盖。
3. `HelloAGENTS`：渐进式降级
   - 学的是能力检测后受限放行，而不是一票否决；
   - 只允许用于非关键 evidence 缺失。
4. `HelloAGENTS`：分发即产品
   - 学的是一键安装和渠道包装；
   - 这是放大器，不是当前最关键的产品内核。

#### 2.1 借鉴边界：学原则，不学机制

对 `Superpowers` 的借鉴必须先翻译成 Sopify-native 分层，而不是直接复制其文本纪律或调度结构：

1. 先落到机器契约层
   - 把“有验证证据才算完成”“失败路径必须给出根因”这类原则，翻译为 develop loop 的结构化字段与完成条件
2. 再补规则镜像层
   - 用简短规则说明解释 contract 存在的原因，辅助约束高频逃逸路径
   - 文本镜像不是主 enforcement，不替代 runtime contract
3. 最后预留升级路径层
   - 当独立 reviewer 或 code review agent 可用时，再升级执行方式
   - 不提前复制其 dispatch 模板、状态机或 prompt-first 编排

因此本轮明确不照搬以下机制：

1. 文本 Iron Laws 作为主控制层
2. 反模式列表作为主 enforcement 机制
3. 完整 Task Status 四态协议
4. `Superpowers` 的 subagent-first dispatch 模板与状态机

### 3. 实施顺序不等于学习顺序

从“先做什么最稳”角度，实施顺序建议为：

1. 收窄并完成 `helloagents-integration-enhancements`
   - 只保留 `registry + status/doctor + README matrix`
   - 作用是先把支持现状、bundle 健康度、workspace 状态变得可见
2. 新建并推进 `develop-quality-loop`
   - 这是最重要的用户价值项，但需要单独成 plan 才能做扎实
3. 新建 `runtime-gate-degradation-mode`
   - 在已有 `doctor` 和质量闭环之后，再把 gate 从 all-or-nothing 调到 fail-soft
4. 新建 `one-liner-distribution`
   - 在产品内核可观测、可验证之后，再做安装与分发放大

补充说明：

1. planning order 可以先于 implementation order；
2. 因此允许先规划 `develop-quality-loop`，但先实施收窄后的 `helloagents-integration-enhancements`；
3. steering plan 的职责是把这两层顺序写清楚，而不是把二者混成一个线性执行队列。

## 路线设计

### A. 当前阶段应做什么

#### A.1 收窄现有 HelloAGENTS 借鉴项

当前最适合先落地的不是多宿主，也不是完整命令面，而是：

1. host capability registry
2. `sopify status`
3. `sopify doctor`
4. README 宿主矩阵

原因：

1. 范围窄；
2. 能快速把“支持什么、哪里坏了、下一步该怎么修”暴露给用户；
3. 能为后续分发和降级提供事实底座。

#### A.2 停止继续给 plan 元系统加码

当前 visible active plan 已经显示出 control plane 比 execution plane 更活跃。下一轮不应优先继续投入：

1. plan history / index 扩张
2. 额外的 README / changelog 元治理
3. 尚未有用户价值牵引的多宿主 scaffold

### B. 下一条最值得做的实现线

#### B.1 `develop-quality-loop`

这是让 Sopify 更像“帮用户写代码的工具”的关键实现线。建议最小闭环包含：

1. 验证命令发现顺序
   - `.sopify-skills/project.md` 的 verify section
   - 项目脚本（如 `package.json` / `pyproject.toml` / `Makefile`）
   - 都不存在时允许显式降级
2. 每个 task 完成后执行验证
3. 失败自动重试一次，并带错误上下文
4. 连续失败后做简化版根因分类
   - 逻辑错误
   - 环境 / 依赖问题
   - 测试基建缺失
   - 设计 / 范围错误
5. 两阶段复审
   - spec compliance
   - code quality

最重要的边界：

1. 不要求先有复杂子智能体编排；
2. 单代理顺序执行也可以先落地；
3. 重点是“默认会验证、默认会复审、默认会暴露失败原因”。

#### B.2 成功标准

`develop-quality-loop` 的完成不应只看代码是否跑通，还应看：

1. 每个 task 是否有验证结果
2. review 是否拦住 overbuild / underbuild
3. 失败是否产出结构化原因
4. handoff / replay 是否能看到验证与 review 结果

### C. 后续线

#### C.1 `runtime-gate-degradation-mode`

在保持主契约不变的前提下，仅新增受限降级：

1. 明确哪些 evidence 缺失可以 degraded
2. degraded 只开放受限 `allowed_response_mode`
3. 宿主必须向用户显式展示 degraded 状态

#### C.2 `one-liner-distribution`

仅在前两条线稳定后推进：

1. 包入口（`pyproject.toml` / CLI entry）
2. `install.sh` / `install.ps1`
3. 安装后自动调用既有 bootstrap 与 doctor

## 明确不做

本轮不建议优先做：

1. 原生子智能体编排平台
2. 多宿主 scaffold 扩张
3. 低门槛 skill 注册
4. 继续加深 plan lifecycle 元系统

## 交付形式

本 plan 的直接交付不是代码功能，而是：

1. 当前活跃 plan 的重新排序与范围收口
2. 下一批实现 plan 的优先级
3. 每条实现线的目标、边界与验收方式
4. planning order 与 implementation order 的明确区分

因此本 plan 结束后的正确动作不是直接 `~go exec`，而是：

1. 先评审本路线；
2. 选定要先开的窄实现 plan；
3. 再进入对应实现 plan 的 `~go plan` / `~go`。
