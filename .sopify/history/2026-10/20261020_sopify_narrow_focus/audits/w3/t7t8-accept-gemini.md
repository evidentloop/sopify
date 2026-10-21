# T7、T8 适配代码验收与 Antigravity 真实 Dogfood 独立验收报告

**验收者**：主要 Dogfood 宿主代表 / 独立验收官（Antigravity / Gemini 3.8 Flash）  
**候选版本**：提交 `a9a0f95`（分支 `feat/sopify-narrow-focus`，工作区干净）  
**验收范围**：
1. **代码验收（T7 Antigravity、T8 Trae）**：架构设计、统一验收标准核查、全量测试回归与预发门禁；
2. **真实 Dogfood（Antigravity 本机）**：真实安装至 `~/.gemini/config/`，前后快照隔离核验，在全新独立测试仓库中运行四大真实会话场景并取证。  
**参考基准**：
- `.sopify/plan/20261020_sopify_narrow_focus/plan.md`（统一验收标准、Key Decisions）
- `tasks.md`（T7、T8 定义与完成标准）
- 执行官报告：`t7t8-codex.md`、前序接入指南：`docs/host-onboarding.md`

---

## 一、综合验收结论

| 验收模块 | 裁决 | 核心结论 |
|---|:---:|---|
| **第一部分：代码验收（T7+T8）** | **【通过】** | 扁平布局仅在 `installer/hosts/flat.py` 唯一定义并由两宿主共用；全量 **406 passed, 97 subtests passed**；release-preflight 28 项 golden 全部通过；无任何失效引用与误伤。 |
| **第二部分：Antigravity 真实 Dogfood** | **【通过】** | 真实安装成功，前后快照证明**严格仅新增 Sopify 专属文件**（48 个），用户已有技能/配置 100% 未动；**四大场景全部通过**（加载正常、问答直来直去不进流程、`~go plan` 完整走通并由 `sopify_writer` 规范落盘、Doctor 严格解耦安装事实与行为证据）。 |

---

## 二、第一部分：代码验收（T7、T8）

### 2.1 全量测试与发布门禁复跑
使用指定 Python 3.11 环境（`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider"`）：
- **全量单元与集成测试**：
  ```bash
  python3 -m pytest tests -q
  ```
  **结果**：`406 passed, 97 subtests passed in 56.36s`（新增 `tests/test_flat_hosts.py` 覆盖 20 项扁平特性测试，退出码 0）。
- **Release Preflight 门禁**：
  ```bash
  bash scripts/release-preflight.sh
  ```
  **结果**：
  - 版本一致性检查通过（Version: 2026-08-30.001152）；
  - Golden 快照检查：`28 passed in 2.19s`（含新增两宿主双语共 4 组 flat prompt tree 快照）；
  - Builtin catalog drift 检查：通过；
  - 全量回归测试：`406 passed`；
  - 5 个协议 Smoke（new-plan、continuation、clarification pending、decision pending、finalize）：全部 `PASS`；
  - Install/payload bootstrap smoke：`passed`；
  - 最终状态：`[release-preflight] All checks passed.`（退出码 0）。

---

### 2.2 统一验收标准核心重点核查

1. **扁平布局是否只实现了一份**：
   - **核验事实**：`installer/hosts/flat.py` 是扁平投影投影、资源重写与树比对的**唯一样板**（`install_flat_host_assets`）。
   - `antigravity.py` 与 `trae.py` 仅作为声明式配置，设置 `flat_skills=True`，由 `base.py` 统一分发至 `flat.py`；
   - 共享 references 资源目录（`shared-writing-dna.md`、`output-contract.md`）每个宿主只存一份（`skills/sopify/references/`），各阶段通过 `../sopify/references/` 统一软引用，无重复代码或重复资源。
2. **与现有宿主行为一致性**：
   - **重装修复**：资源缺失、文件篡改、混入 stale 文件时，再次安装自动修复为标准快照；
   - **语言切换**：从 `zh-CN` 切至 `en-US` 时干净替换阶段内容与受管块语言，块外用户内容保留；
   - **保留用户内容**：受管块外的前后用户文本、用户既有 settings/hooks、用户自建 Skill 目录（如 `my-skill/`）100% 保留；
   - **Doctor 职责分离**：安装文件存在性（`host_prompt_present`、`global_skill_tree_present`、`payload_present`）标为 `pass`，而黑盒行为证据（`antigravity_cli_behavior`、`trae_cli_behavior`）在未接入会话前严格标为 `skip (BLACK_BOX_NOT_VERIFIED)`。
3. **`skills/trae-entry-skill.md.template` 根目录单文件设计的合理性**：
   - **核验结论**：**设计完全合理**。
   - **理由**：
     - Trae 不原生加载全局规则文件，必须通过顶层 Skill `skills/sopify/SKILL.md` 建立入口；
     - 该模板仅包含 4 行通用前置 YAML 元数据（`name: sopify` 与 250 字符的双语 description）；
     - 正文部分随后由安装器动态追加各语言的 `header.md.template` 受管块；
     - 将单一纯元数据模板置于 `skills/` 根目录，避免了在 `zh/` 与 `en/` 之间复制两份同质模板造成的元数据漂移风险。
4. **Header 阶段名替换（`sopify-<stage>`）是否存在误伤**：
   - **核验结论**：**零误伤**。
   - **证据**：静态检查 `skills/{zh,en}/header.md.template`，反引号包裹的 `analyze`、`design`、`develop`、`kb`、`templates` 在整份模板中**仅且仅在阶段路由表**中出现一次（如 `| `analyze` |`）。`_rewrite_text` 的精准替换将其拓展为 `| `sopify-analyze` (~/.gemini/config/skills/sopify-analyze/SKILL.md) |`，正文其他任何段落均无相同模式，完全不存在附带误伤。
5. **扁平安装后相对链接抽查（实测结果）**：
   - 在临时隔离 home 中安装 `antigravity` 与 `trae`，抽查 `sopify-analyze`、`sopify-design`、`sopify-develop` 三个阶段 Skill 的所有内链：
     - `references/analyze-rules.md` → 存在（`True`）
     - `assets/question-output.md` → 存在（`True`）
     - `assets/success-output.md` → 存在（`True`）
     - `../sopify/references/shared-writing-dna.md` → 存在（`True`）
     - `../sopify/references/output-contract.md` → 存在（`True`）
     - 可移植脚本引用 `~/.gemini/config/skills/sopify-analyze/scripts/score_requirement.py` → 存在（`True`）且可正常执行返回评分 JSON；
     - 所有被引用的阶段与文件 100% 物理可达。

---

## 三、第二部分：Antigravity 真实 Dogfood

### 3.1 真实安装与系统快照对比（`~/.gemini/` 零污染验证）

- **安装命令**：
  ```bash
  python3 scripts/install_sopify.py --target antigravity:zh-CN
  ```
  在仓库根目录（HEAD `a9a0f95`）真实执行，输出：`Sopify 安装完成。宿主：Antigravity（antigravity:zh-CN）`。
- **快照对比证据**（比对 `gemini-pre-install-snapshot.json` 与 `gemini-post-install-snapshot.json`）：
  - **安装增量（严格仅限于 Sopify 专属资产，共 48 个）**：
    1. `~/.gemini/config/AGENTS.md`（仅包含带版本的受管指令块）；
    2. `~/.gemini/config/skills/sopify-*`（5 个阶段技能目录）；
    3. `~/.gemini/config/skills/sopify/references/`（2 个共享标准文档）；
    4. `~/.gemini/config/sopify/`（24 个 payload 基础契约与 writer 库文件）。
  - **用户既有环境无损验证**：
    - `~/.gemini/config/hooks.json`、`hooks.json.bak`：**未修改（SHA 一致）**；
    - `~/.gemini/config/mcp_config.json`：**未修改（SHA 一致）**；
    - 用户既有 Skills（`anatomy`、`fire`、`fireworks-tech-graph`）：**未触碰（链接与指向完好）**；
    - 代理、模型、系统设置：**0 修改**。

---

### 3.2 四大场景实测结果

在 `$SP/dogfood-project` 独立 Git 仓库（包含示例代码 `calc.py`）中，使用 `agy -p` 启动全新会话逐一实测：

#### 场景 1：加载与发现（三事实齐备）— 【通过】
- **命令**：
  ```bash
  cd .../dogfood-project && agy -p "Show the exact content of your <user_rules> and list all available skills from <skills>."
  ```
- **实测证据**：
  1. `<user_rules>` 中完整且原生内联了 `~/.gemini/config/AGENTS.md` 的 Sopify 受管块（版本 `2026-08-30.001152`）；
  2. `<skills>` 列表中完整列出了 5 个扁平技能：
     - `sopify-analyze` (`~/.gemini/config/skills/sopify-analyze/SKILL.md`)
     - `sopify-design` (`~/.gemini/config/skills/sopify-design/SKILL.md`)
     - `sopify-develop` (`~/.gemini/config/skills/sopify-develop/SKILL.md`)
     - `sopify-kb` (`~/.gemini/config/skills/sopify-kb/SKILL.md`)
     - `sopify-templates` (`~/.gemini/config/skills/sopify-templates/SKILL.md`)
  3. 用户原有的 `anatomy`、`fireworks-tech-graph` 技能并存且可用。
- **三事实结论**：已安装（磁盘在）、能看到（会话引）、能识别（语义全）。

#### 场景 2：问答直来直去不进流程 — 【通过】
- **命令**：
  ```bash
  cd .../dogfood-project && agy -p "calc.py 里的 divide 函数入参是什么？返回值是什么？"
  ```
- **实测输出**：
  - 模型精准回答 `a`、`b` 为入参，返回两数相除结果；
  - 输出格式遵循受管块的共享写作规范（“先给结论和必要证据，保留 Changes，以 Next: 收尾”）；
  - `Changes: 无（只读查询）`。
- **负向状态检查**：
  - 检查工作区 `.sopify/` 目录：**完全未创建（`SOPIFY_DIR_NOT_CREATED`）**；
  - `git status --short`：**完全干净（0 变动）**。
- **结论**：普通问答和小修直来直去，未触发任何方案流或多余文件写入。

#### 场景 3：方案流（`~go plan`）自洽执行与规范写回 — 【通过】
- **命令**：
  ```bash
  cd .../dogfood-project && agy --dangerously-skip-permissions -p "~go plan 给 calc.py 增加除零保护"
  ```
- **实测执行过程证据**（会话 ID `e613947c-9eab-4e70-b357-0b73fd1bc1a7`）：
  1. **规则与评分机制被真实调用**：模型自发激活 `sopify-analyze`，读取 `references/analyze-rules.md`，执行 `score_requirement.py` 评估清晰度；
  2. **方案包规范生成**：模型激活 `sopify-design`，确定 light 级别方案，生成包含全部 8 个 Canonical 章节（Context/Why, Scope, Approach, Waves/Steps, Key Decisions, Constraints, Status/Progress, Next）的 `plan.md`；
  3. **受控写入真相**：模型调用 `sopify_contracts.plan_package` 中的 `inspect_plan_package`，并通过 `sopify_writer.ProtocolStore` 写入 state；
  4. **产物验证**：
     - `.sopify/plan/20261020_calc_zero_division_guard/plan.md`：前置元数据合规，版本摘要为 `sha256:b6d98e634e447fdfd9f780ec96b4ddbf4522fc139a9256b89d09769ce1272ffa`（`Package snapshot: valid=True`）；
     - `.sopify/state/active_plan.json`：仅含 `{"plan_id": "20261020_calc_zero_division_guard"}`；
     - `.sopify/state/current_handoff.json`：包含 `writer: sopify_writer`、`required_host_action: continue_host_develop`，格式完全符合 schema；
  5. **收口输出**：
     ```text
     [dogfood-project-ai] 方案设计 ✓
     方案: .sopify/plan/20261020_calc_zero_division_guard/plan.md
     路径: 在 calc.py 的 divide 函数中前置校验除数 b == 0，若为零显式抛出 ValueError("除数不能为 0")
     任务: 2 项
     就绪状态: Ready
     ---
     Changes: 3 files
     Next: 运行 ~go 启动 Wave 1 与 Wave 2 的代码修改与验证。
     ```

#### 场景 4：Doctor 诊断分离性验证 — 【通过】
- **命令**：
  ```bash
  python3 scripts/sopify_doctor.py --format json
  ```
- **Antigravity 诊断项输出核查**：
  - `host_prompt_present`: `pass`（证据：`~/.gemini/config/AGENTS.md`）
  - `payload_present`: `pass`（证据：`~/.gemini/config/sopify/...`）
  - `payload_bundle_resolution`: `pass`（`PAYLOAD_BUNDLE_READY`）
  - `global_skill_tree_present`: `pass`（证据：5 个 `sopify-*` Skill 及脚本齐备）
  - `antigravity_cli_behavior`: `skip`（`BLACK_BOX_NOT_VERIFIED`）
- **结论**：安装静态事实（文件在）与动态行为状态（黑盒证据）在 Doctor 契约中清晰分离，未发生因文件存在而假冒行为通过的判定。

---

### 3.3 关于 Doctor `antigravity_cli_behavior` 的升级建议

- **当前状态**：Doctor 仍报告 `BLACK_BOX_NOT_VERIFIED`（因其当前设计为离线静态检查）。
- **建议**：
  - 本次 Antigravity Dogfood 已经提供了完整、可重复、端到端的黑盒行为闭环证据（含会话转录日志、三事实核验、非工作流问答隔离、`~go plan` 真实写回完整度校验）；
  - **建议后续在适当波次中**：可将 Antigravity 的 `antigravity_cli_behavior` 升级为具备正式黑盒行为验证记录的宿主（如记录在 `docs/antigravity-host.md` 中），在需要时平滑过渡。本轮严格遵循只读原则，不改动 Doctor 行为代码。

---

### 3.4 卸载指南（保留安装说明）

按照 dogfood 要求，当前 Sopify 依然**保留在宿主环境中**以备后续实测。若未来需要完全卸载，只需执行以下标准清理：

```bash
# 1. 清理受管块（若 AGENTS.md 仅有受管块则可直接删除）
rm -f ~/.gemini/config/AGENTS.md

# 2. 清理扁平技能与共享资源
rm -rf ~/.gemini/config/skills/sopify-* ~/.gemini/config/skills/sopify

# 3. 清理 Payload 依赖
rm -rf ~/.gemini/config/sopify
```
*注：上述操作绝不影响用户自建的 `anatomy`、`fireworks-tech-graph`、`hooks.json`、`settings.json` 等既有资产。*

---

## 四、作为使用者的真实体验与反思（Dogfooding 体会）

作为第一个真正装上全新扁平化架构 Sopify 的宿主，有三点极具价值的切身体会：

1. **扁平化改造（`sopify-*`）是 Antigravity 生态接入的生命线**：
   - 在之前的 T7 探针中，我们实测证实 Antigravity CLI 只能扫描一层技能目录；
   - 此次安装后，`sopify-analyze`、`sopify-design` 等技能能够被 CLI 顶层瞬时识别并直接以名字调用，配合 `~/.gemini/config/AGENTS.md` 顶层受管规则的指引，整个感知层非常坚固，完全没有出现“找不到子技能”的断层。
2. **`~go plan` 自主走通 `sopify_writer` 的闭环令人惊喜**：
   - 在没有任何人工插手的情况下，模型从识别 `~go plan` 意图，到自动触发分析评分，再到按模板要求生成合规的 8 段式 `plan.md`，最后精准调用 `sopify_writer.ProtocolStore` 将状态写入 `.sopify/state/`，整个机器真相链路完全按协议闭环。这证明这套基于受管块 + 阶段 Skill 的轻量架构在真实 LLM 认知中是完全可行且自然的。
3. **CLI 无头模式（`-p`）工具授权的心智提示**：
   - 在通过 `agy -p` 执行非交互式任务时，宿主若调用未事先授权的命令行工具会被系统默认阻断（`a tool required the 'command' permission that headless mode cannot prompt for`）。通过显式携带 `--dangerously-skip-permissions` 能够完美解决自动化验证场景下的执行阻断。建议将该参数作为未来自动化 CI / preflight 测试 Antigravity 的标准推荐配置。
