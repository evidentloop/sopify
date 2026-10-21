---
title: 新版 Sopify：收窄定位、可靠性、多 agent 协作与新宿主
plan_id: 20261020_sopify_narrow_focus
status: planned
lifecycle_state: planned
level: standard
created: 2026-10-20
updated: 2026-10-20
archive_ready: false
knowledge_sync:
  project: review
  background: required
  design: required
  tasks: required
---

# 新版 Sopify：收窄定位、可靠性、多 agent 协作与新宿主

就绪状态: Ready
依据: 范围、路径与验收已收敛，并经 Codex（可执行性）和验收官（验收口径）审计修订；需求评分 8/10，两项扣分已按审计补齐。用户已于 2026-10-20 对 D1–D5 拍板（见 Key Decisions）。tasks.md 与所选项一致。

## Context / Why

2026-10-20 四方审计（Codex 代码取证、验收官市场与验收、Trae 宿主自检、大脑裁决）结论一致：Sopify 值得继续，但要收窄定位。

- 「先问再写」：Claude Code、Codex、Cursor、Antigravity 都已原生提供 plan mode，而 Sopify 这一项主要靠 prompt 约束，不再是差异化卖点。
- 「决策留痕」：最近 6 个归档包全部有回执，writer 在代码层面保证回执绑定方案版本、不被覆盖。这是最可靠的价值。
- 「跨宿主续做」：最想守的差异点，但归档里没有一条由不同执行会话冷启动接续完成的链。本版用真实样本证明或证伪。
- 已知问题：
  - CI 只跑 7/16 个测试文件，preflight 遇到 golden 不一致会自动刷新并 `git add`；
  - 安装器在文件损坏或缺失后重装返回 skipped；writer 读到非对象 JSON 抛裸 AttributeError；
  - 安装器整份覆盖 home 头文件（`installer/hosts/base.py:394-401`），会冲掉用户写在 CLAUDE.md / AGENTS.md 里的内容；
  - 卸载文档让用户直接删 `.sopify/`。
- README 讲不清是什么、什么价值、怎么用：新手冷读 5 问，首屏只得 2/10。

定位：从「教 AI 先想再写的工作流」收窄为「方案、决策和验收证据随仓库走，换工具、换人、换 agent 都能接着做」。

审计材料（未入库）：codex-r1/r2/r3/r5/r7、gemini-r1/r2/r3/r5/r7、trae-r6、brain-audit-r3。

## Scope

1. **可靠性**：CI 与 preflight 跑全部测试，preflight 检查失败即失败；修 AUDIT-1..4 和共同安装器的完整性判断；吸收 PR #75 的测试；共享 home 文件改为 managed block 写入并迁移旧安装（D2）；卸载说明改为保留方案与历史。
2. **瘦身（中等档，D1）**：压缩宿主入口和 Copilot 平铺；删除已核实的私有残留与历史试点脚本；收束 protocol / blueprint 的退场叙事；合并重复的开发、发版与原理文档。保留 history、ADR、legacy 安装兼容、公开 Python 导出和 MCP。
3. **Sopify × Orca 可选执行适配**：文档加模板（不新增 builtin Skill）；Develop 规则加 bug 调查小分支（借鉴 pstack）；EARS 和增量写法只作为少量可选例子。
4. **宿主接入 recipe**（issue #55）以及 Antigravity CLI、Trae CLI 2.x 两个 baseline 适配。
5. **价值证明**：T5 与 T9 共用一条真实闭环，其中 T9 要求另一宿主只凭 `.sopify/` 冷启动接手。
6. **交付**：按需重写 README 中英文，Pages 同步事实与 Hero 标语；先做候选版验证，再发 release，最后做正式 smoke。

## Approach

**分工**（身份交叉审计：交付物不由产出者自己验收）

| 身份 | 职责 |
|---|---|
| 大脑（Claude Code） | 方案 owner；唯一通过 `sopify_writer` 写 active plan、handoff、receipts；拆单、审 diff、裁决、对外 Git 动作 |
| 执行（Codex） | 代码与文档实现；负责公共注册、renderer / flatten、共有测试和生成物的统一合入 |
| 验收（Antigravity） | 按完成定义验收；Antigravity 适配的 dogfood 宿主 |
| Trae（TRAE CLI） | 写了 T6 recipe 和加载面自检。T8 照常实现（用户决定）；额度用尽期间没有真实会话证据，照实标注，后续 PR 补 |
| Qoder（Qoder CLI，Terminal 5） | 用户指定：T9 冷启动执行者 B，以及 README 新手测试员。两次都用全新会话 |

交叉复核：
- Codex 的实现：由验收官验收，大脑审 diff。
- Antigravity 的 dogfood 证据：由 Codex 复核。
- Trae 的 dogfood 证据：由验收官复核。
- 大脑写的方案和回执：按需派 Codex 和验收官审。

**并行规则**：独立的新文件可以并行；公共注册（`installer/hosts/__init__.py`、`skills/hosts.yaml`、catalog、`distribution.py` 显示名、Doctor）、renderer / flatten、共有测试和 golden / 体积基线由执行统一串行合入，T3、T4、T5 都合入后统一复核一次快照。不引入锁或编排系统。

**统一验收标准**（用户 2026-10-20 提出，适用于每个任务，由验收官核对，大脑审 diff 时同样执行）：
- 不过度设计：没有为未发生的场景预建机制、表或配置。
- 符合设计规范：沿用仓库已有的模块边界与命名，不跨模块引用私有实现。
- 不冗余：同一能力只有一份实现；文档同一事实只写一处。
- 与其他宿主整体一致：同类行为（managed block、安装、Doctor、文案）在各宿主之间语义一致。
- 不增加用户心智负担：不新增用户需要理解的概念、步骤或手工操作；升级不要求用户手动处理。

**停车点**：只在三种情况停：会改变范围的选择、D4 授权之外的对外动作、失败。不按波次机械停车。

**证据规则**：
- 每个任务记录：代码 SHA 或方案版本、命令或会话、结果、证据位置、审查者。
- 缺陷才展开为完整 findings（位置、复现、预期与实际、测试 ID）。
- 宿主证据另外记录宿主版本、候选 SHA、实际安装路径、关键文件 hash。

## Waves / Steps

- [x] W1 可靠性：T1 → T2（T1 的 PR CI 待 push）
- [x] W2 瘦身与契约：T3、T4、T5、T6 完成并验收（T6b 留作 T9 样本）
- [x] W3 新宿主：T7 通过（agy 真实 dogfood），T8 通过（无真实会话证据，照实标注）
- [x] W4 价值证明：T9 通过（Qoder 冷启动）；T1 的 PR CI 已补
- [ ] W5 交付：T10 README 与 Pages，T11 release：T6 可前置；T3 依赖 T2；T4 依赖 T1；T5 文档与模板可并行，阶段源合入后再生成 T3 的最终快照
- [ ] W3 新宿主：T7、T8 先做探针再定布局，独立文件并行，公共接入串行
- [ ] W4 价值证明：T9（与 T5 共用一条真实闭环）
- [ ] W5 交付：T10 候选版验证（README、Pages、新手测试）→ T11 release、正式 smoke、收口

## Key Decisions

- 用户决策（2026-10-20）：
  - D1 冗余删减取中等档。
  - D2 所有宿主的共享 home 文件都改为 managed block，并迁移旧安装。
  - D3 新宿主或 T9 未通过时不阻塞 release：未通过的宿主不注册、不进支持表，T9 失败则 README 不写跨宿主续做。
  - D4 大脑可以直接 commit；push、开 PR、推候选分支、merge、release、关闭 PR #75、在 issue #55 留言，都要先经用户确认。
  - D5 README 标语方向取 A，措辞由验收官和 Trae 各自给出优化稿后再定。大脑的合成稿（T10 开始时请用户最终确认）：
    - 主标语：中文「AI 编程的方案和验收证据存进仓库，换工具、换人、换 agent 都能接着做。」，英文 "AI coding plans and proof in your repo — keep building across tools, teammates, and agents."
    - 副标语：中文「装进你已经在用的 AI 编程工具；问答和小修照常，不强制走流程。」，英文 "Installs into the AI coding tools you already use. Questions and small fixes stay direct."
    - T9 失败时的备用主标语：中文「AI 编程的方案和验收证据存进仓库，不再散落在聊天记录里。」，英文 "AI coding plans and proof live in your repo, not scattered across chats."
  - 允许按需做局部重构，限于本方案已列入范围的文件。
- 定位收窄为「跨宿主可携带的方案与证据契约」；问答和小修继续直接处理，不进方案流。
- writer 和 contracts 的 schema 不改，新增信息一律走 `evidence`；不改公开的 Python 导出；保留 legacy bundle 安装兼容和独立部署 helper / Hook 的 fallback。
- 不引入常驻进程、调度器、锁、第二套进度真相。Orca 负责调度，Sopify 负责仓库里的方案与证据。
- 新宿主一律标 BASELINE_SUPPORTED；安装成功、catalog 可见、实际按规则执行，分别记录为不同的事实。
- worker_done 不等于 verify pass；验收官只出审查结论，回执由大脑写。
- Orca 适配以文档加模板交付，不新增 builtin Skill 或 dispatcher。
- Trae 入口不写全局 AGENTS.md（trae-r6：CLI 2.0 未加载全局规则文件）。候选方案是在 `~/.trae/skills/` 下放一组扁平的 `sopify-*` Skill，外加一个顶层入口 Skill；description 控制在 1024 字符以内；v1 不碰 hooks。最终布局以 T8 探针结果为准。
- Antigravity 是本版主要的 dogfood 宿主。探针结果：全局规则 4 个候选都会加载（`~/.gemini/AGENTS.md` → `~/.gemini/GEMINI.md` → `~/.gemini/config/AGENTS.md` → `~/.gemini/config/GEMINI.md`），都排在项目规则前；Skill 只扫描一层；有 `ask_question`；新会话才生效。安装目标定为 `~/.gemini/config/AGENTS.md`（managed block）和 `~/.gemini/config/skills/` 下一组扁平的 `sopify-*` Skill。共享规则文件只用 managed block；hooks 和 MCP 留到第二期。
- 不复制 pstack 的 56 个 Skill、编排 runtime 和个人化命令；不加 Constitution 层和角色斜杠命令。
- README 最后一次性重写，只写已验证的事实；真实 dogfood 案例保留，挪到「真实案例」小节。
- 旧方案 `20260819_cursor_support` 已于 2026-10-20 按用户授权显式归档。

## Constraints / Not-in-scope

- 不做激进档：不删 legacy contracts 公开模型，不下线 MCP，不替换 Copilot 加载方式，不重建 Pages。
- 新宿主任务允许安装 Sopify 自己的受管入口、Skill 和 payload；禁止修改账号、代理、模型、工具 settings、`traecli.toml` 和 trust 配置；不做 hooks 和 MCP 注册。
- 引用清理只针对当前执行入口、安装、测试和现行文档；history、ADR 中的历史记载，以及负向测试里对退役路径的禁止断言，都保留。
- 不新建发布服务、版本命名方案或营销测量框架；沿用 `YYYY-MM-DD.HHMMSS` 版本。
- PR #75 保持 DO NOT MERGE，由新 PR 吸收其测试。

## Status / Progress

- [x] 2026-10-20 四方审计、冗余盘点、README 诊断、Trae 自检完成；需求评分 8/10 达标
- [x] 旧方案 `20260819_cursor_support` 已归档
- [x] 方案审计 R7：Codex 5 组必改、验收官 3 项必改，均已纳入本版
- [x] 用户已对 D1–D5 拍板
- [x] W1 可靠性：本地完成，验收通过（T1 的 PR CI 待 push）
- [ ] W2 瘦身与契约

## Dogfood 观察（待内部审计）

本方案由四个 agent 用 Sopify 自己执行。用户要求：大家都是使用者，不为开发而开发，发现可优化的地方先做内部审计，再决定是否进入范围。

- 写回执只能手写 Python 调用 `sopify_writer`。大脑在 W1 因 heredoc 引号失误把一个路径写坏，已删掉并经 writer 重写。暂不加 CLI；先审计现有 MCP 写入工具或文档示例能否覆盖。
- 本轮的任务单是手写的。T5 的 task packet 模板以这些真实任务单为样本，不凭空设计。
- Orca 的 `worker-start` 不认 Trae 标签，只能手动 dispatch，并在任务单里抄写回传命令。这是 Orca 侧的限制，最多在 `docs/orca.md` 里写一句注意事项。
- 旧方案的 handoff 59 天没更新，由 T5 的陈旧 handoff 核对覆盖。
- 验收官在 T6 验收中提出 5 条摩擦，经大脑审计全部采纳，均不新增机制：
  1. 任务上下文散在 4–5 个文件里 → T5 的任务单在顶部列出唯一输入清单。
  2. 统一验收标准与完成定义重复对账 → 统一标准作为全局规则，验收报告只写不通过或有风险的项。
  3. 返工后新旧报告并存 → 返工更新原报告，追加「本轮变化」一节。
  4. 共享工作区怕污染 → 任务单统一给出 `PYTHONDONTWRITEBYTECODE=1` 和 `PYTEST_ADDOPTS="-p no:cacheprovider"`。
  5. 审计报告放在临时目录，与「证据存进仓库」相矛盾 → 每个波次收口时，把执行报告和验收报告归档到本方案的 `audits/`（沿用已有惯例），回执引用仓库内路径。W1 的报告在 W2 收口时一并补归档。

## Next

开工：
1. 派 Codex 执行 W1 的 T1、T2，同时让验收官和 Trae 各自优化 D5 标语措辞。
2. 第一次需要 push 时（CI 实跑、候选分支、开 PR）停下来请用户确认。

以下为当时提交给用户的决策选项，保留备查：

- **D1 冗余删减档位**：
  - 中等（推荐）：入口中文约 10.6KB 压到 4–5.5KB，Copilot 平铺压到 22–28KB；删除 4 个私有残留和试点脚本（含维护者命令 `sync-skills.sh`，给出替代命令）；收束蓝图和文档。
  - 保守：只删明显重复和 3 个私有残留，入口压到约 7–8KB。
- **D2 共享 home 文件写入方式**：
  - 全部宿主改为 managed block，按迁移矩阵处理旧的整份安装（推荐；修复冲掉用户内容的真实问题）。
  - 只有新宿主用 managed block，老宿主保持现状，并在文档中写明这个已知问题。
- **D3 新宿主或 T9 未通过时**：
  - 不阻塞 release（推荐）：未通过的宿主不注册为安装目标，也不进支持表；T9 失败则 README 不写跨宿主续做，release notes 如实说明。
  - 阻塞 release，直到通过。
- **D4 执行期对外动作授权**：
  - 推荐：大脑可以在 `feat/` 分支 commit、push、开 PR，并推送候选分支用于 `install.sh --ref` 验证；merge、release、关闭 PR #75、在 issue #55 留言之前停车。
  - 每次 commit 都确认。
- **D5 README 标语**（最终措辞取决于 T9 结果；T9 失败时去掉「换工具接着做」）：
  - A（推荐）：中文「AI 编程的方案和验收证据存进仓库——换工具、换人、换 agent 都能接着做。」英文 "Plans and proof that live in your repo — any tool, teammate, or agent can pick up the work."
  - B：中文「把 AI 编程的方案放进 git：谁都能接着做，每个改动都有证据。」英文 "Your AI coding plan, in git — anyone can resume it, every change has proof."
  - C：中文「跨工具的 AI 编程契约：先澄清再动手，改动有证据，进度跟仓库走。」英文 "The cross-tool AI coding contract — plan with clarity, build with proof, track with git."

用户拍板后，大脑按选择改写受影响的任务，然后派 Codex 进入 W1。
