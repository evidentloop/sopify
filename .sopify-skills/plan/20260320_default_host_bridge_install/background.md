# 变更提案: 默认启用宿主桥接的一键安装（`default-host-bridge-install`）

## 需求背景

当前 Sopify 对 `codex` / `claude` 的安装已经覆盖了三件事：

1. 安装宿主提示层（`AGENTS.md` / `CLAUDE.md` 与技能目录）
2. 安装宿主本地 payload
3. 在项目触发时按需 bootstrap `.sopify-runtime/`

但它还没有把“每轮用户原始输入稳定先进入 Sopify runtime”做成宿主侧硬行为。

这带来几个长期问题：

1. 宿主 prompt 虽然要求“必须先走 runtime”，但当前更多是强提示，不是强入口
2. `preferences preload / manifest-first / handoff-first` 已经有完整机器契约，但宿主并没有统一 turn-level ingress 去稳定消费
3. 现有 smoke 主要验证“安装产物完整”，不验证“宿主每轮真的先走 Sopify runtime”
4. 若继续把 bridge 做成可选参数，用户会天然落回旧模式，长期形成两套接入口径

因此，本轮不再把 host bridge 视为“增强项”，而是把它提升为新的默认安装语义。

## 宿主现实差异

本轮必须承认 `claude` 与 `codex` 的宿主能力并不对称：

1. `claude` 有官方 hooks，且粒度足够细，可在 `UserPromptSubmit` 与 `Stop` 等阶段稳定拦截
2. `codex` 当前公开的稳定深接入口更接近 `App Server / SDK`，而不是 Claude-style hooks
3. 因此，bridge 不能再抽象成“所有宿主都优先 hook、失败再 supervisor”这一条统一路径

本轮已经冻结的宿主策略为：

1. `claude v1 = minimal hooks bridge`
2. `codex v1 = launcher bridge`
3. `codex app-server bridge` 作为后续演进方向，不进入本轮默认安装主链

## 目标

### 1. 保持用户入口不变

- 用户仍通过单条安装命令完成接入
- 不新增 `--bridge` 参数
- `codex` / `claude` 仍保持原有 target 形态：`<host>:<lang>`

### 2. 默认安装 turn-level host bridge

- 新安装默认包含 host bridge
- bridge 负责 turn-level preflight / preferences preload / runtime dispatch / handoff loop
- 用户不需要再理解“bridge 是否开启”

### 3. 不污染现有 installer core

- 现有 `prompt + payload + workspace bootstrap` installer core 继续保持职责单一
- bridge 作为独立模块实现，由新的顶层安装入口编排
- 不把 bridge 逻辑硬塞进当前 `installer/*` 主抽象

### 4. 保持既有运行时机器契约不变

- 继续优先消费 `.sopify-runtime/manifest.json`
- 继续使用既有 default entry / plan-only entry / preferences preload / handoff / checkpoint 契约
- 不重新发明第二套 bridge 协议

### 5. 控制后续维护成本

- 只做一套共享 bridge core
- 只把宿主差异隔离在薄 adapter
- 不为 `codex` / `claude` 各自复制整套 runtime / checkpoint / doctor 逻辑

## 非目标

本轮明确不做以下内容：

- 不引入 `cursor` host 的正式一键安装主链
- 不再提供 `--bridge on/off/auto` 之类面向用户的安装参数
- 不改写 runtime 的既有 route / handoff / checkpoint schema
- 不把 `codex` / `claude` 从 `SUPPORTED_HOSTS` 中扩展为新的桥接 host 类型
- 不在本轮实现 `codex app-server bridge`
- 不在本轮把 `claude` 的所有 hooks 事件都接满；仅冻结最小 hooks 集

## 核心问题拆解

### 1. 一键安装的语义要怎么变化

旧语义：

- 安装宿主提示层
- 安装 payload
- 可选预热 workspace

新语义：

- 安装宿主提示层
- 安装 payload
- 安装默认 host bridge
- 可选预热 workspace

用户入口仍是一条命令，但安装结果不再只是“产物完整”，而是“宿主每轮接入能力已部署”。

### 2. 为什么不保留 `--bridge` 参数

本期不建议把 bridge 暴露成用户级参数，原因有三点：

1. 之前本来就没有桥接，bridge 不是“兼容旧能力的可选插件”，而是这次要补上的缺失基础设施
2. 暴露参数会把同一产品拆成“桥接版”和“非桥接版”，长期造成排障与文档分叉
3. 宿主是否走什么接法，应由宿主适配层和 doctor 判断，而不是让用户理解实现细节

### 3. bridge 应放在什么层

本轮把 bridge 明确为“安装器外的独立模块，由顶层安装入口编排”，原因如下：

1. installer core 是一次性 setup 逻辑
2. host bridge 是会话期 turn-level ingress 逻辑
3. 两者生命周期不同，混在一个抽象里会让 `installer/*` 失去边界

因此，推荐形态是：

- 旧 installer core 继续保留
- 新 façade 安装入口默认串起 `core install + bridge deploy + bridge doctor`

### 4. 默认桥接模式如何决定

用户不再传参。

bridge 部署适配器内部按宿主能力决定：

1. `claude` 直接部署最小 hooks 集，v1 固定为 `UserPromptSubmit + Stop`
2. `codex` 不再假设存在隐藏 hooks，v1 固定部署 `launcher bridge`
3. `codex app-server bridge` 仅保留在后续演进路线，不进入本轮默认值

这属于宿主适配细节，不进入用户命令面。

### 5. 兼容性怎么保证

需要明确四条兼容性底线：

1. 不改 `SUPPORTED_HOSTS = {"codex", "claude"}`
2. 不修改现有 `InstallResult` 所代表的 core install 语义
3. 不修改 runtime manifest / handoff / checkpoint 的既有 contract
4. 共享 core 必须统一消费契约，宿主差异只体现在接入层

bridge 的新增能力应以“扩展组合结果”的方式暴露，而不是让旧 core install 失真。

## 成功标准

满足以下条件即可认为本期目标成立：

1. 用户仍使用单条安装命令完成 `codex` / `claude` 接入
2. 安装后默认具备 turn-level host bridge 能力，不需要用户再显式开启 bridge
3. bridge 实现不侵入当前 `installer/*` core 抽象
4. runtime 继续通过既有 manifest-first / preload / handoff-first 契约运行
5. `claude` 与 `codex` 共用一套 bridge core，但各自保留薄 adapter
6. doctor / smoke 能区分“产物已安装”与“宿主 turn-level 入口已接管”

## 风险评估

### 风险 1

如果直接把 bridge 强行并入当前 installer core，会把“安装期”和“会话期”职责混层。

缓解：

- 保留旧 core install API
- 用 façade 编排 bridge deploy 与 doctor

### 风险 2

如果继续把 bridge 做成用户参数，默认路径会持续有人停留在非桥接模式。

缓解：

- 不暴露 `--bridge`
- 统一把 bridge 作为新的默认安装语义

### 风险 3

如果继续把 `codex` 写成 Claude-style hook 宿主，会导致设计与现实能力错位。

缓解：

- `claude` 与 `codex` 在设计文档中明确分宿主接法
- `codex v1` 固定为 `launcher bridge`
- `claude v1` 固定为 `minimal hooks bridge`

### 风险 4

如果 smoke 仍只验证旧安装链，bridge 失效时会被长期漏检。

缓解：

- 保留旧 smoke 作为 core install smoke
- 新增 bridge doctor / smoke，显式覆盖 per-turn ingress 链路

### 风险 5

如果把宿主差异做成两套完整实现，后续维护成本会持续走高。

缓解：

- 共享 preflight / preload / dispatch / handoff / checkpoint core
- 宿主层仅负责“如何拦截 turn”和“如何做 doctor / smoke 适配”

## 规划结论

`default-host-bridge-install` 的正确方向不是给用户加更多参数，而是把“默认安装后宿主稳定先走 Sopify runtime”收口成新的默认产品语义。

因此，本轮方案结论为：

1. 用户入口继续保持单条安装命令
2. 不暴露 `--bridge`
3. host bridge 默认安装
4. bridge 实现保持在 installer core 之外
5. 采用“一套共享 core + 两个薄 adapter”
6. `claude v1` 使用最小 hooks 集
7. `codex v1` 使用 launcher bridge
8. 通过 façade、doctor 与 smoke 保证新默认行为可观察、可验证、可回滚
