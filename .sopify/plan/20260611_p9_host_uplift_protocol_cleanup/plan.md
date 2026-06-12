---
title: P9 Host Uplift + Protocol Cleanup + Optional Tooling
plan_id: 20260611_p9_host_uplift_protocol_cleanup
status: active
level: architecture
created: 2026-06-11
owner: sanze.li
depends_on: [P8 (protocol_kernel_runtime_retirement), P7 (payload_only_onboarding_mainline)]
---

# P9 Host Uplift + Protocol Cleanup + Optional Tooling

## Plan Snapshot

- **Goal**: 证明 P8 后的轻量协议资产在四个宿主（Codex / Claude / Qoder / Copilot）真实业务场景下能稳定接续、留痕、审计；同时收口 P8 后漂移的活跃 prose、版本模型和可选工具边界
- **Status**: active（待评审通过后按波次执行）
- **Next**: 用户评审 plan.md → design.md → tasks.md，通过后进入 W0
- **Task**: 6 段（W0 活跃真相+版本模型 / W1a 三宿主 baseline+Copilot smoke / W2 Copilot uplift / W1b 四宿主统一验证（条件式）/ W3 prose+图重写 / W4 工具决策）

## 1. Context / Why

**触发条件**（三条输入同时成立）：

1. **P8 已物理落地但 prose 未收敛**：`eed24aa` P8 PR #56 已合并、`fb19833` 发 release、`runtime/` 物理删除、4 宿主 adapter 就位、Qoder PROTOCOL_VERIFIED 证明完成。但 `blueprint/background.md:15-43` 仍写"Validator 是唯一授权者 / Runtime 确定性加固线"，`protocol.md` 28 处 runtime / `design.md` 76 处 runtime+RETIRED 补丁——**LLM 进包读到的世界观与 P8 后现状直接冲突**。
2. **四宿主验收缺真实业务证据**：P8 用 Qoder 做了 host proof，但仅覆盖 Qoder 单宿主。Codex / Claude / Copilot 未在 P8 协议形态下跑过同一组真实业务场景。`installer/hosts/copilot.py:21` 仍是 `BASELINE_SUPPORTED + PROMPT_ONLY`，P7 归档明确留了"handoff consume 待独立端到端验收"。
3. **版本锚点模型未闭环**：当前 `.sopify/sopify.json.bundle_version` 仍是 `2026-05-31.142150`，但 release 为 `2026-06-10.191940`；本机 Codex payload 的 `payload_version` 是 release 号，`active_version` / bundle manifest 却可落到 `0.0.0-dev`。这暴露出 payload version / bundle version / workspace marker pin 三层语义未收口。P9 将对 Sopify-core 安装器做最小受控修复（`sopify_bundle.py` / **`payload.py`** / `sopify_init.py` / `bootstrap_workspace.py` / `status` / `doctor` / **共享渲染层 `inspection.py` + `distribution.py`**），而非仅修 dogfood 仓库的表象。
4. **P9 前讨论已收敛产品定位**：runtime 的"中心化控制进程"形态被宿主吸收，runtime 里验证过的流程纪律（意图分流 / 复杂度先 plan / 缺事实就停 / handoff 恢复 / evidence before done / stale guard）迁移到轻量协议资产和验收矩阵。薄 CLI（status/doctor/protocol-check/init）已存在 4 个独立脚本，但未决定是否封成统一入口。

**输入来源**：

- P8 归档 `history/2026-06/20260605_p8_protocol_kernel_runtime_retirement/plan.md`
- 蓝图 `blueprint/{background,design,tasks,protocol}.md` 当前活跃 prose
- P9 前多轮讨论（runtime vs 协议资产层长期价值、GPT/qwen 审计、CLI 边界）
- 仓库审计：`scripts/sopify_status.py / sopify_doctor.py / sopify_protocol_check.py / sopify_init.py`，`installer/hosts/{codex,claude,qoder,copilot}.py`，`assets/*.svg`
- P9 前竞品分析产出 `plan/20260611_competitive_analysis/`（spec-kit / superpowers / OpenSpec / helloagents / Sopify 五对象横向对比）：其"跨 Host 协议层"定位判断被本 plan 吸收为 W3 prose 与图的叙事锚点；生态桥接 / 协议标准化 / 迁移指南等结论**仅作为 post-P9 follow-up 候选**，不进 P9 scope

**为什么新包**：

- P8 范围是 runtime 退场 + canonical root + state 极简 + Qoder 单宿主 proof；P9 范围是 4 宿主真实验收 + prose 重写 + 图刷新 + CLI 决策——主题切换，不是 P8 延续。

**为什么不在现有 plan 做**：

- `plan/20260418_cross_review_engine/` 是 deferred 残壳（`plan.md` 已不存在，只剩 `tasks.md` + `deferred/`），CrossReview 已独立成 `evidentloop/CrossReview` 自身蓝图，P9 不应吸收其集成工作。

**为什么不做 X**：

- 不做 Protocol v1 normative 升格——P8 刚 freeze 协议内核，P9 不应再开 normative 面
- 不做 pre-commit / sopify gate——与 P8 trade-off（强制力换可移植性）相反，偷偷复活破坏产品一致性
- 不做 sopify run / route / gate——在 P8 讨论里已明确否决，CLI 只做诊断和合规检查
- 不引入新宿主（Cursor / Windsurf 等）——P9 使命是证明 P8 后的 4 宿主协议能跑，铺新宿主是 P10 的事
- 不做跨 agent orchestration / 多 agent 自组织——design.md 竞品边界明确排除

## 2. Scope

**做什么**：

- **W0 Post-P8 Active Truth + Version Model Cleanup**：裁定版本语义 + 修活跃 prose 误导 + 受控改 Sopify-core 安装器版本语义（`sopify_bundle.py` / `payload.py` / `sopify_init.py` / `bootstrap_workspace.py` / `status` / `doctor` / **共享渲染层 `inspection.py` + `distribution.py`** 的最小修复）+ 修安装/marker drift + deferred plan 状态裁定 + active truth/version gate
- **W1a Three-Host Baseline + Copilot Smoke**：Codex / Claude / Qoder 全量 S1-S7（21 单元）+ Copilot S1-S3 baseline smoke，记录 gap
- **W2 Copilot Uplift + Re-Verification**：只补 Copilot 达不到 PROTOCOL_VERIFIED 的可修 gap；若平台硬限制不可修，保持 BASELINE_SUPPORTED 并记录证据型结论
- **W1b Four-Host Unified Verification（条件式）**：W2 触 shared asset 则三宿主回归 smoke，否则轻量对比结论
- **W3 Active Prose + Diagram Rewrite**：基于 W1a/W2/W1b 证据重写 blueprint/README 图文，不靠术语映射打补丁
- **W4 Optional Tooling Decision**：审计现有 4 个脚本，决定是否封成统一 `sopify` CLI

**不做什么**：

- 不写新 runtime / 不变相复刻 runtime
- 不引入第 5 个宿主
- 不做 Protocol v1 normative 升格
- 不重新设计 state 模型（P8 已定型为 2 文件）
- 不做 cross-review 集成工（CrossReview 自有蓝图）
- 不做 pre-commit / 强制门禁

## 3. Approach

**核心命题**：P8 把 Sopify 真相源从 runtime 切到了 `protocol.md + sopify_writer + receipts`。P9 要用真实业务证明这个切换是有效的——4 宿主消费同一协议资产能停、能接、能查；prose 与图与真相源对齐；薄工具有据可依。

**波次划分与依赖**：

```
W0 ── W1a (3-host baseline + Copilot smoke) ── W2 (Copilot uplift) ── W1b (4-host unified, 条件式) ── W3 (prose + 图) ── W4 (CLI 决策)
│     │                                        │                      │                                 │
│     └── W0 gate 是 W1a 前提                   └── W1a gap 是 W2 初始输入 └── W2 shared_asset_impact 决定 W1b 档位 └── W1a/W2/W1b 证据是 W3/W4 输入
```

**runtime 纪律保留方式**（plan-local 映射，不进长期 blueprint）：

| runtime 证明过的纪律 | P9 验收方式（W1a/W1b 矩阵） |
|---|---|
| 先判断意图 | `consult` / `quick_fix` 不误入 active plan |
| 复杂任务先 plan | medium/complex 生成 light/standard plan |
| 缺事实就停 | 关键信息不足时追问，不硬写 |
| handoff 恢复 | 同宿主 / 跨宿主能读 active_plan + current_handoff |
| evidence before done | finalize 前有 receipt / verification evidence |
| stale guard | 不基于过期 plan 或错 subject 继续执行 |

**W1a/W1b 验收矩阵**（7 场景，W1a 跑 Codex/Claude/Qoder 全量 + Copilot S1-S3 smoke；W1b 条件式四宿主统一验证）：

| 场景 | 触发 | 期望产出 |
|---|---|---|
| S1 consult | "解释这段代码" | 不接续 active plan，直接回答 |
| S2 quick_fix | 单文件 typo | low-touch handoff，不出 plan |
| S3 light plan | 中等任务（3-5 文件） | 出 light plan（plan.md 单文件） |
| S4 standard plan | 复杂任务（>5 文件） | 出 standard plan（plan.md + tasks.md） |
| S5 同宿主恢复 | 中断后重开 | 读 active_plan → plan.md → current_handoff → receipts |
| S6 跨宿主恢复 | A 宿主写 → B 宿主续 | 同上，且 B 能消费 A 的 receipts |
| S7 finalize | 显式 `~go finalize` | final receipt + history receipt + state 清 |

**W0 active truth drift gate**（grep 清单）：

- `grep -rn "Validator 是唯一授权者\|fail-closed 授权\|Runtime 是确定性加固线" .sopify/blueprint docs/` → 0 命中（ADR 历史记录和 design.md `[RETIRED by P8]` 标注内的引用为合法保留，不计入）
- `grep -rn "deep_verified\b" .sopify/blueprint/protocol.md` → 只在 RETIRED 注释里出现
- `grep -rn "runtime 单元测试\|runtime smoke" docs/` → 0 命中
- `grep -n "2026-05-31.142150" docs/` → 0 命中；`.sopify/sopify.json` 的 stale pin 允许保留（realign 能力留 W4 `sopify update` 实现，W0 不手改 pin 混淆 exact pin 与 release-sync 语义边界）

**W0 版本模型裁定**（已裁定，2 个正式模式 + 1 个语义预留）：

> **裁定结论**：正式模式只有 Exact pin + Dogfood release-sync。Host-delegated 保留为语义预留（读取侧兼容 `bundle_version == null`），不作为 W0 落地目标——避免扩大 workspace marker 写入语义修改面。

| 模式 | 合法状态 | 适用 | 取舍 |
|---|---|---|---|
| **Exact pin** | `.sopify/sopify.json.bundle_version == selected bundle manifest bundle_version`，且该 bundle 存在 | 外部 repo 默认 | 可复现；升级必须显式更新 marker |
| **Dogfood release-sync** | tracked `.sopify/sopify.json.bundle_version == current release tag`，且 matching bundle 存在 | Sopify 自身仓库 | release 后不漂移；发布链必须维护 |
| Host-delegated（语义预留） | `.sopify/sopify.json.bundle_version` 缺失或 `null`，由 payload `active_version` 选择有效 bundle | 未来可选 | 读取侧兼容；**写入侧本次不主动产出 null**，W0 不改 `sopify_init.py` / `bootstrap_workspace.py` 的写入语义 |

**五个版本锚点合法关系**：

```
SOPIFY_VERSION header (真相源，如 2026-06-10.191940)
  │
  ├─→ payload_version == SOPIFY_VERSION（永远相等）
  │
  └─→ bundle manifest bundle_version
        │   (来源: sopify_contracts.__version__；缺失则 Fail-loud，不静默 0.0.0-dev)
        │
        ├─→ active_version == bundle manifest bundle_version（永远相等）
        │
        └─→ workspace marker bundle_version
              Exact pin:     == bundle manifest bundle_version，且 bundle 存在
              Dogfood:       == CHANGELOG 最新 release tag
              Host-delegated: null（语义预留，读取侧兼容，写入侧本次不产出）
```

**W0 版本一致性审计锚点**：

| 锚点 | 期望 |
|---|---|
| `skills/{zh,en}/header.md.template` | SOPIFY_VERSION 与 CHANGELOG/README release 一致 |
| payload manifest `payload_version` | 当前安装 payload 版本 |
| payload manifest `active_version` | 指向存在的 bundle 目录；stable/release 不得静默落 `0.0.0-dev` |
| selected bundle `manifest.json.bundle_version` | 与 `active_version` 或 exact pin 一致 |
| workspace `.sopify/sopify.json.bundle_version` | 符合 W0 裁定的合法模式 |

**W0 安装资产分类**（重要，不无脑改版本号）：

| 文件 | git status | 角色 | 修复策略 |
|---|---|---|---|
| `.sopify/sopify.json` | tracked | workspace marker / dogfood source | W0 先裁定版本语义；禁止只改版本号制造假一致 |
| `.github/copilot-instructions.md` | gitignored | local installed artifact（installer 渲染） | W0 判断：要么重装刷新，要么更新 installer 渲染源模板（`skills/hosts.yaml` 或 `installer/payload.py`），不要直接改文件 |

**W0 Workspace upgrade 语义**（规则定型,不在本 plan 实施命令）：

- **不自动升级**：宿主本地 payload 更新后,外部项目默认保持原有 exact pin;当前 `scripts/sopify_init.py:104` 的"旧值优先"语义保留,作为 exact pin 的可复现性保证。
- **诊断责任**：`sopify_doctor.py` 负责识别 stale pin (项目 `bundle_version` 与本地 payload `active_version` 脱节,且旧版本已无法解析),并产出 1 句白话 + 1 条下一步提示。"旧但可用" ≠ "stale",前者继续可用,后者必须干预。
- **升级动作留给 W4 / post-P9**：**正式命令名统一为 `sopify update`** (W4 决定是否真的实现 CLI;本 plan 只预留语义)。`refresh` / `upgrade` 仅作为内部同义词 (refresh = 对齐语义 / upgrade = 历史命名),不再作为正式候选命令名并列出现。stale 项目的"下一步推荐提示"由 W4 实现裁定 (未来替换为 `sopify update --workspace .`),W0 不写死面向用户的具体命令;当前临时路径 (手动改 pin + 跑 `install_sopify.py --workspace .`) 仅作为内部过渡,**不作为正式用户指导文案**。

**`sopify update` 作为 W4 第一真实用例**（产品形态占位,不在本 plan 实施）：

- **官方入口**：`sopify update --target <host>` (更新宿主本地 payload) / `sopify update --workspace .` (**核心语义 = 让项目 marker 与当前已安装 payload 重新对齐**;workspace assets / instructions 是否顺带同步是 W4 实现裁定项,不提前绑死) / 两者可组合。这是统一 CLI 的第一真实用例,驱动 W4.4 选项 (d) 的产品形态评估。
- **宿主别名**：`~update` 作为宿主会话里的快捷入口,本质上是 `sopify update` 的 thin wrapper (或指向下一步 CLI 提示);不在 W0 实施,实现推迟到 W4 封装决策后。
- **分层原则**：工作流命令 (`~go` / `~go plan` / `~go finalize`) 与工具命令 (`sopify doctor` / `sopify update`) 必须分层;前者宿主内消费协议资产,后者宿主外管理安装与 marker;避免宿主 prompt 承担安装/升级主入口。

**W4 决策框架**（允许"不封装"结论）：

- 审计 4 个脚本的 import 拓扑、调用面、依赖 `sopify_writer` / `sopify_contracts` 的方式
- 列出 4 个选项：(a) 维持 4 个独立脚本 (b) 包成 `sopify {status,doctor,protocol-check,init}` 统一入口 (c) 只封 `sopify protocol-check --ci` 一个命令 (d) 以 `sopify update` 为第一真实用例的统一 CLI 封装
- 按"人和 CI 第一价值，宿主执行流第二"原则选
- 输出 ADR 草稿进 `blueprint/architecture-decision-records/`，不进 P9 plan

**Post-P9 Follow-up 预留**（不在本 plan 实施，仅作占位）：

- 协议 schema 开放标准化（plan / handoff / receipt 的 JSON schema 或 Dhall 发布）是 post-P9 候选。
- 触发条件：**至少有第二个独立项目（非 Sopify 自身 dogfood）真实写入 `.sopify/` 资产并被 Sopify 消费**；在此之前 schema 视为 Sopify-internal。
- 生态桥接（superpowers / helloagents 写入 `.sopify/`）和迁移指南同属 post-P9，前提是本 plan W1a/W2/W1b 的四宿主证据与版本语义已稳定。

## 4. Non-Goals（显式排除）

- Protocol v1 全面 normative 升格
- pre-commit / sopify gate / 强制门禁
- sopify run / route / gate / 任何自动决定工作流路线的 CLI
- 第 5 个宿主接入（Cursor / Windsurf / 等）
- CrossReview 集成工
- 跨 agent orchestration / 多 agent 自组织
- state 模型重构（P8 已定型）
- runtime 复活（任何形态）
- 知识自动提炼 / 声明式工作流引擎（design.md 明确延后项）

## 5. Risks

| 风险 | 缓解 |
|---|---|
| W1a/W1b 矩阵组合膨胀 | 严格按 7 个代表性场景执行，不做宿主两两互切全排列；W1b 按 shared_asset_impact 分档，不无脑全量复跑 |
| W2 发现 Copilot 平台能力硬限制 | 验收标准不是"和 Qoder 同构"，是"能消费协议并产出可审计资产" |
| W3 prose 重写引入新误导 | 重写前用 W0 的 drift gate 做验收，不靠顶部术语映射兜底 |
| W4 默认封装 CLI 扩大面 | W4 是决策不是实施，必须允许"不封装"结论 |
| W0 版本修复制造假一致 | 先裁定 exact pin + dogfood release-sync 合法状态，再改实现与文件 |
| W0 改动扩散到 ADR / history | W0 只动活跃 prose + 版本模型 + 安装资产 + deferred 裁定，不碰 ADR 正文和已归档 plan |
| P9 范围膨胀（补"强制力焦虑"） | 每波次启动前检查 Non-Goals 列表，新增项必须回到 §4 显式排除 |

## 6. Acceptance

**整体 Acceptance**：

- 4 宿主在 W1a/W2/W1b 后都能跑通 7 个代表性场景，产出可对比的 receipts / handoffs
- payload / bundle / workspace marker 版本模型有明确合法状态，四宿主验证基于同一合法版本基线
- `blueprint/background.md` / `protocol.md` / `design.md` 活跃段落不再误导 LLM 以为有 runtime gate / Validator 进程
- 4 个薄脚本有 ADR 草稿明确长期定位（封装 / 不封装 / 部分封装）
- `blueprint/README.md` 当前焦点区块刷新为 P9 结论
- 无新 machine truth 引入（不新增 state / action / route / checkpoint / receipt）

**W0 Acceptance**：

- active truth drift gate 4 条全 PASS
- workspace marker 版本语义已裁定：exact pin（外部项目）+ dogfood release-sync（Sopify 自身），host-delegated 为语义预留（读取侧兼容，写入侧不产出 null）
- 5 个版本锚点审计全 PASS；stable/release/dogfood 场景不得静默落 `0.0.0-dev`
- inspection-side 4 状态 classifier 已定义并有单测覆盖（枚举留在 `installer/inspection.py`，未抬进 `sopify_contracts/`）；`pin == null` 归 `broken`
- status/doctor 渲染层已基于 classifier 更新，text/json 双格式回归测试通过
- `.github/copilot-instructions.md` 与安装源一致（重装或源模板更新后验证）
- `plan/20260418_cross_review_engine/` 归档为 deferred（或写明保留原因）

**W1a Acceptance**：

- Codex / Claude / Qoder 各 S1-S7（21 单元）产出可对比的 evidence
- Copilot S1-S3 baseline smoke 产出 evidence + gap 初稿
- Qoder rules precedence / override check（W1.4a）产出独立 evidence
- 每个 gap 登记到 `plan/20260611_p9_*/assets/w1_gaps.md`
- Copilot gap 分类完成（平台硬限制 vs 可修 gap），作为 W2 初始输入（W2.3 新暴露 gap 在 W2 内分类处置）
- Copilot 已知 baseline 不足不混入"4 宿主都过"的结论

**W2 Acceptance**：

- W1a 登记的 Copilot 可修 gap 已修复
- 若修改命中 `skills/` 共享 prompt source 或 `installer/payload.py` 渲染链，必须标记 `shared_asset_impact: true` 并记录到 `assets/w1_gaps.md` W2 gate note 区
- 若 Copilot S1-S7 7/7 PASS，则从 `BASELINE_SUPPORTED` 升到 `PROTOCOL_VERIFIED`（改 `installer/hosts/copilot.py`）
- 若存在平台硬限制，则保持 `BASELINE_SUPPORTED`，写明不可修缺口、用户影响和后续触发条件

**W1b Acceptance**：

- W1b 档位已按 W2.2 `shared_asset_impact` 标记判定（轻量档 vs 回归档）
- 轻量档：四宿主最终态对比结论已补充，`assets/w1_gaps.md` 追加区记录
- 回归档：Codex / Claude / Qoder S1-S3 回归 smoke + Copilot S1-S7 全量复验均通过
- 四宿主最终态 evidence 可对比，W1b gate 通过

**W3 Acceptance**：

- `protocol.md` 活跃 prose 不再依赖顶部 P8 术语映射兜底
- `design.md` 的 RETIRED 补丁清理为 active baseline 视图
- 完成 asset inventory 全量扫描：`assets/` + `assets/readme-visuals/` + README/docs 实际引用的所有图逐项裁定（重画 / 保留 / 历史标注 / 删除），不预设具体数量
- `assets/` 至少刷新 2 张正式图（产品形态图 + 协议资产图），数量上不封顶（依赖 W3.3 全量扫描结论）；当前 `assets/p9-product-form-v2-draft.svg` 为 V2 草稿（Style 8 手写），不作为 W3 正式图基线
- `README.md` / `README.zh-CN.md` 主图与 prose 一致
- `README.md` / `README.zh-CN.md` 包含一节短差异化对比（spec-kit / superpowers / Sopify 三栏,≤15 行 prose），锚定"跨 Host 协议层"定位,不扩成长篇营销文案

**W4 Acceptance**：

- `scripts/sopify_{status,doctor,protocol_check,init}.py` 审计表进 `assets/w4_tooling_audit.md`
- 审计表必须覆盖**代码面**（import 拓扑、调用面、依赖 `sopify_writer` / `sopify_contracts` 的方式）与**功能覆盖度**（当前脚本是否覆盖"看状态 / 做诊断 / 做协议检查"三类用户常见问题,缺口是什么）
- **真实用例驱动**：审计表必须评估"`sopify update` 作为第一真实用例"是否值得成为统一 CLI 的入口场景,驱动选项 (a)/(b)/(c)/(d) 的产品形态对比
- 4 个选项对比表 + 推荐项 + 理由
- 明确 `sopify_protocol_check.py --ci` 是否应加入 workspace pin vs payload active_version drift 检查
- **借鉴边界**（来自 `plan/20260611_competitive_analysis/critical-audit-helloagents-cli.md`）：允许借鉴 helloagents CLI 的**命令可发现性**，不允许借鉴其**工作流编排厚度**（多命令前缀族 / 状态快照 / 恢复命令族扩张 / `~auto` 式自动执行入口 / 把 CLI 做成独立产品面）
- **CLI 评估配对**：每个选项必须同时通过 (a) **正向可发现性评估**（统一入口是否真的降低用户发现成本）与 (b) **反向约束三否评估**（是否引入新的运行时进程 / 自动决定工作流路线 / 强制流程的 hook 或 gate;违反任一项即否决）。宿主能力模型中已存在的 entry-mode hook（PreToolUse / PostToolUse / SubagentStop 等仅用于只读诊断或合规检查）**不在否决范围**,被否决的是"偷偷复活 runtime 强制力"的 hook/gate
- ADR 草稿（若推荐封装）进 `blueprint/architecture-decision-records/ADR-0XX.md`

## 7. Tasks

详见 `tasks.md`。

波次顺序：W0 → W1a → W2 → W1b（条件式）→ W3 → W4。每波次启动前检查前一 gate。

## 8. Assets

- 产品形态图（SVG）：`assets/sopify-product-form-p9.svg`（W3 产出）
- 协议资产图（SVG）：`assets/sopify-protocol-assets-p9.svg`（W3 产出）
- W1a/W1b gap 登记：`assets/w1_gaps.md`
- W4 工具审计：`assets/w4_tooling_audit.md`
- W4 ADR 草稿（若）：`blueprint/architecture-decision-records/ADR-0XX.md`
- 产品形态图 V2 草稿（Style 8）：`assets/p9-product-form-v2-draft.svg`（跨渲染器鲁棒，仍待 W3 基于 W1a/W2/W1b 证据出正式版替换）
