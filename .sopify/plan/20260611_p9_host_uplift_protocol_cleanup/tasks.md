# P9 Tasks

本文定位：P9 的波次级任务清单。粒度到 wave + sub-wave，不到具体文件 diff。具体 diff 在执行阶段按波次启动时细化。

## W0 Post-P8 Active Truth + Version Model Cleanup

W0 范围：版本模型裁定 + LLM-first 误导 prose + 版本实现修复（受控改 Sopify-core 安装器）+ 安装资产 drift + deferred plan 状态 + gate 验收。

> 执行顺序：**W0B（版本语义先裁定）→ W0A（prose/示例，依赖 W0B）→ W0C（代码修复，依赖 W0B）→ W0D（installed artifact）→ W0E（deferred plan 裁定）→ W0F（gate）**

### W0B Version model decision（先做，后续依赖其结论）

- [x] **W0.4** 裁定 workspace marker 版本语义：exact pin / host-delegated / dogfood release-sync 三选一或分场景组合。**时间盒：最多 2 轮讨论不收敛，则采用默认策略"外部项目 exact pin + Sopify 自身 dogfood release-sync"，后续 ADR 复审**
- [x] **W0.5** 写明 5 个版本锚点的合法关系：SOPIFY_VERSION header / payload_version / active_version / bundle manifest bundle_version / workspace marker bundle_version
- [x] **W0.6** 明确 `0.0.0-dev` 规则：release/stable/dogfood 禁止静默 fallback；explicit local dev 可允许但必须标记 dev channel

### W0A Active prose cleanup（依赖 W0B）

- [x] **W0.1** 重写 `blueprint/background.md:15-43` 产品栈 / 核心架构模式 / 产品形态锚点段落，去掉 Validator / Runtime 旧叙事
- [x] **W0.2** 更新 `docs/getting-started.md:98` bundle_version 示例，使其符合 W0B 裁定后的版本模式
- [x] **W0.3** 更新 `docs/dev/release-process.md:23` "runtime 单元测试 + smoke" 为当前实际 preflight 清单

### W0C Version implementation fix（受控改 Sopify-core 安装器，依赖 W0B）

- [x] **W0.7** 修复 3 处 `0.0.0-dev` 静默 fallback (受控改 Sopify-core 安装器, 全仓 6 处命中含 pyc 二进制)：**(a)** `installer/sopify_bundle.py:85` 硬编码默认值;**(b)** `installer/payload.py:220` `_normalize_payload_bundle_version(...) or "0.0.0-dev"` 兜底;**(c)** `installer/payload.py:242` `_payload_bundle_version_or_default(..., default=... or "0.0.0-dev")` 兜底。每处改为 Fail-loud: 缺版本源时直接抛 `InstallError`, dev 场景必须显式 opt-in。**dev opt-in 真规则** (不留半口子)：`SOPIFY_DEV_VERSION=1` **必须同时带显式 dev channel 版本字符串** (如 `SOPIFY_DEV_VERSION=0.0.0-dev.local` 或从 git rev / timestamp 生成);布尔开关单独存在时**不允许**落回任何模糊默认值,否则仍抛 `InstallError`。同时**审计 `scripts/w33_qoder_proof.py:28`** 里硬编码的 `bundles/0.0.0-dev` 路径: 若 W0 后 dogfood payload 不再落 `0.0.0-dev`, 同步改此测试脚本的路径假设;补最小回归测试覆盖 3 处修复
- [x] **W0.8** 修复或定义 `scripts/sopify_init.py` 对已有 `.sopify/sopify.json.bundle_version` 的升级行为（保留 exact pin vs 显式 upgrade；host-delegated 仅读取侧兼容，写入侧不产出 null）；规则先写清，再改代码
- [x] **W0.9** 修复或定义 `installer/bootstrap_workspace.py` 对 stale workspace pin 的处理与诊断，避免旧 bundle 存在时无提示继续
- [x] **W0.10a** 定义 inspection-side 4 状态 machine contract / classifier 并补单测。**边界**：4 状态枚举（`up_to_date` / `pinned_old_but_healthy` / `stale` / `broken`）及分类逻辑**留在 `installer/inspection.py`**，不抬进 `sopify_contracts/`——status/doctor 诊断态属于 inspection 面，不是 protocol kernel。classifier 输入为 `(workspace_pin, active_version, bundle_resolvable)`，输出为 4 状态之一；**`pin == null` 处理**：W0B 裁定 host-delegated 为语义预留（读取侧兼容，写入侧本次不产出 null），因此 `pin == null` 归 `broken`（marker 缺失需修复），不归 `up_to_date`；补单测覆盖每个分支 + 边界 case（pin 缺失 / active_version 缺失 / bundle 不存在）。`scripts/sopify_*.py` 消费此 classifier，不各自维护分类逻辑
- [x] **W0.10b** 基于 W0.10a classifier 更新渲染层 + 补回归测试。改动面：**(a)** `installer/inspection.py:385` 的 `render_status_text()`;**(b)** `installer/inspection.py:452` 的 `render_doctor_text()`;**(c)** `installer/distribution.py:163` 的安装完成页 doctor 调用链。`scripts/sopify_*.py` 只是包装层,真正控用户输出的是这 3 处。**职责边界**：`status` 只答"现在是什么状态" (轻量现状),`doctor` 才答"为什么这样、该怎么做" (诊断 + 下一步);4 状态 contract 主要落在 `doctor` 输出,`status` 仅轻量带出,不做成两个不同风格的半诊断工具。**status 最小信息契约**：必须让用户一眼看到 **(1)** 当前项目有没有 `.sopify/` **(2)** 当前项目是否对齐 **(3)** 4 状态中的哪一类;不允许压成只剩 `overall=partial` 这种无用信息。**中文文案参考句式** (W0 实现时统一此风格,避免"漂移/过期/失效"混用)：`up_to_date` = "当前项目已对齐到本机 Sopify 版本;无需操作。";`pinned_old_but_healthy` = "当前项目固定在旧版本,但仍可正常使用";`stale` = "当前项目记录的版本已无法在本机解析,需要刷新";`broken` = "当前项目的 Sopify 标记或安装状态损坏,需要修复"。回归测试必须覆盖 text 和 json 两种输出格式,防止 text/json 漂移

### W0D Installed artifact drift

- [x] **W0.11** 判断 `.github/copilot-instructions.md`（gitignored installed artifact）修复策略：重装刷新 vs 更新 installer 渲染源
- [x] **W0.12** 执行 W0.11 选定策略，验证与安装源一致

### W0E Deferred plan cleanup

- [x] **W0.13** 裁定 `plan/20260418_cross_review_engine/` 状态：归档为 deferred 或写明保留原因

### W0F Gate

- [x] **W0.14** 跑 active truth drift gate 4 条，全 PASS
- [x] **W0.15** 跑版本模型 gate：5 个版本锚点合法、无 release/stable/dogfood 静默 `0.0.0-dev`
- [x] **W0.16** 登记 W0 gate 结论后再启动 W1a

## W1a Three-Host Baseline + Copilot Smoke

W1a 范围：Codex / Claude / Qoder 全量 S1-S7 baseline（21 单元）+ Copilot baseline smoke（S1-S3，抓大 gap 不抓边界 case）。记录 gap，不假装 4 宿主起跑线一致。

- [x] **W1.1** 设计 7 个代表性场景的具体业务 prompt（S1 consult / S2 quick_fix / S3 light plan / S4 standard plan / S5 同宿主恢复 / S6 跨宿主恢复 / S7 finalize）。每个场景 prompt 须附带 3 项 gate quality check（来源：`assets/qoder_host_drift_learnings.md` A-G 反模式）：**(a) 包完整性** — 产出 plan 的场景（S3/S4/S5/S6/S7）须列应有文件清单（按 light/standard/architecture 级别），逐一确认存在后才算交付；**(b) 状态词一致** — prose 中的状态词（draft / accepted / frozen / retired）须与文件顶部状态字段一致，不得使用未定义状态词；**(c) 开放问题交叉核对** — "开放问题"节与任务表 BLOCKED 项不能矛盾（一边说"无"、一边有 BLOCKED = 伪关闭，反模式 B）
- [ ] **W1.2** Codex 跑 S1-S7，产出 evidence（S3/S4/S5 已完成；S1/S2 仅有人工审计依据，S6/S7 待补）
- [ ] **W1.3** Claude 跑 S1-S7，产出 evidence
- [x] **W1.4** Qoder 跑 S1-S7，产出 evidence（S1-S5 PASS；S6 SKIP 单宿主限制；S7 SKIP 不能对活跃 plan 执行 finalize，是否补隔离 finalize 证据待单独决策）
- [x] **W1.4a** Qoder rules precedence / override check：显式验证 `.qoder/rules/` 与 AGENTS.md 的优先级覆盖关系（`scripts/w33_qoder_proof.py:48` 已声明此风险），记录 rules 覆盖是否导致协议入口被绕过，产出 evidence 进 `assets/w1_gaps.md`
- [ ] **W1.5** Copilot 跑 S1-S3（baseline smoke，允许失败），产出 evidence + gap 初稿
- [ ] **W1.6** 汇总 W1a evidence 到 `assets/w1_gaps.md`（21 + 3 单元）
- [ ] **W1.7** gap 分类（平台硬限制 vs 可修 gap），Copilot gap 作为 W2 初始输入（W2.3 首次跑 S4-S7 新暴露的 gap 仍在 W2 内分类处置，不算输入泄漏）
- [ ] **W1.8** W1a gate 评审，决定是否进入 W2

## W2 Copilot Uplift + Re-Verification

W2 范围：只补 Copilot 达不到 PROTOCOL_VERIFIED 的可修 gap，修完复验；平台硬限制不得强行伪装成 verified。

- [ ] **W2.1** 按 W1a gap 清单设计 Copilot 修复方案（最小集）
- [ ] **W2.2** 修改 `installer/hosts/copilot.py` 及相关 prompt asset。**shared asset 标记**：若修改命中 `skills/` 共享 prompt source 或 `installer/payload.py` 渲染链，必须标记 `shared_asset_impact: true` 并记录到 `assets/w1_gaps.md` W2 gate note 区（不开新 schema，只做 plan-local 人类可读标记），触发 W1b 三宿主回归 smoke
- [ ] **W2.3** 复跑 Copilot S1-S7，记录 pass/fail evidence
- [ ] **W2.4** 若 7/7 PASS，则 Copilot 从 `BASELINE_SUPPORTED` 升到 `PROTOCOL_VERIFIED`；若未达成，则保持 BASELINE 并写清不可修缺口
- [ ] **W2.5** W2 gate 评审，决定是否进入 W1b

## W1b Four-Host Unified Verification（条件式）

W1b 范围：基于 W2 是否触及 shared asset，分两档执行。目的是确保 W2 修复不引入对其他宿主的回归，产出四宿主最终态统一证据。

**触发条件**：
- **轻量档**（W2 未触 shared asset）：W1b 只补 Copilot 与 W1a 其他宿主的对比结论，确认四宿主最终态可对比，不重跑 Codex/Claude/Qoder
- **回归档**（W2 命中 `skills/` 共享 prompt source 或 `installer/payload.py` 渲染链）：对 Codex / Claude / Qoder 补 S1-S3 回归 smoke（不需全量 7 场景）+ Copilot 全量 S1-S7 复验

- [ ] **W1b.1** 判定 W2 触发档位（轻量档 vs 回归档），依据 W2.2 的 `shared_asset_impact` 标记
- [ ] **W1b.2** 执行对应档位验证，产出 evidence
- [ ] **W1b.3** 汇总四宿主最终态 evidence 到 `assets/w1_gaps.md` 追加区
- [ ] **W1b.4** W1b gate 评审，决定是否进入 W3

## W3 Active Prose + Diagram Rewrite

W3 范围：基于 W1a/W2/W1b 证据重写蓝图 prose + README 图文。

- [ ] **W3.1** 重写 `blueprint/protocol.md` 活跃 prose，去掉顶部术语映射兜底
- [ ] **W3.2** 重写 `blueprint/design.md` 活跃基线视图，清理 RETIRED 补丁
- [ ] **W3.3** 全量扫描 `assets/` + `assets/readme-visuals/` + README/docs 实际引用的所有图，逐项裁定：重画 / 保留 / 历史标注 / 删除。不预设具体数量
- [ ] **W3.4** 调用 fireworks-tech-graph 出产品形态图（SVG）：Host executes / Sopify preserves / Any host resumes
- [ ] **W3.5** 调用 fireworks-tech-graph 出协议资产图（SVG）：plan / state pointers / receipts / history 如何支撑"能停、能接、能查"
- [ ] **W3.6** 更新 `README.md` / `README.zh-CN.md` 主图引用；当前 `assets/p9-product-form-v2-draft.svg` 不作为正式图基线
- [ ] **W3.7** 刷新 `blueprint/README.md` 当前焦点区块
- [ ] **W3.8** 跑 active truth drift gate，全 PASS 后登记 W3 gate
- [ ] **W3.9** 在 `README.md` / `README.zh-CN.md` 新增一节短差异化对比（spec-kit / superpowers / Sopify 三栏,≤15 行 prose），锚定"跨 Host 协议层"定位；文案引用 `plan/20260611_competitive_analysis/` 结论,不扩成长篇营销文案,不引入新术语

## W4 Optional Tooling Decision

W4 范围：审计 + 决策，不预设封装。

**借鉴边界**（来自 `plan/20260611_competitive_analysis/critical-audit-helloagents-cli.md`）：W4 允许借鉴 helloagents CLI 的**命令可发现性**（统一入口是否降低发现成本），不允许借鉴其**工作流编排厚度**（多命令前缀族 / 状态快照 / 恢复命令族扩张 / `~auto` 式自动执行入口 / 把 CLI 做成独立产品面）。薄工具，不是工作流 OS。

- [ ] **W4.1** 审计 4 个脚本（status / doctor / protocol-check / init）的 import 拓扑、调用面、依赖 `sopify_writer` / `sopify_contracts` 的方式
- [ ] **W4.2** 产出 `assets/w4_tooling_audit.md`；审计表必须覆盖三类维度：(a) **代码面**：4 个脚本的 import 拓扑、调用面、依赖 `sopify_writer` / `sopify_contracts` 的方式 (来自 W4.1)；(b) **功能覆盖度**：当前脚本是否覆盖用户最常见的三类问题——看状态 (`sopify_status.py`)、做诊断 (`sopify_doctor.py`)、做协议检查 (`sopify_protocol_check.py`)，缺口是什么；(c) **真实用例驱动**：`sopify update` 作为第一真实用例（更新宿主本地 payload + 刷新项目 marker + 组合形式），是否值得成为统一 CLI 的入口场景,驱动选项 (a)/(b)/(c)/(d) 的产品形态对比
- [ ] **W4.3** 裁定 `protocol-check --ci` 是否加入 workspace pin vs payload active_version drift 检查
- [ ] **W4.4** 列出 4 个选项对比表：(a) 维持 4 独立脚本 (b) 封统一 `sopify` 入口 (c) 只封 `sopify protocol-check --ci` (d) **以 `sopify update` 为第一真实用例的统一 CLI 封装** (包含 `sopify doctor` / `sopify update --target <host>` / `sopify update --workspace .` / 组合形式;`~update` 作为宿主层 thin wrapper,实现推迟到本决策后)；每个选项必须同时通过**正向可发现性评估**（统一入口是否真的降低用户发现成本）与**反向约束三否评估**（是否引入 (a) 新的运行时进程 (b) 自动决定工作流路线 (c) 强制流程的 hook 或 gate;违反任一项即否决）。宿主能力模型中已存在的 entry-mode hook（PreToolUse / PostToolUse / SubagentStop 等仅用于只读诊断或合规检查）**不在否决范围**,被否决的是"偷偷复活 runtime 强制力"的 hook/gate
- [ ] **W4.5** 推荐项 + 理由
- [ ] **W4.6** 若推荐封装：起草 ADR 草稿进 `blueprint/architecture-decision-records/ADR-0XX.md`
- [ ] **W4.7** W4 gate 评审，进入 Finalize

## Finalize

- [ ] **F1** 全波次 acceptance 复核
- [ ] **F2** 迁移至 `history/2026-06/20260611_p9_host_uplift_protocol_cleanup/`
- [ ] **F3** 更新 `history/index.md`
- [ ] **F4** 刷新 `blueprint/README.md` 当前焦点区块为 post-P9 状态
- [ ] **F5** 删除 `plan/20260611_p9_host_uplift_protocol_cleanup/`（归档后不双驻留）
