# 技术设计: README / About / CHANGELOG 对外表达收口

## 技术方案

- 核心技术: Markdown、shell release hooks、Python unittest
- 实现要点:
  - README 只保留新用户需要理解的价值、工作流、目录体系和快速开始，正文 ≤250 行
  - README 首页继续保持 outcome-first；`Harness Engineering` 仅作为极短设计来源说明，不上升为首屏主叙事
  - workflow 说明下沉到 `docs/how-sopify-works.md`（CN）/ `docs/how-sopify-works.en.md`（EN）
  - 维护者内容迁入 `CONTRIBUTING.md`（EN）+ `CONTRIBUTING_CN.md`（CN）
  - `CONTRIBUTING.md` 中 `skill-authoring` 死链改回已有真源目录，不在本包补 `docs/skill-authoring*.md`
  - 长期 contract / 治理说明迁入 `.sopify-skills/blueprint/design.md`
  - CHANGELOG 草稿从“列文件”升级为“语义分组 + 动作化描述”
  - 新增 `scripts/check-readme-links.py` 自动化 README 结构验证与行数检查
  - 删除"与 HelloAGENTS 的区别"段落

## 文档职责边界

| 位置 | 面向对象 | 保留内容 | 语言策略 |
|------|---------|----------|---------|
| `README.md` | 新用户 | 价值主张、工作流、快速开始、目录体系、FAQ、命令速查 | CN |
| `README_EN.md` | 新用户 | 与 `README.md` 结构一致的英文版 | EN |
| `docs/how-sopify-works.md` | 新用户（深入阅读） | 设计来源（Harness Engineering）、主工作流、checkpoint、`.sopify-skills/` 层级说明、plan 生命周期附录 | CN |
| `docs/how-sopify-works.en.md` | 新用户（深入阅读） | 与中文 workflow 文档结构一致的英文版 | EN |
| `CONTRIBUTING.md` | 维护者 / 接入者 | runtime bundle、验证命令、同步与维护流程、Skill Authoring | EN |
| `CONTRIBUTING_CN.md` | 维护者 / 接入者 | 与 `CONTRIBUTING.md` `##` 结构对齐的中文版 | CN |
| `.sopify-skills/blueprint/design.md` | 长期架构记录 | runtime contract、checkpoint / knowledge 约束、内部治理约定 | CN (项目内部) |

## Section → Destination 映射（README 迁出清单）

冻结后作为 Step 1.1 的正式完成标准。

| 当前段落 | README.md 行范围 | 去向 | 说明 |
|---------|-----------------|------|------|
| 二次接入 runtime bundle | 84-127 | `CONTRIBUTING.md` | 维护者手工同步操作 |
| 长期偏好预载入 | 128-143 | `blueprint/design.md` | 内部契约，长期保留 |
| 硬约束复核（2026-03-19） | 145-163 | `CONTRIBUTING.md` | 维护者复核指南 |
| 首次使用 | 164-189 | `README.md` 保留 | 面向用户，但精简代码示例 |
| 仓库内最小验证 | 191-271 | `CONTRIBUTING.md` | 维护者验证路径 |
| 文档治理约定 | 274-294 | `blueprint/design.md` | 内部治理，已有类似内容 |
| KB 职责矩阵 | 295-309 | `blueprint/design.md` | 内部架构记录 |
| 第一版 checkpoint 各段说明 | 310-366 | `blueprint/design.md` | 内部契约 |
| 同步机制（维护者） | 637-655 | `CONTRIBUTING.md` | 维护者同步流程 |
| Skill Authoring（稳定规范） | 573-598 | `CONTRIBUTING.md` / `CONTRIBUTING_CN.md` | 维护者规范 |
| 分层试点材料 | 617-634 | `blueprint/design.md` | 长期项目知识，不进入 public / maintainer 快速入口 |
| 与 HelloAGENTS 的区别 | 725-737 | **删除** | 新用户无此背景知识 |
| 文件说明 | 739-758 | `README.md` 精简保留 + `docs/how-sopify-works*` | README 只保留顶层结构摘要，深入说明下沉到 workflow 文档 |

说明：`README_EN.md` 执行同样的迁出逻辑，段落位置可能有偏移但结构对应。

## README 目标约束

- 改版后 `README.md` / `README_EN.md` 正文 **≤250 行**（不含 badge 头部与代码块）
- 保留段落：价值主张、核心特性（精简为用户视角）、快速开始、首次使用、配置说明、命令参考、多模型对比、子 Skills 导航、目录结构（精简）、FAQ、版本历史、许可证、贡献
- 删除段落：与 HelloAGENTS 的区别
- 精简段落：文件说明（只保留顶层结构 + workflow 文档链接）
- 新增 1 段极短设计来源说明，放在“核心特性”与“快速开始”之间，不单独起 `##`
- 设计来源说明只保留 3 个映射点：structured knowledge / machine contracts / observable checkpoints，并链接对应语言的 workflow 文档
- `README.md` / `README_EN.md` 不引入 Harness 外部资料链接
- FAQ 如需回应 `Superpowers` 相关提问，只允许使用低权重“关系/共存”表述，不扩展为定位对比。推荐 CN 文案：`Sopify Skills 聚焦配置驱动的自适应工作流、manifest-first 机器契约与 checkpoint 可恢复性。如果宿主环境支持，它可以与其他扩展能力并存使用；本仓库不维护逐项定位对比。`

## Workflow 文档交付规格

- `README.md` / `README_EN.md` 只保留 1 个精简目录树（约 6 行）与对应语言的 workflow 文档链接：
  - `README.md` → `docs/how-sopify-works.md`
  - `README_EN.md` → `docs/how-sopify-works.en.md`
- `docs/how-sopify-works.md` / `.en.md` 使用同一结构：
  - `## 设计来源：Harness Engineering` / `## Design Rationale: Harness Engineering`
  - 1 个四行映射表：Structured Knowledge / Mechanical Constraints / Observability / Self-Healing / Continuity → Sopify 落地
  - 1 段短说明：Harness 仅作为设计来源说明，不作为仓库首页主定位
  - 1 条官方外链：OpenAI harness engineering 官方文章
  - 图 1：主工作流（Mermaid flowchart）
  - 图 2：Checkpoint 暂停 / 恢复（Mermaid flowchart）
  - 图 4：目录结构与层级（代码块）
  - 附录：图 3 Plan 生命周期（Mermaid flowchart）
- 图 1 语义固定为：`Runtime Gate → 路由判定 → 咨询 / 对比 / 回放 / 代码任务 → 代码任务内复杂度分流`
- 图 2 中 `confirm_execute` 固定为“开发前确认”，放在方案设计与开发实施的衔接处
- 图 4 的 `state/` 需要显式体现 `sessions/<session_id>/...`，用于说明并发 review 隔离
- 不映射 `Agent Cross-Review`，避免超出 Sopify 当前真实能力边界

## GitHub About 三档文案

直接产出，执行时可直接复制粘贴。

约束：

- 三档文案保持 outcome-first，不出现 `Harness Engineering`
- `tagline` 讲“配置驱动 + 自适应”，`short description` 讲“复杂度路由 + 宿主支持”，`repo description` 讲“是什么”

**Tagline:**
- CN: `配置驱动的自适应 AI 编程技能包`
- EN: `Config-driven adaptive AI coding skills`

**Short Description:**
- CN: `根据任务复杂度自动选择执行流程，支持 Codex CLI 与 Claude Code`
- EN: `Complexity-based workflow routing for Codex CLI and Claude Code`

**Repo Description:**
- `Sopify (Sop AI) Skills — adaptive AI coding skills with config-driven workflow routing`

**Topics:**
- `ai-coding`, `codex`, `claude`, `adaptive-workflow`, `skills`, `ai-agent`

## CHANGELOG 草稿策略

`render_draft()` 从 2 区域扩展到 6 个语义区域分类，每个区域附带动作化描述模板：

| 路径前缀 | 区域标题 | 动作模板 |
|---------|---------|---------|
| `README*`, `CONTRIBUTING*`, `docs/`, `LICENSE*` | Docs | "Refined public documentation" |
| `runtime/` | Runtime | "Updated runtime internals" |
| `scripts/` | Scripts | "Adjusted maintenance scripts" |
| `tests/` | Tests | "Updated automated coverage" |
| `Codex/`, `Claude/` | Skills | "Synced prompt-layer skills" |
| 其他 | Changed | "Updated project files" |

约束：
- 只出现有内容的 section，空区域不输出
- 保持 `## [Unreleased]` 与版本标题格式不变，避免破坏既有自动化
- 分类优先级从上到下匹配（一个文件只归入第一个命中的区域）

触发说明：

- 触发与分类是两层逻辑。auto-draft pipeline 仍由 `is_release_relevant_file()` 窄触发。
- 一旦 pipeline 被触发，`render_draft()` 会读取当前提交中的全量 staged files，并按上表做语义分类。
- 非 allowlist 路径不能独立触发 auto-draft，但与 release-relevant 文件同次 staged 时会进入输入并正常归类。

## README 验收脚本设计

新增 `scripts/check-readme-links.py`，覆盖以下检查项：

1. **Badge 版本一致性**: 正则提取 shield.io badge 中的版本号，与 `SOPIFY_VERSION` 比对
2. **页内锚点有效性**: 提取所有 `[text](#anchor)` 引用，验证对应 `##` 标题存在
3. **语言切换链接**: 验证 `README.md` 引用的 `README_EN.md` 存在，反之亦然
4. **CN/EN 结构对齐**: 比较两份文件的 `##` 级标题数量和顺序，不一致时报警
5. **相对文件链接存在性**: 提取所有 `./` / `../` 相对文件链接，按当前文件所在目录解析并验证目标存在
6. **README 正文行数限制**: 仅对 `README.md` / `README_EN.md` 生效；跳过首个 `---` 之前的 badge 头部区域与 fenced code block 后，剩余正文行数必须 ≤250

退出码：0 全部通过，非 0 有失败项；超标或失效项需输出具体文件与原因。

## 中英文维护者文档策略

- `CONTRIBUTING.md` 与 `CONTRIBUTING_CN.md` 只要求 `##` 标题结构对齐
- 内容允许因翻译与示例调整产生合理偏差，不做内容级 diff 校验
- 顶部入口按语言切换：
  - `README.md` 中的贡献入口指向 `CONTRIBUTING_CN.md`
  - `README_EN.md` 中的贡献入口指向 `CONTRIBUTING.md`

## 仓库外事项

- GitHub About 不作为 repo 文件提交；本包负责在 design.md 中沉淀三档文案，执行时手工更新
- 历史 `CHANGELOG` 条目治理待新格式在真实提交中稳定后再单独立项
