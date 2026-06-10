# Sopify 如何工作

## 设计来源：Harness Engineering

Sopify 借鉴 harness engineering 的设计思路，但不把它作为仓库首页定位。这里说明的是设计来源，不是产品口号。

> **说明**：下图展示的是原始设计灵感来源。部分概念（如"运行时门禁"）在当前架构中已退场——当前模型请见[核心价值](#核心价值ai-开发审计资产)和[协议入口](#协议入口4-步读链)章节。

<div align="center">
<img src="../assets/sopify-harness-cn.png" width="800" alt="Harness Engineering → Sopify 映射（历史设计参考）" />
</div>

官方参考：[`Harness engineering: leveraging Codex in an agent-first world`](https://openai.com/index/harness-engineering/)

## 核心价值：AI 开发审计资产

Sopify 把 AI 开发过程中的**方案、决策、交接、执行/验证证据和归档记录**沉淀为可追溯资产。跨 session、跨宿主的接续是这些资产可携带、可验证后的自然结果。

宿主（Codex、Claude、Qoder、Copilot）负责执行。Sopify 确保每个决策都留下痕迹，且这些痕迹能跨越 session 边界、宿主切换和团队交接。

**Runtime 已退场；工作流保留。** analyze → design → develop → finalize 的默认工作流不变。变化的是：工作流规则现在活在协议文件和宿主 prompt 资产里，而不是 runtime 进程里。

## 主工作流

<div align="center">
<img src="../assets/sopify-workflow-cn.svg" width="800" alt="Sopify 主工作流" />
</div>

工作流要点：

- 宿主从已安装的 prompt 资产中读取协议入口指令（通过 `install.sh --target <host>` 安装）
- 进入 managed plan / continuation / finalize 前，宿主按 4 步读链恢复上下文：`state/active_plan.json` → `plan/<id>/plan.md` → `state/current_handoff.json` → `plan/<id>/receipts/`
- consult 和 quick-fix 请求**不**自动接续 active plan
- 状态写入统一走 `sopify_writer`（协议资产的唯一写路径）

### Checkpoint 暂停与恢复

工作流包含两种 canonical checkpoint：

- `answer_questions` — 补事实，不提前物化正式 plan
- `confirm_decision` — 拍板分叉，确认后再恢复执行

两者都通过 `current_handoff.required_host_action` 表达，不再是独立 state 文件。

## 协议入口（4 步读链）

当宿主检测到 `.sopify/` 且用户请求指向 managed plan / continuation / finalize 时：

```
1. state/active_plan.json     → 定位 plan_id（缺失则进入 consult / new-plan）
2. plan/<id>/plan.md          → 语义入口：目标 + 进度（真相源）
3. state/current_handoff.json → 恢复提示 + 是否等用户
4. plan/<id>/receipts/        → 最新 1-3 个 receipt（哪些已验证）
```

**设计原则**：先读 `plan.md` 建立语义真相，再读 `current_handoff` 作为恢复提示。handoff 永远不是第二真相源。

**状态文件缺失时**（如新机器 fresh clone）：`active_plan.json` 和 `current_handoff.json` 按设计被 gitignore。宿主会回退到浏览 `plan/` 目录来找到活跃方案。方案和收据始终在 git 里——只有"我现在在哪"的指针是本地的。

## 目录结构与层级

```text
.sopify/
├── blueprint/                   # L1 长期蓝图（git tracked）
│   ├── README.md
│   ├── background.md
│   ├── design.md
│   ├── tasks.md
│   └── protocol.md
├── plan/                        # L2 活跃方案（git tracked）
│   └── <plan_id>/
│       ├── plan.md              # 唯一语义入口
│       ├── tasks.md             # 可选（standard+）
│       ├── design.md            # 可选（architecture 级）
│       └── receipts/            # 执行/验证证据
├── history/                     # L3 已归档方案（git tracked）
│   ├── index.md
│   └── YYYY-MM/
├── state/                       # 协议状态（gitignored，仅 2 文件）
│   ├── active_plan.json         # 当前 plan 指针
│   └── current_handoff.json     # 恢复提示 + required_host_action
├── user/
│   ├── preferences.md
│   └── feedback.jsonl
├── sopify.json                  # workspace 激活标记
└── project.md                   # 项目技术约定
```

层级说明：

- `blueprint/` 承载长期知识、协议规范与稳定契约
- `plan/` 保存当前工作方案与过程审计资产（receipts）
- `history/` 保存已收口方案与归档收据
- `state/` 是最小协议状态层——仅 2 文件，始终 gitignored

## 宿主支持

| 宿主 | Tier | 安装命令 | 说明 |
|------|------|---------|------|
| Codex | PROTOCOL_VERIFIED | `install.sh --target codex:zh-CN` | 全能力接续 |
| Claude | PROTOCOL_VERIFIED | `install.sh --target claude:zh-CN` | 全能力接续 |
| Qoder | PROTOCOL_VERIFIED | `install.sh --target qoder` | 已在 Qoder CLI 验证 |
| Copilot | BASELINE_SUPPORTED | `install.sh --target copilot` | 仅 prompt；payload 升级计划中 |

## 附录：Plan 生命周期

<div align="center">
<img src="../assets/sopify-plan-lifecycle-cn.png" width="800" alt="Sopify Plan 生命周期" />
</div>

附录只用于说明维护者视角的收口过程；普通用户理解主工作流即可。
