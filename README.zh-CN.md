# Sopify

<div align="center">

**先问再写、随时恢复的 AI 编程**

[![许可证](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![文档](https://img.shields.io/badge/docs-CC%20BY%204.0-green.svg)](./LICENSE-docs)
[![版本](https://img.shields.io/badge/version-2026--05--31.142150-orange.svg)](#版本历史)
[![欢迎PR](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING_CN.md)

[English](./README.md) · 简体中文 · [快速开始](#快速开始) · [贡献者](./CONTRIBUTORS.md)

</div>

<div align="center">
<img src="./assets/sopify-cover-cn.jpg" width="660" alt="Sopify — 先问再写、随时恢复的 AI 编程" />
</div>

---

AI 工具写代码很快。但没搞清楚需求就动手，快就变成了返工。Sopify 帮你保存 AI 编程的全过程——方案、决策、交接、验证记录——所以中断后能从上次停下的地方继续，即使换到不同的 AI 宿主也能接力。

无需新编辑器、无需新 CLI。安装到你已有的宿主：Codex、Claude、Qoder、Copilot 均支持。

**设计原则：**

- **不确定就停下** — 需求不全时先追问，再动手
- **随时恢复** — 方案、决策、收据都持久保存在 git 里；换宿主、换机器、换人接手都能从项目状态继续
- **决策留痕** — 方案、取舍、审查持久保存在 `.sopify/`

**Sopify 主要在防什么：**

- **过早开写** — 关键信息没补齐、关键决策没拍板，AI 就直接改代码
- **接力断档** — 一换宿主、换机器、换人接手，就得重新解释上下文
- **决策失忆** — 重要取舍留在聊天里，没沉淀成项目资产

[查看工作流图、checkpoint 与恢复流程 →](./docs/how-sopify-works.md)

## 实战演示

<p align="center">
  <img src="./assets/demo-en.svg" alt="Sopify 演示 — 在 Claude Code 分析设计，然后在 Codex CLI 恢复开发" width="900" />
</p>

## 快速开始

```bash
curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/install.sh | bash -s -- --target codex:zh-CN
```

安装后用 `~go` 启动全托管工作流。审查优先安装、其他宿主和 Windows 请看[安装说明](#安装说明)。

**已在 Sopify 管理的仓库里？** 打开任意 AI 宿主，让它继续未完成的任务——它会从上次停点恢复。

## 为什么选择 Sopify？

**需求不清楚时，它会停下来。**
你说"加个缓存"。Sopify 不急着动手——先分析需求、设计方案、拆分任务，把讨论结果沉淀到 `.sopify/plan/` 里。方案确认后才写代码，改的每一行都有据可查。

<div align="center">
<img src="./assets/readme-visuals/sopify-scene-ask.jpg" width="720" alt="先有方案 再写代码 — 讨论·沉淀·执行" />
</div>

**你的队友可以直接接手。**
你在 Codex 里开始一个功能，完成了设计和两个任务。下周队友打开同一个仓库的 Claude，输入 `~go`。Sopify 读取 checkpoint，从任务 3 继续——不用写交接文档，不用重新交代上下文。

<div align="center">
<img src="./assets/readme-visuals/sopify-scene-cross-host.jpg" width="720" alt="跨宿主无缝接力" />
</div>

**每个决策都留有痕迹。**
一个月后，有人问为什么缓存 key 里带了用户 ID。答案在 `.sopify/plan/` 里——触发这个决策的需求、设计它的方案、通过它的审查，一应俱全。

<div align="center">
<img src="./assets/readme-visuals/sopify-scene-decision.jpg" width="720" alt="决策留痕 可追溯" />
</div>

## 架构

<div align="center">
<img src="./assets/sopify-architecture.svg" width="760" alt="Sopify 架构 — 协议内核 + 工作流 + 宿主适配" />
</div>

宿主 LLM 负责执行。Sopify 把 AI 开发过程中的审计资产——方案、决策、交接、验证证据——持久保留在 `.sopify/` 中，跨 session、宿主和团队成员均可访问。

Sopify 靠四件事做到稳定可控、质量可靠：

- **每个宿主同一套规则** — Claude、Codex、Qoder、Copilot 加载的是同一套 Sopify 指令，切换宿主不会把流程重置
- **一切都持久保存在 git 里** — 方案、决策、验证记录都落在 `.sopify/`，后续接手读的是项目状态，不是上一段对话
- **从上次停下的地方继续** — 宿主读取当前方案、上次交接记录和已验证内容，然后接着干
- **Runtime 已退场；工作流保留** — analyze → design → develop → finalize 流程不变；变的是规则活在文件里，不再依赖 runtime 进程

## 安装说明

审查优先安装：

```bash
curl -fsSL -o sopify-install.sh https://github.com/evidentloop/sopify/releases/latest/download/install.sh
less sopify-install.sh          # 审查后再执行
bash sopify-install.sh --target codex:zh-CN
```

Windows PowerShell：

```powershell
iwr https://github.com/evidentloop/sopify/releases/latest/download/install.ps1 -OutFile sopify-install.ps1
Get-Content sopify-install.ps1 | more
.\sopify-install.ps1 --target codex:zh-CN
```

宿主支持：

| 宿主 | Tier | Target | 说明 |
|------|------|--------|------|
| Codex | PROTOCOL_VERIFIED | `codex:zh-CN` / `codex:en-US` | 全能力接续 |
| Claude | PROTOCOL_VERIFIED | `claude:zh-CN` / `claude:en-US` | 全能力接续 |
| Qoder | PROTOCOL_VERIFIED | `qoder` | 已在 Qoder CLI 验证 |
| Copilot | BASELINE_SUPPORTED | `copilot:zh-CN` / `copilot:en-US` | 仅 prompt；payload 升级计划中 |

可用 `--workspace <path>` 指定目标仓库，`--language <lang>` 控制输出语言。

完整设置指南见 [Getting Started](./docs/getting-started.md)。分步 demo 见 [External Repo Quickstart](./examples/external-repo-quickstart/README.md)。

## 命令参考

| 命令 | 说明 |
|-----|------|
| `~go` | 自动判断并执行完整流程（有活动 plan 时自动恢复执行） |
| `~go plan` | 只规划不执行 |
| `~go finalize` | 收口当前活动方案 |

普通用户只需要记住 `~go / ~go plan`；维护者验证命令放在 [贡献指南](./CONTRIBUTING_CN.md)。

## 配置说明

```bash
cp examples/sopify.config.yaml ./sopify.config.yaml
```

```yaml
brand: auto
language: zh-CN

workflow:
  mode: adaptive   # strict | adaptive | minimal
  require_score: 7

```

## 目录结构

```text
sopify/
├── scripts/               # 安装、诊断与维护脚本
├── examples/              # 配置示例
├── docs/                  # 工作流指南与开发者参考
├── sopify_writer/         # 协议资产写入库
├── sopify_contracts/      # schema 定义与共享数据结构
├── skills/                # prompt-layer 源码
├── installer/             # 宿主适配器与安装编排
└── .sopify/               # 项目协议根目录
    ├── blueprint/         # 协议规范、设计基线与削减目标
    ├── plan/              # 活跃方案 + receipts
    └── history/           # 已归档方案 + receipts
```

完整工作流、checkpoint 和知识库层级说明见 [工作流说明](./docs/how-sopify-works.md)。

## 版本历史

- 详细变更记录见 [CHANGELOG.md](./CHANGELOG.md)

## 许可证

- 代码与配置：Apache 2.0，见 [LICENSE](./LICENSE)
- 文档：CC BY 4.0，见 [LICENSE-docs](./LICENSE-docs)

## 贡献

提交用户可见行为改动时，建议同步更新 `README.md` / `README.zh-CN.md`，并参考 [CONTRIBUTING_CN.md](./CONTRIBUTING_CN.md) 执行校验。
