# T4 冗余清理与 T6 接入指南修订独立验收报告

**验收者**：独立验收官（Antigravity / Gemini）  
**验收对象**：
- 提交 `8285888`（T4 中等档冗余清理，父提交 `a9f6825`）
- 提交 `a9f6825`（包含 T6 修订版 `docs/host-onboarding.md`）  
**测试隔离**：在独立 Git worktree（`/private/tmp/.../t4-accept-wt`）中执行全量验证与静态扫描，主工作区零修改，验证完毕后已彻底清除 worktree。  
**参考基准**：
- `.sopify/plan/20261020_sopify_narrow_focus/plan.md`（统一验收标准）
- `.sopify/plan/20261020_sopify_narrow_focus/tasks.md`（T4、T6 定义与完成条件）
- 执行官报告：`t4-codex.md`、前序验收报告：`t6-accept-gemini.md`

---

## 一、验收结论

| 任务 | 验收裁决 | 最小修改建议清单 |
|---|:---:|---|
| **T4 冗余清理（提交 8285888）** | **【通过】** | **无阻断修改**。22 处文件变更净减 2,292 行，未丢失任何现行架构决策，0 失效引用，全量 386 测试与 release-preflight 100% 通过。建议在后续 T7/T8 发版前顺手微调 `render-host-skills.py:98` 将中文字符数标签由 bytes 澄清为 chars（非阻断项）。 |
| **T6 接入指南（docs/host-onboarding.md）** | **【通过】** | **无新增修改**。首轮验收提出的 4 项最小修改（时序重排、PROTOCOL_VERIFIED 精简、3 种 surface 说明、提问工具与生成脚本细节）已全部完整落实，篇幅精准收敛至 172 行。 |

---

## 二、逐项核实与证据

### 1. `.sopify/blueprint/design.md` 删减核对（714 行 → 149 行，删减 565 行）

核对重点：是否丢失现行架构决策？

- **删减内容分类审查**：
  1. **已明确退场的历史负担（约 320 行）**：
     - `ExecutionAuthorizationReceipt（授权脊柱）— *[RETIRED by P8]*` 全文及字段细节；
     - `Runtime 五层架构 — *[RETIRED by P8]*`（Ingress、State Resolution、Routing、Execution、Knowledge Lifecycle 各层展开）；
     - `Route Families — *[P8 后不再承诺]*`、`Non-family Surfaces`；
     - `Legacy Mapping（P8 退场）`、`Mainline-only Keep-list（pre-P8 legacy reference）`；
     - `Output Rendering Audit — *[pre-P8 legacy reference]*`；
     - `宿主能力治理（pre-P8 legacy reference）`、`Runtime gate ingress`、`Runtime state scope`。
     - **核查判定**：上述内容均已在 P8 中物理删除或退场，保留在现行蓝图中只会误导新宿主与贡献者，删除完全正确。沿革已按规范统一链接至 `history/2026-06/` 归档。
  2. **与 Protocol 重复的规范细节（约 150 行）**：
     - ActionProposal / Receipt 具体字段细节（已由 `protocol.md §7` 规范）；
     - Ingress 验证序列、Missing-file 降级规则、Reading Budget（已由 `protocol.md §8` 规范）；
     - Verifier 边界规范（已由 `protocol.md §6` 规范）。
     - **核查判定**：消除“两份真源”，将 normative 协议条款收敛至 `protocol.md`，`design.md` 仅保留职责边界与索引，符合单真源原则。
  3. **与 README / Installer 重复的静态表格（约 95 行）**：
     - 各宿主重复的安装命令行与能力展开表（由 README 与 `installer/hosts/` 唯一定义）。
- **现行架构决策留存验证**：
  - **模块边界**（第 24–42 行）：`sopify_contracts/`（schema/版本）、`sopify_writer/`（确定性结构/版本校验/receipt 写入/归档）、`skills/{zh,en}/`（prompt 单源）、`installer/hosts/`、`payload.py`、`bootstrap_workspace.py`、`inspection.py`、`protocol_check.py` 完整定义；
  - **宿主能力梯度**（第 106–114 行）：`convention_only`、`payload_capable`、`protocol_verified` 3 级划分及定义严格保留；
  - **安装与分发原则**（第 37–42、99–105 行）：Python 3.11+ 要求、公开安装器、`--target` 参数保留、独立 bootstrap/Cursor hook 脱离源码仓库运行要求完整保留；
  - **Writer 所有权与职责**（第 29、67–68、135 行）：明确 writer 只处理确定性结构事实、不生成方案语义、目录迁移仅在 `finalize_plan` 校验后执行；
  - **Verifier 边界与 MCP 试点**（第 121–126 行）：Verifier 不默认安装/运行，Protocol §6 边界保留；repo-local MCP server（`sopify_mcp_server.py`）事实提供者角色、Codex 持久注册与 Claude 会话级只读证据边界完整保留；
  - **底层哲学与收敛链**（第 43–56 行）：`Convergence-first`（produce → verify → record evidence → settle）、`Wire-composable`、`Surface-shared` 三大核心哲学完整保留；
  - **预算与硬约束**（第 75–84、131–138 行）：Checkpoint 2 种（clarification/decision）、required_host_action 5 项、Core state files 2 份（`active_plan` / `current_handoff`）硬上限保持，develop_mode hint 性质、archive 状态不进 host_action 等约束严格保留。
- **核查结论**：**零丢失现行决策**。删减均为已退场历史与重复文本，蓝图骨干更加聚焦有力。

---

### 2. `protocol.md` Normative 章节完整性核对

- **§6 Verifier（外部工具与证据）**：
  - Normative 规则（Evidence schema、Write boundaries、Verdict 状态语义）100% 完整保留；
  - 删除冗余的 Runtime 模式映射列；
  - 将已退场的 EAR（ExecutionAuthorizationReceipt）折叠块替换为单句归档说明：
    > *“执行前 EAR 已退场，现行主链使用过程 receipts 与 history receipt；旧字段及决策见 [ADR-017] 和 [P8 归档设计]。”*
- **§7 Subject Identity & Review Wire Contract**：
  - Normative 规则（Subject Identity、Bound-Subject Binding、Action Applicability Matrix）100% 完整保留，字句未改；
  - Informative 实现映射去除了旧 state 细节，提炼为一句话指向 `sopify_writer` 与方案包。
- **§8 Host Protocol Entry Contract**：
  - §8.1 四步入口序列、§8.2 规范入口点、§8.3 Ingress 验证序列、§8.4 协议准入、§8.5 会话与状态模型、§8.6 Checkpoint 处理、§8.7 Finalize 序列、§8.8 状态缺失降级规则、§8.9 required_host_action 枚举、§8.11 ActionProposal 角色声明全部完整保留；
  - §8.10 退场说明压缩为一句指向 P8 归档。
- **核查结论**：**规范语义 100% 完整保留**，退场内容严格收缩为单句加链接。

---

### 3. 被删文件失效引用扫描（7 个已删文件）

在隔离工作区对全仓文件执行 `git grep` 完整排查被删的 7 个文件/符号：
1. `sopify_writer/_resume.py`
2. `scripts/w33_qoder_proof.py`
3. `scripts/check-enhancement-declaration.py`
4. `scripts/sync-skills.sh`
5. `.sopify/blueprint/skill-standards-refactor.md`
6. `docs/dev/development-guidelines.md`
7. `examples/external-repo-quickstart/sopify.json.example`

- **排查结果统计**：
  - **活动源码 / 安装器 / CLI / 测试**：**0 处命中**；
  - **活动文档（README、CONTRIBUTING、docs/ 等）**：**0 处命中**；
  - **蓝图索引（blueprint/README.md）**：已修复，指向现有文档，**0 处失效命中**；
  - **命中保留处**：全部位于受保护的历史与归档文档（`.sopify/history/`、`.sopify/plan/`、`architecture-decision-records/`）以及 `CHANGELOG.md` 的迁移说明中。
- **核查结论**：**无任何失效引用**。

---

### 4. 文档合并与发布流程唯一性

- **CONTRIBUTING 中英文双语对齐**：
  - `CONTRIBUTING.md`：74 行；
  - `CONTRIBUTING_CN.md`：74 行；
  - 结构、段落、示例命令完全 1:1 镜像对称，已纳入短生命周期分支、单文件预览命令、MCP 试点指引，删除了旧 guidelines 的重复长篇说教。
- **`docs/dev/release-process.md` 发版步骤唯一步骤源**：
  - 全文 89 行（由原 193 行精简）；
  - CONTRIBUTING 中发版步骤唯一链接到 `release-process.md`；
  - 经逐条核对，文中提及的 6 个脚本工具（`release-preflight.sh`、`check-version-consistency.sh`、`release-sync.sh`、`render-release-installers.py`、`check-readme-links.py`、`check-install-payload-bundle-smoke.py`）全部真实存在且执行无误；
  - 删除了不存在的“eval gate”说明，严格区分了本地源码 smoke 与正式 release assets 远端 smoke。
- **核查结论**：**合并质量极高，中英文一致，发版步骤真实可行**。

---

### 5. 隔离 Worktree 全量自动化测试与验证

在独立 worktree（`/private/tmp/.../t4-accept-wt`）中，设置 `PYTHONDONTWRITEBYTECODE=1`、`PYTEST_ADDOPTS="-p no:cacheprovider"`，使用 Python 3.11 执行：

1. **Pytest 全量套件**：
   ```bash
   python3 -m pytest tests -q
   ```
   **结果**：`386 passed, 97 subtests passed in 31.19s`（退出码 0）。
2. **Release Preflight 完整门禁**：
   ```bash
   bash scripts/release-preflight.sh
   ```
   **结果**：
   - 版本一致性检查通过（Version: 2026-08-30.001152）；
   - Golden 镜像快照检查：`24 passed in 0.20s`；
   - Builtin catalog drift 检查：通过；
   - 全量回归测试：`386 passed, 97 subtests passed in 33.93s`；
   - 5 个协议 Smoke（new-plan、continuation、clarification pending、decision pending、finalize）：全部 `PASS`；
   - Install/payload bootstrap smoke：`passed`；
   - 最终输出：`[release-preflight] All checks passed.`（退出码 0）。
3. **文档与代码规范检查**：
   - `python3 scripts/check-readme-links.py`：`README validation passed`（退出码 0）；
   - `git diff --check a9f6825..8285888`：完全为空（无空白或格式异常，退出码 0）。
- **核查结论**：**全量门禁 100% 绿灯**。

---

### 6. T6 接入指南（`docs/host-onboarding.md`）修订复核

对照 `t6-accept-gemini.md` 提出的 4 项最小修改建议逐条核验：

| 验收项 | 要求 | `docs/host-onboarding.md` 实测落地情况 | 判定 |
|---|---|---|:---:|
| **1. 重排时序** | 将测试模板调至代码接入之后 | 章节顺序重排为：`§1 矩阵 -> §2 探针选布局 -> §3 代码接入与注册 -> §4 测试与会话检查 -> §5 证据包 -> §6 负向边界 -> §7 DoD`。时序自然顺畅。 | **已落实** |
| **2. 精简认证** | 删除 PROTOCOL_VERIFIED 8 条展开 | 第 88–90 行收缩为一句原则声明加 `protocol.md` 外链，完全删除 8 项超纲展开。 | **已落实** |
| **3. 3 种 Surface 说明** | 明确 `header_embedded` / `single_file` / `user_plugin` 场景 | 第 57–71 行详细补充了三种 surface 的适用特征与典型宿主对照（Claude/Codex、Copilot、Cursor）。 | **已落实** |
| **4. 工具与脚本细节** | 澄清提问工具边界、注明 catalog 脚本 | 第 21 行明确注明提问工具“This is a probe observation only; a baseline adapter needs no Python code for it”；第 79 行补齐 `python3 scripts/generate-builtin-catalog.py` 完整路径。 | **已落实** |
| **篇幅控制** | 目标 150 ~ 170 行 | 当前全长 **172 行**（原 222 行，精简 50 行 / 23%），高度凝练。 | **已落实** |

- **核查结论**：**4 项修改全部扎实落实**。

---

### 7. 统一验收标准核查（5 项）

1. **不过度设计**：通过。中等档清理删减 2,292 行，未引入任何新机制；
2. **符合设计规范**：通过。Protocol 协议规范完好，模块依赖干净；
3. **不冗余**：通过。消除了 blueprint 和 protocol 之间的重叠，发版流程统一归口至 `release-process.md`；
4. **与其他宿主整体一致**：通过。各宿主 prompt、skill 及接入模板统一遵循 `host-onboarding.md`；
5. **不增加用户心智负担**：通过。对外只保留清晰的替代预览命令 `render-host-skills.py --output`，移除了内部临时试点脚本。

---

## 三、作为使用者的真实体验与摩擦（Dogfooding 反思）

在经历了前置的多轮探针（T7 Step 1 & Step 2），并在此次独立 worktree 中完成 T4/T6 完整验收后，分享三点真实体验：

1. **独立 Git Worktree 隔离策略极大地解除了“只读验收者”的心理负担**：
   - 之前在主工作区进行测试与审计时，必须时刻担心 `pytest` 或 `python3` 产生 `__pycache__` 导致破坏正在并行修改代码的 Codex 工作区。
   - 本次通过 `git worktree add $SP/t4-accept-wt 8285888` 建立独立隔离环境，运行全量 386 个测试和发布 preflight 时完全无需顾虑主工作区的冲突，测试结束直接 `git worktree remove`，整个流程清爽、安全且可重复。建议将 Worktree 隔离作为今后多 Agent 并行验收的标准化范式。
2. **`docs/host-onboarding.md` 修订后可用性大幅提升**：
   - 在刚完成的 T7 探针任务中，我实际使用了这版指南：从“先探针确定全局/项目规则优先级”，到“验证 Skill 发现层级限制”，再到“三事实模型（Installed / Sees it / Follows it）”，整体逻辑非常顺滑。
   - 特别是第 57–71 行新增的 3 种 instruction surface 说明，在做 Antigravity 选型时直接指导了我选择 `header_embedded`，免去了反复翻阅 `base.py` 源码的时间。
3. **蓝图大瘦身使得架构文档重新具备“可阅读性”**：
   - 过去 `design.md` 超过 700 行，里面夹杂着大量早先已废弃的 P8 架构表格和历史对比，新接入者在阅读时很难分清哪些是当前仍在生效的规则，哪些是早已作废的历史参考。
   - 瘦身至 149 行后，模块职责、边界硬约束、核心哲学与目录分层一目了然，协议细节精准引用到 `protocol.md`，文档维护成本和阅读心智负担显著降低。
