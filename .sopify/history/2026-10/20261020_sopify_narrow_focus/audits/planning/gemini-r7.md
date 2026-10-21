# Sopify R7 方案包审计报告：验收口径、交叉审计与决策完备度

**角色**：独立验收官（Antigravity）  
**被审对象**：
- `/Users/weixin.li/code/github/sopify/.sopify/plan/20261020_sopify_narrow_focus/plan.md`
- `/Users/weixin.li/code/github/sopify/.sopify/plan/20261020_sopify_narrow_focus/tasks.md`  
**依据材料**：`brain-audit-r3.md`、`analyze-v1.md`、`gemini-r3.md`、`gemini-r5.md`、`codex-r5.md`  
**报告输出路径**：`/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/gemini-r7.md`  
**审计日期**：2026-10-20  

---

## 一、验收口径与完成定义（DoD）对照核查

对照 `gemini-r3.md`（统一方案包验收标准）与 `gemini-r5.md`（README 诊断与新手测试），对 `tasks.md` 中各项任务的完成定义进行逐条闭环核验：

### 1.1 核心质量与契约任务（T1、T2、T5）
* **[认可] W1/T1 全量测试门（`tasks.md:9-12`）**
  * **核验**：完成定义要求“本地 `python3 -m pytest tests -q` 退出 0；CI 在 PR 实跑全量且为绿；preflight 遇 golden 漂移退出非 0 且不改 index”。完全闭环了 `gemini-r3` 的要求，同时切断了 preflight 自动 `git add` 掩盖语义漂移的暗道。
* **[认可] W1/T2 安装与 writer 修复（`tasks.md:13-17`）**
  * **核验**：完成定义要求“每个缺陷有修前失败、修后通过的测试证据；已有用户内容的 CLAUDE.md / AGENTS.md 重装保持不变；删掉阶段 Skill 重装复原；全量测试通过”。与 `gemini-r3` 的 DoD 完全一致，且覆盖了共享 home 文件的 managed block 写入保护。
* **[认可] W2/T5 Sopify × Orca 适配与 findings 模板（`tasks.md:28-31`）**
  * **核验**：完成定义要求“跑通一次大脑派单、执行实现、验收审查、大脑写 receipt；receipt 的 evidence 包含 Orca run/task/dispatch ID 和代码 SHA；writer schema 无变化”。严格恪守了“零运行时进程、不改核心 schema、worker_done 不等于 verify pass”的红线。

### 1.2 宿主与价值证明任务（T7、T8、T9）
* **[认可] W3/T7 & T8 新宿主 Baseline 适配（`tasks.md:39-46`）**
  * **核验**：定级严格限定为 `BASELINE_SUPPORTED`；T7 明确以验收官真实会话生效的 `~/.gemini/config/skills` 路径为准；T8 要求记录 trust 前后的行为差异；两项均不碰 hooks 与 MCP 自动注册。完全符合 R3 确立的克制原则。
* **[认可] W4/T9 冷启动跨宿主续做实测样本（`tasks.md:50-53`）**
  * **核验**：大脑开真实 pending 任务，Trae 全新会话只凭 `.sopify/` 接手，记录起止 SHA、plan_version 与文件读写，无论成败如实写入 release notes。这为 Sopify 最关键的“跨宿主可携带性”提供了决定性的真实验证链。

### 1.3 交付阶段任务的缺口排查（T10、T11）
* **[建议修改] W5/T10 README 与 Pages 验收口径缺口（`tasks.md:57-60`）**
  * **位置**：`tasks.md:60`（T10 完成定义）与 `plan.md:43`
  * **理由**：
    1. `plan.md:43` 与 `tasks.md:58` 均明确要求“Pages（`index.html` 与 `zh-CN.html`）同步事实与链接，保留布局”。但在 `tasks.md:60` 的最终完成定义中，仅写了 `check-readme-links 通过；中英文结构一致；标语在本任务开始时交用户选定`，**完全遗漏了对 Pages 的验收口径**！
    2. 如果缺乏 Pages 的明确检验项，容易导致执行者只改了 `README.md` 和 `README.zh-CN.md`，而把同等重要的官网首页（GitHub Pages）遗漏，造成线上产品定位割裂。
  * **最小修改建议**：
    在 `tasks.md:60` 完成定义中补齐 Pages 验收项：
    > “...中英文结构一致；**Pages（`index.html` / `zh-CN.html`）完成事实与 Hero 标语同步，全站链接检查退出码为 0**；标语按用户决策 D5 确定。”

---

## 二、分工与交叉审计矩阵防污染分析

在多 Agent 协同体系中，“谁产出、谁不验收”是防止自我验证偏差的基本原则。方案中设立的审计矩阵总体完备，但在 **Trae 的角色复用上存在严重的上下文污染风险**：

### 2.1 Trae 的多重角色冲突与“伪新手测试”风险
* **[建议修改] 角色防污染隔离（`plan.md:51` 与 `tasks.md:59`）**
  * **位置**：`plan.md:51` 及 `tasks.md:59`（T10 新手测试）
  * **理由**：
    方案中将 Trae 标签同时安排为：
    1. W3/T8 的 Trae 适配 dogfood 执行者；
    2. W4/T9 的冷启动接手执行者 B；
    3. W5/T10 的“新手测试全新 Agent”（要求其以完全没见过 Sopify 的新手视角冷读新 README 并答题）。
    **这存在致命的上下文污染（Contamination）**：
    * 当流程走到 W5 时，Trae 的会话历史和本地环境已经深刻经历了 T8 的安装调试与 T9 的方案读写！它的上下文早已被 `.sopify/`、`plan_version`、`sopify_writer` 等内部知识浸润。
    * 如果直接让带有历史记忆的同一个 Trae 实例去执行 T10 的“新手测试”，它根本无法扮演“一张白纸的新用户”，其对 README 5 问的回答必然带有后验偏见，无法真实暴露“新用户看不懂、装不上”的问题！
  * **最小修改建议**：
    在 `tasks.md:59` 中**增加物理级环境与上下文隔离前置条件**：
    > “新手测试：Trae **必须新开全新终端会话（执行 `traecli` 时不带任何历史上下文，清除记忆）**，并在**完全独立的空临时目录（如 `/tmp/fresh-sopify-onboarding/`）**中进行测试，确保其宿主环境未残留任何本项目的上下文，以此保证冷读与安装体验的绝对真实客观。”

---

## 三、待用户决策事项（Next D1–D4）的完备度审查

### 3.1 对既有 D1–D4 的评价
* **[认可] 既有决策项定位精准（`plan.md:94-99`）**
  * **理由**：D1（冗余删减档位）、D2（共享 home 文件的 managed block 写入与旧安装迁移）、D3（新宿主/T9 失败时不阻塞 release）、D4（执行期 Git commit/push 授权），均抓住了直接影响工程范围、代码安全性与发布节奏的实质问题。大脑在每条前均提供了负责任的“（推荐）”选项，未将技术实现细节甩锅给用户。

### 3.2 遗漏的关键决策项补充（D5）
* **[建议修改] 增加 D5：README 核心标语选定（`plan.md:92-100`）**
  * **位置**：`plan.md:92-100`（Next 决策区）
  * **理由**：
    `tasks.md:60` 明确声明：`标语在本任务开始时交用户选定`。
    既然标语属于用户拍板事项，为什么不在当前的方案阶段一并向用户呈现决策？如果等到 T10 执行阶段才突然向用户提问，会产生不必要的流程停顿。
    在 `gemini-r5.md` 中，验收官已经给出了经过充分论证的 3 个中英文候选标语（候选 1 最佳），完全具备在当前阶段直接提请用户定夺的条件。
  * **最小修改建议**：
    在 `plan.md:Next` 中正式追加 **D5 决策项**：
    > - **D5 README 核心标语选定**：
    >   - **选项 A（推荐）**：*AI 编程方案与证据契约 — 方案和测试收据随 Git 走，换宿主、换人、换 Agent 都能接上。*（Repo-tracked plans and verified receipts for AI coding — resume seamlessly across tools, teammates, and agents.）
    >   - **选项 B**：*可接力的工程级 AI 编程协议 — 告别重复解释，让方案与验收记录成为代码库的永久资产。*（Relayable, verifiable AI coding — stop re-explaining context, keep plans and audit evidence in your repo.）
    >   - **选项 C**：*跨工具 AI 编程契约 — 规划先澄清，实现留证据，进度跟仓库。*（The cross-host AI coding contract — plan with clarity, build with proof, track with Git.）

---

## 四、过度设计与低价值产物排查

大脑在本方案包的制定中展现了极强的克制力，此前争议较大的“激进重写 Pages”、“整套复制 pstack 56 技能”、“引入调度守护进程”均被果断排除在 Scope 之外。仅有两处细节需作精简：

### 4.1 细节审视与修改建议
* **[建议修改] W2/T4 内部 YAML 解析器替换的优先级（`tasks.md:25`）**
  * **位置**：`tasks.md:25`（`render-host-skills.py 复用 _yaml_subset`）
  * **理由**：Codex 在 R5 盘点中指出，此项仅能节省约 50 行维护者脚本代码，但却伴随破坏现有 YAML 字符串（引号、布尔、null）解析边界的隐蔽风险，且外部用户完全无感知。在聚焦发布的大背景下，此项不应作为阻碍 T4 交付的硬门槛。
  * **最小修改建议**：在 `tasks.md:25` 标注为“低风险试探，若全量快照测试发现细微解析漂移，则保持现状不强求合并”。

* **[建议修改] W2/T6 对外部 GitHub Issue #55 发言的解耦（`tasks.md:33`）**
  * **位置**：`tasks.md:33`（`在 #55 留言引用（需按 D4 授权）`）
  * **理由**：Orca 调度合同明文要求“不向外部发布内容”，且调用 GitHub API 涉及远端网络与写权限。若用户在 D4 中对网络发帖持保守态度，不应导致 T6 无法完成。
  * **最小修改建议**：将完成定义中的发帖要求解耦为“在 `docs/host-onboarding.md` 沉淀规范，并在文档末尾附上一段可供人工粘贴回复 #55 的 markdown 摘要文本；若获得 D4 授权则由大脑直接留言”。

---

## 五、终审结论清单归总

### 5.1 必须修改（Must-Fix）—— 方案定稿前必须纳入：
1. **[隔离新手测试]** 在 `tasks.md:59` 增加硬性约束：Trae 必须在“全新空白会话 + 独立临时测试目录”下执行 T10 的新手测试，杜绝 T8/T9 残留上下文造成的“伪冷读”；
2. **[补充 D5 标语决策]** 在 `plan.md:Next` 中追加 **D5 标语选择项**，将 R5 提炼的 3 个候选直接呈现给用户，避免在 T10 执行时产生二次中断；
3. **[补齐 Pages 验收项]** 在 `tasks.md:60`（T10 完成定义）中显式增加对 `index.html` / `zh-CN.html` 的事实同步与全站链接无死链检查。

### 5.2 可选修改（Nice-to-Have）—— 执行期灵活处置：
1. **[解耦外部发帖]** 将 T6 对 GitHub Issue #55 的远端留言改为“生成留言草稿”，避免受外部权限约束阻塞主线；
2. **[弱化内部脚本精简]** 将 T4 中 `render-host-skills.py` 复用内部 YAML parser 标记为非必须项，确保以 100% 行为稳定为先。

方案包整体设计非常扎实，完成了从“教 AI 先想再写”向“跨宿主方案与证据契约”的优雅收窄，在补齐上述 3 项必须修改后，验收官**全面认可该方案包进入定稿并可立即提请用户拍板！**
