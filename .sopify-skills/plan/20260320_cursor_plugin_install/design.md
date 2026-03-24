# 技术设计: Cursor 插件式安装 Sopify（`cursor-plugin-install`）

## 设计目标

在不改变现有 `codex/claude` 安装器与 runtime 控制面边界的前提下，为 Cursor 新增一条独立的插件式接入方案：

1. 通过 Cursor 插件完成 Sopify 安装
2. 插件内交付 `rules + hooks + skills`
3. 插件继续复用 Sopify 现有 runtime bundle / helper contract
4. v1 限定为 Cursor IDE 主链，不承诺 CLI parity

## 总体设计

### 0. 产品入口

Cursor 的正式入口不再是：

```bash
python3 scripts/export_cursor.py export --workspace <path>
```

而是：

1. 在 Cursor IDE 中安装 Sopify 插件
2. 插件加载 Sopify 的 rules / hooks / skills
3. 用户在 Cursor 内直接触发 Sopify 能力

说明：

- `workspace export` 可作为开发/调试 fallback 保留，但不再是正式主线
- `~/.cursor/skills` 不再作为正式安装落点

### 1. 分层架构

推荐分成三层：

#### A. shared Sopify runtime source of truth

继续保留当前仓库内已有的共享控制面：

- runtime entries
- vendored bundle schema
- preferences preload helper
- handoff / checkpoint contract
- workspace bootstrap helper

这一层仍然是所有宿主共享的唯一来源。

#### B. Cursor plugin package

新增 Cursor 插件源码与打包层，建议目录：

```text
integrations/
└── cursor-plugin/
    ├── plugin/
    ├── assets/
    ├── build/
    ├── rules/
    ├── hooks/
    ├── skills/
    └── scripts/
```

职责：

1. 组织 Cursor 插件所需目录结构
2. 打包 Sopify 的 rules / hooks / skills
3. 把共享 runtime bundle / helpers 以插件可消费的方式带入
4. 生成可安装的插件产物

#### C. Cursor host adapter

Cursor 不是现有 installer 的第三个 target，而是插件内的宿主适配层。

职责：

1. 把 Cursor 的 hook 事件映射到 Sopify turn ingress
2. 管理 Cursor rules / skills 的最小投放
3. 对接 Cursor 插件内 doctor / smoke

## 为什么 Cursor 不并入现有安装器主链

当前 `install-sopify.sh -> install_sopify.py` 的职责是：

1. 外部安装器分发
2. host prompt install
3. payload install
4. optional workspace bootstrap

Cursor 插件的职责则是：

1. 宿主内插件分发
2. 插件内交付 rules / hooks / skills
3. 在 IDE 生命周期内参与 agent loop

两者生命周期不同，因此本设计明确：

- `codex/claude` 继续走安装器主链
- Cursor 走独立插件分发线
- 两者共享 runtime 源，但不共享安装入口

## Cursor 插件内的交付内容

### 1. Rules

插件只投放薄的 always-on rules，负责：

1. 声明 Sopify 是默认 workflow shell
2. 要求 runtime-first / handoff-first / checkpoint-first
3. 约束长期偏好与当前任务指令的优先级

Rules 不负责承载整套长文案技能，只保留必须始终在场的宿主契约。

### 2. Hooks

v1 最小 hooks 集建议为：

1. `beforeSubmitPrompt`
2. `stop`

职责：

#### `beforeSubmitPrompt`

在用户 prompt 真正提交给 Cursor agent 前，先执行：

1. workspace preflight / bootstrap
2. preferences preload
3. default runtime dispatch
4. handoff-first continuation

#### `stop`

在 runtime 仍处于以下 pending 状态时执行 fail-closed：

1. `clarification_pending`
2. `decision_pending`
3. `execution_confirm_pending`

本轮不进入默认值的扩展 hooks：

1. `beforeShellCommand`
2. `afterShellCommand`
3. 更细粒度工具审计 hooks

### 3. Skills

插件内的 skills 应复用 Sopify 的阶段能力，但做 Cursor 适配包装。

建议最小集合：

1. `analyze`
2. `design`
3. `develop`
4. `workflow-learning`
5. `model-compare`

设计要求：

1. skills 不重复定义 runtime 契约
2. skills 只承载流程知识与输出结构
3. 宿主入口控制仍由 hooks 负责

### 4. Commands

Cursor 官方公开材料中，插件侧对 commands 的具体打包方式需要以官方 scaffold 为准。

因此 v1 设计要求为：

1. 若官方插件 schema 明确支持 commands，则提供：
   - `/sopify-go`
   - `/sopify-plan`
   - `/sopify-compare`
   - `/sopify-doctor`
2. 若 commands 不属于插件稳定打包面，则不自造并行目录结构，改由 rules / skills 引导主链路

### 5. 可选扩展（不进 v1）

后续可选能力：

1. `subagents`
2. `MCP servers`
3. 插件面板 / 更丰富的 UI 集成

## 运行时接法

Cursor 插件本质上是 `cursor_hooks` adapter，而不是 `codex launcher` 或 `claude hooks` 的直接复用实现。

### 1. 运行顺序

用户在 Cursor IDE 发起请求后，链路固定为：

```text
Cursor prompt
  -> beforeSubmitPrompt hook
  -> Sopify preflight / bootstrap
  -> Sopify preferences preload
  -> Sopify default runtime dispatch
  -> Sopify handoff-first continuation
  -> Cursor agent normal continuation
```

### 2. bootstrap 来源

插件不依赖 `~/.cursor/skills` 或外部全局安装器。

推荐方案：

1. 插件内自带 Sopify bundle / helper 资产
2. hook handler 从插件打包产物内解析这些资产
3. 若项目缺少 `.sopify-runtime/`，则由插件内 helper 为工作区 bootstrap vendored bundle

### 3. shared source of truth

虽然插件是独立分发线，但其 bundle / helper 必须来自现有 Sopify 统一来源，而不是手工复制：

1. 共享 manifest schema
2. 共享 bootstrap helper
3. 共享 preferences preload helper
4. 共享 runtime entry contract

这要求新增插件打包脚本，把共享资产收集到 Cursor 插件产物里。

## 插件打包策略

### 1. 官方 scaffold 优先

由于当前公开文档对插件内部 schema 细节展示有限，v1 明确要求：

1. 以 Cursor 官方 Create Plugin / 官方 scaffold 为唯一打包结构依据
2. 不把“猜测的插件 manifest 结构”写成 Sopify 长期契约
3. Sopify 侧只维护内容源与打包适配逻辑

### 2. 构建入口

建议新增构建入口：

```text
scripts/build_cursor_plugin.py
```

职责：

1. 从共享 runtime / skills / rules / hooks 源生成插件工作目录
2. 校验插件包含的 bundle / helper 版本与仓库版本一致
3. 产出 Cursor 可安装插件包或插件源码目录

### 3. 分发方式

v1 推荐先走：

1. 私有插件
2. 团队内分发
3. `Create Plugin` / `Add Plugin` 可安装形态

暂不在本轮冻结：

1. 公共 marketplace 上架流程
2. 对外发布节奏

## 兼容性原则

本轮必须满足以下兼容性约束：

1. 不修改 `SUPPORTED_HOSTS = {"codex", "claude"}`
2. 不把 Cursor 插件塞回 `install-sopify.sh`
3. 不改变既有 runtime manifest / handoff / checkpoint schema
4. 不要求安装 `codex` 或 `claude` payload 才能使用 Cursor 插件

## doctor / smoke 设计

### 1. repo-side package doctor

建议新增：

```text
python3 scripts/check_cursor_plugin_package.py
```

职责：

1. 插件产物是否完整
2. hooks / rules / skills 是否齐全
3. 插件内 bundle / helper 版本是否与仓库一致
4. 是否包含 v1 约定的最小 bridge 能力

### 2. plugin-side doctor

建议提供 `/sopify-doctor` 或等价入口，在 Cursor IDE 内输出：

1. 插件版本
2. bundle 版本
3. hooks 注册状态
4. 当前 workspace 的 `.sopify-runtime/` 状态
5. preload / handoff / checkpoint helper 解析结果

### 3. smoke contract

最小 smoke 覆盖：

1. 通过 `beforeSubmitPrompt` 触发 preflight -> preload -> runtime dispatch
2. runtime 产出 handoff 后，优先消费 handoff，而不是只依赖文案输出
3. clarification / decision / execution confirm 三类 checkpoint 在 pending 时 fail-closed
4. smoke 只承诺 Cursor IDE 内行为，不以 CLI 结果作为 v1 通过标准

## rollout 策略

### Phase 1

- 新增 Cursor 插件源码目录与打包脚本骨架
- 明确插件产物与共享 runtime 源之间的映射
- 不动现有 `codex/claude` 主链

### Phase 2

- 接通最小 hooks 集
- 接通插件内 rules / skills
- 完成 workspace bootstrap 与 runtime dispatch

### Phase 3

- 增加 repo-side doctor / plugin-side doctor / smoke
- 完成团队内分发与安装文档

### Phase 4

- 评估 Cursor CLI parity
- 评估更丰富 hooks / MCP / subagents
- 再决定是否公开发布 marketplace 版本

## 设计结论

Cursor 如果正式支持 Sopify，正确路径不是继续强化 `workspace export`，而是新增一条独立的插件分发与宿主接入线。

实现结论如下：

1. Cursor 走插件式安装
2. v1 只承诺 IDE-first
3. 插件内最小交付为 `rules + hooks + skills`
4. hooks 承担真正的 runtime ingress
5. 插件继续复用 Sopify 现有 runtime 控制面
6. `codex/claude` 安装器主链保持不变
