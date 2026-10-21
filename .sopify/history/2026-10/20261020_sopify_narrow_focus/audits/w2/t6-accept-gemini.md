# T6 宿主接入 Recipe（`docs/host-onboarding.md`）独立验收报告

**验收者**：验收官（Antigravity / Gemini），同时作为 T7 Antigravity CLI 接入任务的第一执行者  
**验收对象**：`/Users/weixin.li/code/github/sopify/docs/host-onboarding.md`（Trae 撰写，未提交状态，全长 222 行）  
**参考基准**：
- 方案：`.sopify/plan/20261020_sopify_narrow_focus/plan.md`（统一验收标准）、`tasks.md`（T6、T7 定义）
- 报告参考：`t6-trae.md`
- 关联代码与规范：`docs/cursor-host.md`、`installer/models.py`、`installer/hosts/`

---

## 一、综合结论与修改建议

### **验收裁决：【有条件通过】**

**总体评价**：
文档整体框架清晰，严格贯彻了克制、防过度设计与务实的工程风格。核心亮点包括：
1. **三事实模型**（`Installed` -> `Host sees it` -> `Host follows it`）直击过往宿主接入时“把文件存在当做功能生效”的顽疾；
2. **严守负面边界**（严禁修改账号、代理、模型、settings、trust，baseline 不碰 hooks/MCP）；
3. **支持档位克制**（新宿主严格从 `BASELINE_SUPPORTED` 起步，`declared_enhancements` 留空）。

但文档在**面向新执行者（T7）的实操时序感**、**已有 surface 概念的直观解释**、以及**部分超纲内容的冗余度**上存在改进空间。

- **建议目标篇幅**：从当前 **222 行** 压缩至 **150 ~ 170 行**（精简约 25% ~ 30%）。
- **最小修改清单（4 项）**：
  1. **重排执行章节的时序**：将当前的 `§6 Minimum test template` 调整到 `§7 Code map` 之后，理顺“探针矩阵 -> 选定布局 -> 代码接入与公共注册 -> 自动化测试与真实会话验收 -> 证据交付”的自然施工流；
  2. **精简 PROTOCOL_VERIFIED 展开内容**：删除 §5 中对 Protocol Verified 8 条具体断言的冗余铺陈，缩减为 1~2 句话加外链至 `docs/blueprint/protocol.md`，聚焦 Baseline 主线；
  3. **补充 3 种既有 instruction surface 的简明指引**：在 §7 用 1~2 句话点明 `header_embedded`（共享规则追加块+复制 skills 树）、`single_file`（单文件平铺内联）、`user_plugin`（独立规则+全局 skill 树）的适用特征，避免读者必须通读 `base.py` 才能选型；
  4. **明确提问工具与生成脚本细节**：明确指出提问工具仅作为探针观察宿主行为，baseline 无需编写 Python 代码适配；在 §7 表格中补充 catalog 生成脚本路径 `python3 scripts/generate-builtin-catalog.py`。

---

## 二、能不能照着用（以 T7 Antigravity 接入者视角实测）

假设当前立即开始执行 T7（将 Antigravity CLI 接入 Sopify）：

### 2.1 第一步做什么、确认哪些事、怎么判断通过？
- **第一步非常清晰**：
  - 不得盲目复制代码，首先建立隔离测试工作区，并记录宿主精确版本（`agy --version`）与 Sopify 候选 commit SHA。
  - 放置唯一探针标记（unique markers），启动全新会话测试宿主加载。
- **确认事项明确**：
  - §1 能力矩阵清晰指导了 6 个关键维度：全局规则路径、项目规则路径、Skill 发现（目录、嵌套、description 上限）、提问工具、持久化与重启要求、缺席降级路径。
- **通过判据严谨**：
  - 明确要求三事实独立取证：文件已安装并匹配 hash（事实 1）、宿主在新会话中 quote 标记（事实 2）、宿主在确定性任务中实际执行动作或触发 tool call（事实 3）。

### 2.2 读者卡住或含糊的地方（摩擦点）

1. **时序倒置与阅读认知断层**：
   - 现章节顺序为：`§1 矩阵 -> §2 探针 -> §3 边界 -> §4 证据字段 -> §5 档位 -> §6 测试模板(含 7 个会话检查) -> §7 代码图谱 -> §8 漂移检查 -> §9 DoD`。
   - 读者在读完 §2 探针并选定布局后，跳到 §6 看到“Real-session checks”要求测试 `~go plan`、`Analyze` 跑分脚本等。但此时宿主适配器代码还根本没有编写，Sopify 根本还没安装进去！代码图谱（Code map）却被放在了后面的 §7。这导致实操流线前后颠倒，贡献者必须前后翻跳。
2. **已有三种 `instruction surface` 的选型缺乏说明**：
   - §7 表格开头提到：`Prefer reusing one of the existing instruction surfaces ('header_embedded', 'single_file', 'user_plugin') before adding a new one.`
   - 但文档全文没有解释这三种 surface 分别适合什么场景。对 Antigravity CLI 这种拥有全局 rules（如 `GEMINI.md` 或配置）和 skills 目录的宿主，到底该用哪一个？如果读者不直接去翻 `installer/hosts/base.py` 的源码实现，单看本文档会不知道该选哪个。
3. **“向用户提问”能力的落地边界模糊**：
   - §1 提到：“Does the host expose a structured question tool? What is its tool name? What is the plain-text fallback?”
   - Antigravity 实际具备 `ask_question` 交互式结构化提问工具。初次阅读的贡献者容易困惑：“我是否需要在 `installer/hosts/antigravity.py` 中写 Python 代码去对接或代理 `ask_question` 工具？”实际上 baseline 只需确认宿主自身是否能提问即可，无须代码侵入。文档应明确澄清这一负向边界。
4. **探针文件名的策略提示缺失**：
   - §2 说“Seed candidate files with unique markers: one global rule, one project rule, and one Skill.”
   - 对于新宿主，如果能顺带给出业界常见规则文件名列表（如 `AGENTS.md`、`INSTRUCTIONS.md`、`<HOST>.md`），贡献者在探针阶段能少走很多盲测弯路。

---

## 三、用户统一验收标准逐条判定

依据用户 2026-10-20 提出的 5 项统一验收标准逐项裁定：

### 3.1 不过度设计：【通过】
- **核对标准**：没有为未发生的场景预建机制、表或配置。
- **证据**：
  - 文档明确定位为工作清单（checklist），坚决拒绝新造编辑器、CLI、运行时、配置文件或 Hook schema；
  - 强制新宿主从 `BASELINE_SUPPORTED` 起步，`declared_enhancements` 必须留空；
  - 严格依托现有已测试的安装器基础设施（`install.sh`、`sopify_doctor.py`、`release-preflight.sh`）。

### 3.2 符合设计规范：【通过】
- **核对标准**：沿用仓库已有的模块边界与命名，不跨模块引用私有实现；术语与既有规范对齐。
- **证据**：
  - 文中涉及的模型与枚举全部与 `installer/models.py` 严格一致（`SupportTier.BASELINE_SUPPORTED`、`EntryMode.PROMPT_ONLY`、`FeatureId`、`HostCapability`）；
  - 规范继承了 `docs/cursor-host.md` 的三事实模型与证据包要求；
  - 强调了共享 home 必须复用公开的 `installer.bootstrap_workspace.upsert_managed_instruction_block`，严禁宿主适配器引入私有 helper。

### 3.3 不冗余：【有条件通过 / 需瘦身】
- **核对标准**：同一能力只有一份实现；文档同一事实只写一处；篇幅适度（当前 222 行）。
- **审查与删减建议**：
  - **冗余 1（超纲展开协议认证）**：§5（行 119-125）花了大量篇幅详细罗列升级到 `PROTOCOL_VERIFIED` 的 8 个要求。文档第 3-4 行明确指出“目标是可重复的 BASELINE_SUPPORTED，而非完整协议认证”。此处详述与目标脱节，且与 `blueprint/protocol.md` 重复，建议压缩为一句原则说明并挂链接。
  - **冗余 2（测试列表重复）**：§6 Automated tests 列了 6 个测试文件，§7 Code map 表格底行又再次列出测试文件。建议将两处测试合并表述。
  - **冗余 3（漂移检查重复）**：§8 的反复强调（“不要把路径存在当通过”）与 §2、§6、§9 高度重合，可精简并入 DoD。
  - **篇幅裁定**：当前 222 行略显冗长，精简至 **150~170 行**将极大提升贡献者的阅读效率。

### 3.4 与其他宿主整体一致：【通过】
- **核对标准**：同类行为（managed block、安装、Doctor、文案）在各宿主之间语义一致。
- **证据**：
  - 全面贯彻受管块机制，严禁整文件覆盖；
  - 明确日常问答和小修直来直去（keep direct），严禁强制进入流程；
  - Doctor 检查要求严格分离安装静态检查与运行时黑盒行为。

### 3.5 不增加用户心智负担：【通过】
- **核对标准**：读者是贡献者，不是最终用户；不引入额外的心智负担。
- **证据**：
  - 文档开篇定义明确；
  - 流程严格基于贡献者已知的 Git、pytest、Doctor 等标准工作流，没有引入自定义的 compliance DSL 或复杂脚本。

---

## 四、事实核对（代码位置、档位、Doctor 行为）

逐条核对文档提及的代码事实：

| 文档陈述项 | 源码实际核对 | 结论 | 说明 |
| :--- | :--- | :---: | :--- |
| `SupportTier.BASELINE_SUPPORTED` | `installer/models.py` | **完全一致** | 枚举值 `baseline_supported` |
| `EntryMode.PROMPT_ONLY` / `HOOKS` | `installer/models.py` | **完全一致** | 存在该枚举 |
| `HostCapability` 字段名 | `installer/models.py` | **完全一致** | `declared_features`, `verified_features` 等 |
| `installer/hosts/__init__.py` 中 `_REGISTRATIONS` | `installer/hosts/__init__.py:17` | **完全一致** | 宿主全局注册表字典 |
| `skills/hosts.yaml` | 存在该文件 | **完全一致** | 供 `render-host-skills.py` 消费 |
| `installer/distribution.py` 中 `_host_display_name` | `installer/distribution.py:900` | **完全一致** | 宿主产品显示名转换函数 |
| `installer/inspection.py` 中 Doctor 检查 | `installer/inspection.py:321, 836` | **完全一致** | 区分 `_present` 与 `_behavior` |
| `BLACK_BOX_NOT_VERIFIED` 状态码 | `installer/inspection.py:817` | **完全一致** | 行为未验证时的官方跳过码 |
| `scripts/sopify_doctor.py --format json --home-root` | `scripts/sopify_doctor.py` | **完全一致** | 参数完全受支持 |
| `upsert_managed_instruction_block` | `installer/bootstrap_workspace.py` | **完全一致** | 公开函数签名一致 |
| `skill_tree_matches` | `installer/hosts/base.py:378` | **完全一致** | W1 返工后公开的树比对函数 |
| `skills/catalog/*/skill.yaml` | `skills/catalog/` | **完全一致** | 存在 5 个内置技能目录 |
| *小瑕疵 1*：生成 catalog 脚本名未提 | `scripts/generate-builtin-catalog.py` | **微小瑕疵** | 文中只说 existing generator，应写明脚本名 |
| *小瑕疵 2*：YAML 与 Python 中 single_file 命名 | `skills/hosts.yaml:25` | **微小瑕疵** | Copilot 在 yaml 里叫 `copilot_instructions_md`，Python 里叫 `single_file`，建议备注避免混淆 |

---

## 五、作为使用者的真实体验与摩擦（Dogfooding 反思）

在作为验收官经历了 R1（四方审计）、R2（Antigravity 探针）、R3（冗余盘点）、R5（README 诊断）、R7（方案审计）、Tagline 标语优化、W1 全量测试/迁移实测以及本轮 T6 验收后，以下为我在真实使用 Sopify 及多 Agent 协作工作流中切身体会到的摩擦与真实建议：

### 1. 任务包信息高度碎片化，跨 4~5 个文件拼凑上下文成本高
- **真实摩擦**：协调员派单时在 Orca prompt 里给出简要描述，指向 `/private/tmp/.../scratchpad/audit/task-*.md`；核心方案与验收基准在 `.sopify/plan/.../plan.md` 和 `tasks.md`；前置执行官报告在 `w1-codex.md`、`w1-fix-codex.md`，还有证据目录 `w1-evidence/`、`w1-fix-evidence/`。
- **痛点**：每次接到任务，我作为一个独立的 worker，第一件事必须像拼图一样，在 5 个不同路径的文件间来回穿梭核对，经常需要反复 grep 和跨文件查找当前派发的最新基线是什么。
- **建议**：Sopify × Orca 规范（T5）应推行**自包含的 Task Packet 规范**。在任务单顶部给出唯一的绝对输入清单（任务目标、本轮基线 commit SHA、必须参照的文档路径、写集白名单、验收命令），不再让 worker 在各种 scratchpad 历史文件中盲人摸象。

### 2. 「统一验收标准」与方案「完成定义 (DoD)」存在平行重合与双重对账
- **真实摩擦**：在 W1 验收中，`tasks.md` 给出了一套 T1/T2 的详细 DoD（全量测试通过、迁移矩阵覆盖等）；而用户又提出了 5 条通用的「统一验收标准」（不过度设计、符合规范、不冗余、跨宿主一致、不增加心智负担）。
- **痛点**：这两套标准在多个维度上高度重合（例如“不过度设计/不冗余”与“删除首轮多余哈希字典”、“不增加心智负担”与“卸载指南简明化”）。这导致验收官在撰写报告时，同一件事要在 DoD 里写一遍证明，又在统一标准里换个角度再写一遍证明，极大地增加了文档维护负担。
- **建议**：在方案层面将「统一验收标准」作为所有任务共用的元规则（Meta-rules），拆解子任务时直接将它们融入任务的验收项，避免建立平行平级的两套打分体系。

### 3. 返工（Rework）场景下交付物缺乏“单一真相源（SSOT）”
- **真实摩擦**：W1 执行中，Codex 第一轮产出了 `w1-codex.md`（81 个测试），返工后又产出了 `w1-fix-codex.md`（44 个测试）。两个报告并存在同级目录下，且内容都非常详尽。
- **痛点**：验收官介入时，必须极其小心地区分哪条证据来自首轮、哪条来自返工，一旦看错文件就会采纳被废弃的旧数据。
- **建议**：返工交付物应覆盖更新原报告，或在首轮报告顶部强制添加 `> [!WARNING] 本报告已被 w1-fix-codex.md 替代` 的显式废弃横幅。

### 4. 共享工作区中只读任务的“防污染”心理负担过重
- **真实摩擦**：本任务特别提醒：“同一工作区里 Codex 正在修改 `skills/**` 和 installer，不要动”。
- **痛点**：验收官在执行必要的只读验证（如复跑全量 pytest、运行探针脚本）时，Python 和 Pytest 默认会生成 `__pycache__` 或 `.pytest_cache`，甚至某些脚本会误触 git index。我必须时刻提防命令产生副作用，每次操作后都要反复运行 `git status` 确保没有任何未暂存文件被污染。
- **建议**：在多 agent 并行协作时，协调员应优先利用 Git worktree 建立隔离分支工作区，或者在测试脚本中默认配置环境变量（`PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider"`），从根本上消除相互踩脚的隐患。

### 5. 临时目录 `/tmp/` 与“方案证据存进仓库”核心承诺的反差
- **真实摩擦**：Sopify 对外宣传最核心的价值就是“方案与验收证据存进仓库，跟着 Git 走”。但实际上，我们在过去几轮所有严肃的审计报告（R1-R7、Tagline、W1 验收实测证据、T6 验收等）全都被存放在 `/private/tmp/claude-503/.../scratchpad/audit/` 下！
- **痛点**：这些在临时目录下的报告一旦遇到机器重启或会话过期就会彻底蒸发。真正留在仓库 `.sopify/` 里的，除了 `plan.md` 和 `tasks.md` 外，几乎没有具体的测试与验收回执。
- **建议**：Sopify 自身的方案流应该“真正 dogfood 自己的承诺”：在任务验收通过后，由大脑统一把 scratchpad 中的关键验证报告或其 SHA 指纹回填/归档到 `.sopify/history/` 或 `receipts/` 中，让严肃的研发闭环证据真正“留在仓库里”。
