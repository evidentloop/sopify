# 任务清单: 新版 Sopify：收窄定位、可靠性、多 agent 协作与新宿主

目录: `.sopify/plan/20261020_sopify_narrow_focus/`

角色：大脑 = Claude Code（owner），执行 = Codex，验收 = Antigravity 验收官，Trae = TRAE CLI 标签，新手 = 全新会话。每项「验收」由非产出者完成。本清单按用户的 D1–D5 决策编写。D4：大脑可以直接 commit；凡是需要 push 的步骤（T1 的 PR CI、T10 的候选分支、开 PR），执行前都要先经用户确认。

## W1 可靠性

- [ ] T1 全量测试门（本地已完成并通过验收，见 exec_001 / verify_001；PR CI 链接待用户批准 push 后补）
  - 产物：`.github/workflows/ci.yml` 和 `scripts/release-preflight.sh` 都改为收集 `tests/` 全部测试，保留 catalog drift、protocol smoke、payload smoke；preflight 遇 golden 不一致直接失败，不再自动 regenerate 并 `git add`；保留 `release-sync.sh` 在显式版本更新时同步模板和 golden 的职责；调整 `tests/test_release_hooks.py`。
  - 依赖：无。执行：执行。验收：验收。
  - 完成定义：
    - 本地 `python3 -m pytest tests -q` 退出 0；
    - PR 上的 CI 实跑全量并为绿（记录 CI 链接）；
    - 在隔离夹具或临时仓库中验证：preflight 遇 golden 漂移时退出非 0，且 index 不变。
- [x] T2 安装与 writer 修复（exec_001 / verify_001。返工后：首尾锚点迁移所有 2026-06 以来的旧 header；Copilot、home、bootstrap 共用一个 managed block 实现）
  - 产物：
    - AUDIT-1 与共同安装器（`installer/cursor_plugin.py`、`installer/hosts/base.py`）按 Sopify 受管树的内容判断完整性；
    - AUDIT-2/3（`installer/distribution.py`）：空 smoke 显示为「未执行运行时自检」，补 Cursor 显示名；
    - AUDIT-4（`sopify_writer/io.py`）：读取边界拒绝非对象 JSON，抛 `InvariantViolationError`；
    - 吸收 PR #75 的 4 个测试文件并去掉 xfail；
    - Claude、Codex、Qoder 的 home 头文件改为 managed block 写入（D2）；
    - `docs/getting-started.md` 的卸载说明改为保留 `.sopify/` 的方案与历史。
  - 迁移矩阵（必须全部有测试）：
    | 输入 | 期望 |
    |---|---|
    | 只有用户内容、没有 Sopify 块 | 追加一块，保留用户内容；重复安装不增加块 |
    | 能确认是旧版 Sopify 整份产物 | 迁移为单块，不留下旧规则和新规则同时生效 |
    | 旧产物混有用户内容 | 保留非受管内容；无法可靠识别的部分不做破坏性改写，明确提示迁移未完成 |
    | 已有合法块，或 markers 不完整、重复 | 合法块正常更新且保留外部内容；结构异常时明确拒绝或保守处理，不静默丢内容 |
  - 保留：legacy bundle 兼容测试（`tests/test_installer.py:995-1053`）、独立部署 helper 和 Hook 的 fallback。
  - 依赖：T1。执行：执行。验收：验收；大脑审 diff。
  - 完成定义：
    - 每个缺陷都有修前失败、修后通过的测试证据；
    - 迁移矩阵 4 类输入全部有测试；
    - 删掉一个阶段 Skill 后重装，返回 updated 并复原；
    - 语言切换、重复安装、用户其他 Skill 不受影响；
    - 全量测试通过。

## W2 瘦身与契约

公共文件、生成物和共有测试由执行统一合入；T3、T4、T5 都合入后，统一复核一次 golden 和体积。

- [ ] T3 入口压缩
  - 产物：
    - `skills/{zh,en}/header.md.template` 按 codex-r5 第 1 节逐节压缩，中文约 4–5.5KB，英文约 5–6.5KB；
    - Copilot 平铺去重：中文约 22–28KB，英文约 24–31KB，可能触及 `installer/hosts/base.py` 的 flatten 和共享资源；
    - 核对 Cursor 薄入口 `skills/{zh,en}/cursor-plugin-rule.mdc.template`、`cursor-cli-skill.md.template` 的语义对齐，不把通用长 header 塞进 Cursor；
    - 同步 `tests/behavior-scenarios/plain-language-output-v1.json` 的实测 after 值（记录中英文 UTF-8 字节）；golden 经人工审查后更新。
  - 依赖：T2。最终快照在 T5 阶段源合入后生成。执行：执行。验收：验收。
  - 完成定义：
    - 四步读链、意图优先、writer 边界、三个命令仍在第一跳可见；
    - `test_golden_snapshots`、`test_plan_contract_assets`、`test_plain_language_contracts` 通过；
    - 真实会话验证并入 T7、T8 的 dogfood（新宿主消费的就是压缩后的同一份入口）。这样发版前不用改动用户自己的 Claude、Codex 安装。
- [ ] T4 冗余清理（中等档）
  - 删除：`sopify_writer/_resume.py`、`scripts/w33_qoder_proof.py`、`scripts/check-enhancement-declaration.py`、`scripts/sync-skills.sh`（以 `render-host-skills.py --output` 替代，同步 CONTRIBUTING、hook 白名单和测试夹具）。
  - 精简与合并：
    - `render-host-skills.py` 改为复用 `_yaml_subset`；若快照出现解析漂移，就保持现状；
    - 收束 `protocol.md` 中的 RETIRED / legacy 段落和陈旧实现映射，以及 `blueprint/design.md`、`blueprint/tasks.md`；
    - 删除 `blueprint/skill-standards-refactor.md`，同时更新 `blueprint/README.md` 中的链接；
    - `docs/dev/development-guidelines.md` 并入 CONTRIBUTING；`release-process.md` 作为发版步骤的唯一来源；
    - `how-sopify-works*.md` 去重；清理 `examples/external-repo-quickstart/` 中失效的 runtime 示例。
  - 依赖：T1；renderer、测试、生成物的合入在 T3 之后。执行：执行。验收：验收。
  - 完成定义：
    - 当前执行入口、安装、测试和现行文档中没有失效引用（history、ADR 和负向断言除外）；
    - 全量测试与 `check-readme-links` 通过；
    - 维护者命令变化写进 CHANGELOG。
- [ ] T5 Sopify × Orca 可选执行适配
  - 产物：
    - `docs/orca.md`，外加同目录的 task packet 和 findings 小模板，内容包括：
      - task packet：plan_id、plan_version、task、代码基线、写集、验收命令、继承证据、待重验项；
      - 陈旧 handoff 核对；
      - 唯一 owner 写回；
      - worker_done 与 verify 的区别；
    - Develop 规则加 bug 调查小分支：先复现，再修，修完用同一复现证明；
    - Analyze、Design 各加一段可选的 EARS 与增量写法示例。
  - 依赖：无（文档与模板可先并行）；阶段源合入时与 T3 协调。执行：执行。验收：验收；大脑审语义。
  - 完成定义：
    - 文档和模板经评审可用；
    - 最终的真实闭环证据与 T9 共用：大脑派单 → 执行实现 → 验收审查 → 大脑写 receipt，evidence 中包含 Orca run、task、dispatch ID 和代码 SHA；
    - writer schema 无变化。
- [ ] T6 宿主接入 recipe（issue #55）
  - 产物：`docs/host-onboarding.md`，包括：
    - 能力矩阵：入口、Skill 发现、提问、持久化、缺席降级；
    - 负向边界；
    - 先探针后布局的步骤；
    - 证据字段：宿主版本、候选 SHA、安装路径、文件 hash；
    - 漂移检查；
    - 新宿主测试模板。
  - 依赖：无，可前置。执行：执行。验收：验收。
  - 完成定义：recipe 经评审，可供 T7、T8 直接使用。T7、T8 遵循 recipe 的证据在各自任务中回填。#55 的留言由大脑在收口时按授权处理，不作为本任务的完成门槛。

## W3 新宿主（独立文件并行；公共注册、catalog、Doctor 和共有测试由执行串行合入）

- [ ] T7 Antigravity CLI baseline
  - 步骤：
    1. 临时安装探针：确认规则、Skill 发现和资源引用路径，以及重启或新会话的要求；
    2. 定投影；
    3. 实现 `installer/hosts/antigravity.py`、`docs/antigravity-host.md` 和测试。
    共享规则文件只用 managed block。
  - 依赖：T2、T3、T6。执行：执行。dogfood：验收官在自己的 agy 会话中安装候选产物并验证。复核：执行审 dogfood 证据。
  - 完成定义：
    - 会话证据绑定候选 SHA、安装路径和文件 hash，并分别记录：已安装、Skill 可见、实际按规则执行；
    - 问答不进方案流；
    - 用户已有的 GEMINI.md / AGENTS.md 内容不变；
    - Doctor 区分安装事实和行为证据；
    - 标 BASELINE_SUPPORTED。
  - 未通过时（D3）：不注册为安装目标，不进支持表；同步注册、catalog、Doctor 和文档。
- [ ] T8 Trae CLI 2.x baseline
  - 步骤：探针 → 投影 → 实现 `installer/hosts/trae.py`、`docs/trae-host.md`、测试。候选布局：`~/.trae/skills/` 下放一组扁平的 `sopify-*` 阶段 Skill 加一个顶层入口 Skill；不写全局 AGENTS.md，不碰 hooks 和 `traecli.toml`。
  - 必须验证：
    - 扁平化后阶段之间的相对路径和共享 references 能否读取；
    - 两层嵌套是否被发现（只做记录，不依赖它）；
    - description 不超过 1024 字符；
    - trust 对加载的影响：只用已有的不同信任状态工作区或宿主支持的隔离方式验证，没有可行方式就标「未验证」。
  - 依赖：T2、T3、T6。执行：执行。dogfood：Trae。复核：验收审 dogfood 证据。
  - 完成定义：同 T7。
  - 未通过时：同 T7。

## W4 价值证明

- [ ] T9 冷启动跨宿主续做（与 T5 共用一条闭环）
  - 做法：
    1. 大脑开出本方案剩余任务中的一个真实小任务，并写明写集；
    2. 执行者 B 开一个全新会话，只凭 `.sopify/` 文件接手、实现并跑验收；
    3. 验收官审查；
    4. 大脑通过 writer 写回 receipt。
  - 执行者 B 的路线：
    - 首选 Trae，需要 T8 已取得真实加载证据；
    - T8 未通过时改用 Antigravity，需要 T7 已通过；
    - 两者都未通过：按 D3，把失败结果写进 release notes，README 不写跨宿主续做。
  - 依赖：T5 文档与模板可用，以及上述路线对应的宿主任务。验收：验收。
  - 完成定义：记录两个执行身份、起止代码 SHA、plan_version、实际读取的文件和结果，成功或失败都如实记录。

## W5 交付

- [ ] T10 README 与 Pages（候选版验证）
  - 产物：`README.md`、`README.zh-CN.md` 按需重写：
    - 首屏讲清它是什么、价值、怎么开始，使用 D5 选定的标语；
    - 一个可复制的安装命令和第一个 `~go plan` 示例；
    - 什么时候不用；
    - Before/After 价值场景：单宿主长任务、换宿主或换人接手、Orca 多 agent 分工；
    - 宿主表只列已验证的宿主；
    - 架构图和 EvidentLoop 细节移到 docs；真实 dogfood 案例挪到「真实案例」小节；
    - `index.html`、`zh-CN.html` 同步 Hero 标语、事实和链接，保留布局。
  - 新手测试：
    - 一个全新会话，在全新临时目录中进行，此前从未接触本项目或本轮任何材料；
    - 只读新 README，回答 5 问（它是什么、什么价值、何时不用、怎么开始、产物是什么样），得分 ≥ 9/10；
    - 用 `install.sh --ref <候选分支>` 在临时仓库完成安装和第一个 `~go plan`；
    - 记录全过程。
  - 依赖：T7、T8、T9 的已裁定结果。执行：执行（大纲由大脑定）。验收：验收。
  - 完成定义：
    - 新手测试通过且有记录；
    - `check-readme-links` 通过，Pages 链接人工核对；
    - 中英文结构一致；
    - 这一步只算「候选版验证」，不算 release 完成。
- [ ] T11 Release 与收口
  - 产物：
    - CHANGELOG 和 release notes：成果、维护者命令变化、迁移边界、未通过项；
    - 版本同步、preflight；
    - PR 合并；
    - 用 `render-release-installers.py` 生成匹配 tag 的安装资产；
    - GitHub Release 与 latest；
    - 按公开 README 的正式命令从远端安装，核对 tag、来源版本和关键产物；
    - 新 PR 合并后关闭 PR #75；在 #55 留言；
    - 更新 blueprint；`~go finalize` 归档本方案。归档产生的 tracked 变化通过一个后续获准的提交或 PR 交付。
  - 依赖：T1–T10（或按 D3 已裁定排除的项）。执行：大脑和执行。验收：验收复核正式 smoke。
  - 完成定义：
    - 只有实际发布并通过正式远端 smoke，才算 release 完成；
    - merge、release、关闭 PR、issue 留言之前按 D4 停车。
