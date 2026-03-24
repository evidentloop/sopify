---
plan_id: 20260320_cursor_plugin_install
feature_key: cursor-plugin-install
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

# 任务清单: Cursor 插件式安装 Sopify（`cursor-plugin-install`）

## 当前状态

- `2026-03-24` 基线清理：本 plan 保留内容，但暂标记为 `on_hold`，不进入当前执行序列。
- 恢复条件：确认 Cursor 插件路线重新进入当前优先级后再恢复实施。

## A. 已冻结决策

- [x] A.1 Cursor 正式接入走插件式安装，不再以项目导出为主线
- [x] A.2 不写入 `~/.cursor/skills`
- [x] A.3 不改用户全局 Cursor 配置作为前提条件
- [x] A.4 Cursor 方案不复用现有 `codex/claude` 安装器主链
- [x] A.5 Cursor v1 限定为 IDE-first，不承诺 CLI parity
- [x] A.6 插件继续复用 Sopify 现有 runtime manifest / preload / handoff / checkpoint 契约
- [x] A.7 插件最小交付为 `rules + hooks + skills`
- [x] A.8 hooks 为真正的 turn ingress 接口，skills 不承担宿主桥接职责

冻结标准：

- 方案文档不再把 `export_cursor.py` 写成正式主安装入口
- 方案文档不要求 `~/.cursor/skills`
- 方案文档明确 `Cursor IDE != Cursor CLI` 的 v1 边界

## B. 待实施任务

### 1. 插件源码与打包骨架

- [ ] 1.1 新增 `integrations/cursor-plugin/` 目录骨架
- [ ] 1.2 明确插件源码、构建目录、资产目录的边界
- [ ] 1.3 新增 `scripts/build_cursor_plugin.py`
- [ ] 1.4 对接 Cursor 官方 scaffold / Create Plugin 流程

验收标准：

- 仓库内存在可维护的 Cursor 插件源码目录
- 插件打包结构以官方 scaffold 为准
- 不需要修改现有 `install-sopify.sh`

### 2. 共享资产收集

- [ ] 2.1 从现有 runtime 源收集 bundle / helpers / manifest 相关资产
- [ ] 2.2 建立插件产物与共享 runtime 源的版本映射
- [ ] 2.3 确保插件内 helper 不手工复制脱节
- [ ] 2.4 明确插件 bootstrap 使用的 bundle 来源

验收标准：

- 插件 bundle 来源唯一
- 插件内 helper 与仓库 helper 版本一致
- 不需要依赖 `codex/claude` payload 才能工作

### 3. Cursor host adapter

- [ ] 3.1 实现 Cursor 插件内薄 rules
- [ ] 3.2 实现最小 hooks 集：`beforeSubmitPrompt + stop`
- [ ] 3.3 将 hooks 接入 Sopify preflight / preload / runtime dispatch / handoff loop
- [ ] 3.4 实现 pending checkpoint 的 fail-closed

验收标准：

- hooks 真正承担 turn ingress
- rules 只保留 always-on 契约，不重复长技能文案
- clarification / decision / execution confirm 三类 pending 状态均不可绕过

### 4. Skills 适配

- [ ] 4.1 梳理要纳入插件的 Sopify skills 最小集合
- [ ] 4.2 处理 Cursor 下的 skill 发现与加载方式
- [ ] 4.3 避免 skills 与 hooks 在入口职责上重叠
- [ ] 4.4 评估 commands 是否作为插件稳定打包面进入 v1

验收标准：

- skills 与 hooks 职责边界清晰
- 插件最小集合足以支持 Sopify 主流程
- commands 若未被官方 schema 稳定支持，则不自造目录规范

### 5. doctor / smoke

- [ ] 5.1 新增 repo-side `check_cursor_plugin_package.py`
- [ ] 5.2 设计 plugin-side doctor 入口
- [ ] 5.3 建立 IDE-first smoke contract
- [ ] 5.4 将 CLI parity 明确排除在 v1 smoke 通过标准之外

验收标准：

- 包完整性可在仓库内验证
- 插件安装后的诊断信息可在 Cursor 内查看
- smoke 能证明 preflight -> preload -> runtime dispatch -> handoff 顺序已执行

### 6. 分发与文档

- [ ] 6.1 编写 Cursor 插件安装文档
- [ ] 6.2 明确团队内私有分发路径
- [ ] 6.3 说明 IDE-first 边界与 CLI parity 状态
- [ ] 6.4 说明 Cursor 插件与 `codex/claude` 主链的关系

验收标准：

- 用户能理解 Cursor 是独立插件线
- 文档不再把 Cursor 描述为 `codex/claude` 的附属安装 target
- 用户能清楚知道 v1 的能力边界

## C. 推荐实施顺序

1. 先搭 `integrations/cursor-plugin/` 与构建脚本骨架
2. 再接通共享 bundle / helper 收集
3. 然后实现 Cursor 最小 hooks 集与薄 rules
4. 再接入 Sopify skills 最小集合
5. 最后补 doctor / smoke 与团队内分发文档
