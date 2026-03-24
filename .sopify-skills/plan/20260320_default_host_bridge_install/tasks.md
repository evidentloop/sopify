---
plan_id: 20260320_default_host_bridge_install
feature_key: default-host-bridge-install
level: standard
lifecycle_state: active
knowledge_sync:
  project: review
  background: review
  design: review
  tasks: review
blueprint_obligation: review_required
archive_ready: false
plan_status: on_hold
---

# 任务清单: 默认启用宿主桥接的一键安装（`default-host-bridge-install`）

## 当前状态

- `2026-03-24` 基线清理：本 plan 保留内容，但暂标记为 `on_hold`，不进入当前执行序列。
- 恢复条件：确认默认 host bridge 安装主链重新排期后再恢复实施。

## A. 已冻结决策

- [x] A.1 用户安装入口继续保持单条命令
- [x] A.2 本轮不暴露 `--bridge` 参数
- [x] A.3 bridge 升级为默认安装语义，而不是可选增强项
- [x] A.4 bridge 实现保持在 installer core 之外，由 façade 编排
- [x] A.5 本轮不扩展 `cursor` 到一键安装主链
- [x] A.6 采用“一套 shared bridge core + 两个 host adapter”
- [x] A.7 `claude v1` 固定为最小 hooks 集：`UserPromptSubmit + Stop`
- [x] A.8 `codex v1` 固定为 `launcher bridge`
- [x] A.9 `codex app-server bridge` 仅作为后续演进方向，不进入本轮默认主链

冻结标准：

- 方案文档中不存在 `--bridge on/off/auto` 的用户命令面
- `codex` / `claude` 仍是唯一正式 host target
- `codex` 不再被描述成 Claude-style hook 宿主

## B. 待实施任务

### 1. 安装入口重构

- [ ] 1.1 新增 façade 安装入口，默认编排 `core install + bridge deploy + doctor`
- [ ] 1.2 保持 `bash scripts/install-sopify.sh --target <host:lang>` 为唯一用户入口
- [ ] 1.3 保留 `scripts/install_sopify.py` 作为 installer core entry，不直接承担 bridge 逻辑
- [ ] 1.4 façade 输出统一安装结果，但不破坏旧 core install 语义

验收标准：

- 用户命令面不增加新参数
- 旧 core installer 仍可单独运行与测试
- façade 能组合展示 core 与 bridge 两段结果

### 2. shared bridge core

- [ ] 2.1 新增独立 `host_bridge/` 模块，承载共享 turn-level ingress 逻辑
- [ ] 2.2 bridge 核心链路固定为：preflight -> preload -> runtime dispatch -> handoff loop
- [ ] 2.3 bridge 只消费既有 manifest / handoff / checkpoint 契约，不新造第二套协议
- [ ] 2.4 shared core 输出统一 trace markers，供 doctor / smoke 复用

验收标准：

- bridge 目录结构与 installer core 解耦
- bridge 不直接修改 runtime schema
- `claude` 与 `codex` 共用 preflight / preload / dispatch / handoff core

### 3. Claude host adapter

- [ ] 3.1 部署 `~/.claude/sopify/bridge/` 资产
- [ ] 3.2 注册最小 hooks 集：`UserPromptSubmit + Stop`
- [ ] 3.3 `UserPromptSubmit` 进入 shared bridge core
- [ ] 3.4 `Stop` 覆盖 clarification / decision / execution confirm 的 fail-closed

验收标准：

- Claude hooks 配置可定位、可验证
- `UserPromptSubmit` 能稳定先于宿主主链执行 runtime ingress
- pending checkpoint 不能被 `Stop` 误收口

### 4. Codex host adapter

- [ ] 4.1 部署 `~/.codex/sopify/bridge/` 资产
- [ ] 4.2 部署 `~/.codex/sopify/bin/` launcher
- [ ] 4.3 launcher 在宿主处理请求前先进入 shared bridge core
- [ ] 4.4 launcher 对 clarification / decision / execution confirm 执行 fail-closed

验收标准：

- 不依赖未公开的 Codex hooks / 私有配置点
- launcher 可解析 workspace / manifest / preload / default entry
- pending checkpoint 不能被绕过成普通开发入口

### 5. 组合结果与渲染

- [ ] 5.1 façade 层新增 `BridgeInstallResult`
- [ ] 5.2 façade 层新增 `UnifiedInstallResult = core + bridge`
- [ ] 5.3 安装结果渲染新增 `Bridge:` 区块
- [ ] 5.4 不直接修改旧 `InstallResult` 的 core 语义

验收标准：

- 老的 core installer API 不因 bridge 方案失真
- 安装输出能清楚分辨 Host / Payload / Workspace / Bridge
- bridge 失败时能明确定位到 bridge 阶段，而不是误报成 payload 或 workspace 问题

### 6. 校验链路

- [ ] 6.1 保留现有 core install smoke，不改变其职责
- [ ] 6.2 新增 bridge doctor，检查部署与 ingress 可达性
- [ ] 6.3 新增 bridge smoke，验证 turn-level preflight / preload / runtime dispatch / handoff loop
- [ ] 6.4 bridge smoke 至少覆盖 clarification / decision / execution confirm 的 fail-closed 行为

验收标准：

- core smoke 与 bridge smoke 分工清晰
- `claude` 与 `codex` 的 doctor / smoke 各自验证真实接法
- 任何“只装了 prompt/payload、没装或没接管 bridge”的情况都能被 doctor / smoke 看出来

### 7. 文档与 rollout

- [ ] 7.1 安装 README 与宿主接入文档统一改为“默认安装 bridge”的口径
- [ ] 7.2 文档不再出现 `--bridge` 参数说明
- [ ] 7.3 rollout 先以 façade 替换安装入口，不要求本轮重写 installer core
- [ ] 7.4 保留 legacy core install 作为内部依赖与回退抓手

验收标准：

- 文档口径与安装行为一致
- 新默认行为不需要用户做额外理解
- 出现 bridge 回归时仍有清晰的内部回退路径

## C. 推荐实施顺序

1. 先补 façade 安装入口与组合结果模型
2. 再实现 shared bridge core 与 trace marker
3. 然后接通 `claude` 最小 hooks 集
4. 再接通 `codex` launcher bridge
5. 最后补 doctor / smoke 与文档收口
