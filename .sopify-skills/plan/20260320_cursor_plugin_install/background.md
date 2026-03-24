# 变更提案: Cursor 插件式安装 Sopify（`cursor-plugin-install`）

## 需求背景

当前 Sopify 的正式宿主接入仍以 `codex` / `claude` 的一键安装链为主：

1. 安装宿主提示层
2. 安装宿主本地 payload
3. 在项目触发时按需 bootstrap `.sopify-runtime/`

但对 Cursor，用户希望的不是：

1. 导出到项目 `.cursor/*` 目录作为主要安装方式
2. 写入 `~/.cursor/skills`
3. 复用现有 `codex/claude` 安装器主链

而是直接采用 Cursor 官方支持的插件式安装。

## Cursor 侧现实约束

截至本轮调研，Cursor 已经具备把以下能力打包成插件的官方方向：

1. `rules`
2. `hooks`
3. `skills`
4. `subagents`
5. `MCP servers`

这意味着 Sopify 在 Cursor 上可以走“单次插件安装，统一交付规则、钩子、技能与桥接逻辑”的产品路径，而不必再把 `workspace export` 当成主安装形态。

同时，本轮也需要承认两个现实约束：

1. Cursor 插件更适合 `IDE-first` 形态
2. Cursor `CLI` 与 `IDE` 当前能力不完全等价，插件 / hooks 在 CLI 侧不应在 v1 被视为已稳定承诺

因此，Cursor 接入如果采用插件式安装，本轮正确范围应是：

1. 先做 Cursor IDE 插件
2. 不承诺 Cursor CLI parity
3. 不让 Cursor 方案侵入现有 `codex/claude` 主链

## 变更目标

### 1. Cursor 改走插件分发

- 通过 Cursor 插件统一交付 Sopify 接入能力
- 不再把 `scripts/export_cursor.py` 或 `~/.cursor/skills` 作为主方案
- 插件安装后即可获得 rules / hooks / skills 等宿主能力

### 2. 继续复用 Sopify runtime 控制面

- 继续使用现有 `.sopify-runtime/manifest.json`
- 继续使用既有 default entry / preferences preload / handoff / checkpoint 契约
- 不为 Cursor 发明第二套 runtime 协议

### 3. 不影响现有 `codex/claude`

- 不修改 `SUPPORTED_HOSTS`
- 不把 Cursor 插件式安装塞回 `install-sopify.sh`
- 不改变现有 `codex/claude` 安装器与 bridge 设计

### 4. 以插件为主，不依赖全局路径

- 不写入 `~/.cursor/skills`
- 不要求用户手工修改全局 Cursor 配置
- 插件自身应尽量自包含交付 bridge 所需资产

## 非目标

本轮明确不做以下内容：

- 不把 Cursor 纳入现有 `codex/claude` 一键安装 target
- 不先做项目导出模式作为主路径
- 不承诺 Cursor CLI 与 IDE 体验完全一致
- 不在本轮实现公开市场发布流程
- 不重写 Sopify runtime 现有 manifest / handoff / checkpoint schema

## 核心问题拆解

### 1. 为什么 Cursor 不继续走“导出到项目”主线

导出到项目的方案虽然简单，但会带来几个问题：

1. 安装体验分散，不像插件那样“一次安装即可复用”
2. rules / hooks / skills 资产容易在每个仓库分叉
3. 很难形成统一升级与版本观察面

因此，如果要正式支持 Cursor，插件式安装更符合产品形态。

### 2. 为什么 Cursor 不能直接复用 `codex/claude` 主链

原因有三点：

1. Cursor 的官方扩展面更接近插件，而不是外部安装器
2. Cursor 方案需要打包 `rules + hooks + skills`，其分发形态与 `codex/claude` 明显不同
3. 若强行塞回现有安装器，会把“外部安装器”和“宿主内插件”两类产品混在一起

因此，Cursor 应视为单独分发线，而不是第三个安装器 target。

### 3. 为什么 v1 要限定为 IDE-first

本轮不建议把 Cursor `CLI` 一并承诺，原因如下：

1. 当前公开信息更明确支持的是插件在 Cursor IDE 内的能力
2. CLI 侧插件 / hooks 能力存在不完全一致的现实风险
3. 若在 v1 同时承诺 IDE + CLI，会显著放大 doctor / smoke 与排障复杂度

因此，v1 的产品边界应是：

- 插件安装 = Cursor IDE 主链
- Cursor CLI parity = 后续评估项

### 4. Sopify 在 Cursor 插件里到底交付什么

本轮推荐插件最小交付集合为：

1. 薄 `rules`
2. 必需 `hooks`
3. Sopify `skills`
4. 插件内自带的 runtime bundle / helper 解析逻辑

后续可选扩展：

1. `subagents`
2. `MCP servers`
3. 更丰富的 commands / 面板能力

## 成功标准

满足以下条件即可认为本期目标成立：

1. Cursor 可以通过插件方式安装 Sopify
2. 插件安装后，Sopify 能在 Cursor IDE 中稳定接管 turn ingress
3. 继续复用既有 runtime manifest / preload / handoff / checkpoint 契约
4. 不写入 `~/.cursor/skills`
5. 不影响现有 `codex/claude` 主链
6. 能明确说明 IDE-first 与 CLI parity 的边界

## 风险评估

### 风险 1

如果插件打包结构完全手写，而不跟随 Cursor 官方插件脚手架，会增加格式漂移风险。

缓解：

- 以 Cursor 官方 Create Plugin / 插件脚手架为准
- 不手写猜测性的插件 schema 作为长期契约

### 风险 2

如果继续把 Cursor 当成 `workspace export` 的延伸，会形成两套安装口径。

缓解：

- 明确插件式安装为正式主线
- 项目导出只保留为调试或 fallback，不作为正式分发路径

### 风险 3

如果 v1 承诺 Cursor CLI parity，而现实里插件 / hooks 在 CLI 侧不稳，会导致产品落差。

缓解：

- plan 文档明确 IDE-first
- CLI parity 进入后续里程碑，而不是本轮交付承诺

### 风险 4

如果 Cursor 插件复制一整套独立 runtime，会抬高长期维护成本。

缓解：

- 继续复用现有 Sopify runtime bundle 与 helper contract
- 只新增 Cursor 插件分发层与宿主适配层

## 规划结论

Cursor 正式支持 Sopify 的正确方向，不是继续围绕项目导出与全局 skills 路径打补丁，而是新增一条独立的插件分发线。

因此，本轮方案结论为：

1. Cursor 走插件式安装
2. v1 限定为 IDE-first
3. 插件继续复用 Sopify 现有 runtime 控制面
4. Cursor 方案不影响 `codex/claude` 安装器主链
