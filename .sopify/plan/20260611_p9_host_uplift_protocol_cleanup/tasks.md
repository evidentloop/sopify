# P9 Tasks

本文定位：P9 的波次级任务清单。粒度到 wave + sub-wave，不到具体文件 diff。具体 diff 在执行阶段按波次启动时细化。

## W0 Post-P8 Active Truth + Version Model Cleanup

W0 范围：版本模型裁定 + LLM-first 误导 prose + 版本实现修复（受控改 Sopify-core 安装器）+ 安装资产 drift + deferred plan 状态 + gate 验收。

> 执行顺序：**W0B（版本语义先裁定）→ W0A（prose/示例，依赖 W0B）→ W0C（代码修复，依赖 W0B）→ W0D（installed artifact）→ W0E（deferred plan 裁定）→ W0F（gate）**

### W0B Version model decision（先做，后续依赖其结论）

- [ ] **W0.4** 裁定 workspace marker 版本语义：exact pin / host-delegated / dogfood release-sync 三选一或分场景组合。**时间盒：最多 2 轮讨论不收敛，则采用默认策略"外部项目 exact pin + Sopify 自身 dogfood release-sync"，后续 ADR 复审**
- [ ] **W0.5** 写明 5 个版本锚点的合法关系：SOPIFY_VERSION header / payload_version / active_version / bundle manifest bundle_version / workspace marker bundle_version
- [ ] **W0.6** 明确 `0.0.0-dev` 规则：release/stable/dogfood 禁止静默 fallback；explicit local dev 可允许但必须标记 dev channel

### W0A Active prose cleanup（依赖 W0B）

- [ ] **W0.1** 重写 `blueprint/background.md:15-43` 产品栈 / 核心架构模式 / 产品形态锚点段落，去掉 Validator / Runtime 旧叙事
- [ ] **W0.2** 更新 `docs/getting-started.md:98` bundle_version 示例，使其符合 W0B 裁定后的版本模式
- [ ] **W0.3** 更新 `docs/dev/release-process.md:23` "runtime 单元测试 + smoke" 为当前实际 preflight 清单

### W0C Version implementation fix（受控改 Sopify-core 安装器，依赖 W0B）

- [ ] **W0.7** 修复 bundle manifest 生成语义（受控改 `installer/sopify_bundle.py`）：缺少版本来源时不得在 release/stable/dogfood 下静默写 `0.0.0-dev`；补最小回归测试
- [ ] **W0.8** 修复或定义 `scripts/sopify_init.py` 对已有 `.sopify/sopify.json.bundle_version` 的升级行为（保留 exact pin vs 显式 upgrade vs host-delegated）；规则先写清，再改代码
- [ ] **W0.9** 修复或定义 `installer/bootstrap_workspace.py` 对 stale workspace pin 的处理与诊断，避免旧 bundle 存在时无提示继续
- [ ] **W0.10** 更新 `scripts/sopify_status.py` / `sopify_doctor.py` 对 workspace pin vs payload active_version drift 的展示；或登记到 W4 决策表（若判定应进 `sopify_protocol_check.py --ci`）

### W0D Installed artifact drift

- [ ] **W0.11** 判断 `.github/copilot-instructions.md`（gitignored installed artifact）修复策略：重装刷新 vs 更新 installer 渲染源
- [ ] **W0.12** 执行 W0.11 选定策略，验证与安装源一致

### W0E Deferred plan cleanup

- [ ] **W0.13** 裁定 `plan/20260418_cross_review_engine/` 状态：归档为 deferred 或写明保留原因

### W0F Gate

- [ ] **W0.14** 跑 active truth drift gate 4 条，全 PASS
- [ ] **W0.15** 跑版本模型 gate：5 个版本锚点合法、无 release/stable/dogfood 静默 `0.0.0-dev`
- [ ] **W0.16** 登记 W0 gate 结论后再启动 W1

## W1 Four-Host Baseline Verification

W1 范围：4 宿主 × 7 场景，记录 gap，不假装 4 宿主起跑线一致。

- [ ] **W1.1** 设计 7 个代表性场景的具体业务 prompt（S1 consult / S2 quick_fix / S3 light plan / S4 standard plan / S5 同宿主恢复 / S6 跨宿主恢复 / S7 finalize）
- [ ] **W1.2** Codex 跑 S1-S7，产出 evidence
- [ ] **W1.3** Claude 跑 S1-S7，产出 evidence
- [ ] **W1.4** Qoder 跑 S1-S7，产出 evidence
- [ ] **W1.5** Copilot 跑 S1-S7（baseline 状态，允许失败），产出 evidence
- [ ] **W1.6** 汇总 28 个单元 evidence 到 `assets/w1_gaps.md`
- [ ] **W1.7** gap 分类（平台硬限制 vs 可修 gap）
- [ ] **W1.8** W1 gate 评审，决定是否进入 W2

## W2 Copilot Uplift + Re-Verification

W2 范围：只补 Copilot 达不到 PROTOCOL_VERIFIED 的可修 gap，修完复验；平台硬限制不得强行伪装成 verified。

- [ ] **W2.1** 按 W1 gap 清单设计 Copilot 修复方案（最小集）
- [ ] **W2.2** 修改 `installer/hosts/copilot.py` 及相关 prompt asset
- [ ] **W2.3** 复跑 Copilot S1-S7，记录 pass/fail evidence
- [ ] **W2.4** 若 7/7 PASS，则 Copilot 从 `BASELINE_SUPPORTED` 升到 `PROTOCOL_VERIFIED`；若未达成，则保持 BASELINE 并写清不可修缺口
- [ ] **W2.5** W2 gate 评审，决定是否进入 W3

## W3 Active Prose + Diagram Rewrite

W3 范围：基于 W1/W2 证据重写蓝图 prose + README 图文。

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
- [ ] **W4.2** 产出 `assets/w4_tooling_audit.md`；审计表必须覆盖两类维度：(a) **代码面**：4 个脚本的 import 拓扑、调用面、依赖 `sopify_writer` / `sopify_contracts` 的方式 (来自 W4.1)；(b) **功能覆盖度**：当前脚本是否覆盖用户最常见的三类问题——看状态 (`sopify_status.py`)、做诊断 (`sopify_doctor.py`)、做协议检查 (`sopify_protocol_check.py`)，缺口是什么
- [ ] **W4.3** 裁定 `protocol-check --ci` 是否加入 workspace pin vs payload active_version drift 检查
- [ ] **W4.4** 列出 3 个选项对比表：(a) 维持 4 独立脚本 (b) 封统一 `sopify` 入口 (c) 只封 `sopify protocol-check --ci`；每个选项必须同时通过**正向可发现性评估**（统一入口是否真的降低用户发现成本）与**反向约束三否评估**（是否引入 (a) 新的运行时进程 (b) 自动决定工作流路线 (c) 强制流程的 hook 或 gate;违反任一项即否决）。宿主能力模型中已存在的 entry-mode hook（PreToolUse / PostToolUse / SubagentStop 等仅用于只读诊断或合规检查）**不在否决范围**,被否决的是"偷偷复活 runtime 强制力"的 hook/gate
- [ ] **W4.5** 推荐项 + 理由
- [ ] **W4.6** 若推荐封装：起草 ADR 草稿进 `blueprint/architecture-decision-records/ADR-0XX.md`
- [ ] **W4.7** W4 gate 评审，进入 Finalize

## Finalize

- [ ] **F1** 全波次 acceptance 复核
- [ ] **F2** 迁移至 `history/2026-06/20260611_p9_host_uplift_protocol_cleanup/`
- [ ] **F3** 更新 `history/index.md`
- [ ] **F4** 刷新 `blueprint/README.md` 当前焦点区块为 post-P9 状态
- [ ] **F5** 删除 `plan/20260611_p9_host_uplift_protocol_cleanup/`（归档后不双驻留）
