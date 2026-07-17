# 变更提案: Sopify 会话入口状态预检

## 需求背景

P8 runtime 退场后，宿主通过 prompt 和文件协议判断是否接续活动方案。现有协议已经规定 consult / quick fix 不自动读取 `active_plan`，但异常状态的处理边界仍不够完整：缺失与冲突容易被一概当成阻断，状态提示也可能抢占用户真正的问题。

本方案要补的是一个有限的会话入口状态预检：先识别用户意图，只在 managed plan 操作真正依赖状态链时检查；能够确定的情况直接继续，存在有效方案意图分叉时才向用户询问一次。

评分:
- 方案质量: 9/10
- 落地就绪: 9/10

评分理由:
- 优点: 复用 P8 两文件状态模型、现有 `workspace_status_lite` 和宿主 prompt，不恢复 runtime，也不新增诊断平台。
- 扣分: “先回答用户”属于宿主行为，除自动化契约测试外仍需一次宿主上下文隔离回放验证。

## 变更内容

1. 在 Host Protocol Entry Contract 中增加意图 × 状态处理矩阵，区分静默放行、非阻断提示和阻断一次。
2. 扩充 `workspace_status_lite` 的必要客观事实，使宿主能区分 active plan 文件缺失与内容无效，并判断 `plan.md` 是否存在、handoff 是否与活动方案匹配；MCP 不可用时仍按文件协议继续。
3. 收紧中英文宿主 prompt：用户当前请求优先，异常只阻断它所依赖的 managed plan 操作。
4. 建立有限状态自动测试，并用一次 Codex 上下文隔离回放验证陈旧状态不会劫持普通问答。
5. 同步协议、产品说明和 blueprint，完成后按现有 lifecycle 归档。

## 影响范围

- 模块: Host Protocol Entry Contract、MCP lite status、宿主 prompt、安装资产测试、产品文档与 blueprint。
- 主要候选文件:
  - `.sopify/blueprint/protocol.md`
  - `scripts/sopify_mcp_server.py`
  - `skills/zh/header.md.template`
  - `skills/en/header.md.template`
  - `tests/test_sopify_mcp_server.py`
  - `tests/test_installer.py`
  - `docs/how-sopify-works.md`
  - `docs/how-sopify-works.en.md`
  - `docs/getting-started.md`
  - `.sopify/blueprint/{README,design,tasks}.md`

## 风险评估

- 风险: 入口规则过重，使每轮请求都扫描状态并输出诊断。
- 缓解: 先做意图分类；consult / quick fix 不进入状态链，健康 managed plan 静默通过。

- 风险: 为减少询问而错误覆盖仍有效的活动方案。
- 缓解: 只有无效旧指针且用户明确发起 new plan 时直接切换；有效方案始终保留切换、合并、暂停的用户决策。

- 风险: 只补 prompt 文案，真实宿主仍可能被异常状态劫持。
- 缓解: 自动化覆盖确定性事实和安装资产，再用一次 Codex 上下文隔离回放验证关键用户路径。

- 风险: new plan、旧 checkpoint 和失配 handoff 同时存在时触发多次询问。
- 缓解: 固定“本轮用户意图 → 活动方案有效性与主体绑定 → 匹配方案的 handoff/checkpoint”优先序，旧方案 checkpoint 不参与 new plan 仲裁。

- 风险: 同一 workspace 的两个 session 都基于旧状态准备写入，后者静默覆盖前者。
- 缓解: session 标识仅写入既有 observability；managed 写入前重读 active plan 与匹配 checkpoint，发现已变化则不覆盖，只对受影响动作提示一次。不在本方案引入锁、租约或 session 注册表。

- 风险: 为覆盖异常继续引入状态枚举、诊断记录和修复流程。
- 缓解: 工具只返回少量客观事实；不新增 machine truth、持久诊断状态或自动修复入口。

- 风险: 把 repo-local MCP 试点误写成所有宿主的入口依赖。
- 缓解: 4 步文件读取始终是规范路径；`workspace_status_lite` 仅在可用时减少重复读取。
