# 首次 ~go 后 workspace bundle 缺失诊断

**裁定：老行为、用户可感知；不是本版扁平适配回归，也不是本例的 Doctor 误报。** 至少已发布版本 `8770413` 就存在同样的“宿主规则没有确定性接上首次项目绑定调用”的缺口。只创建 KB 文档、plan 和 writer state 不会产生 `.sopify/sopify.json`；Doctor 准确报告缺少项目绑定，而不是全局 payload 未安装或必须复制一份本地 bundle。

本轮仓库基线：`feat/sopify-narrow-focus@32687ae0ba9e80f6122c2b907239b98a6b5d34d3`，开始时干净。仓库仅修改 `docs/antigravity-host.md`；未修改 `installer/hosts/flat.py`、测试、README、`.sopify/**`，未 commit、push 或写真实 home。实验均在本报告旁 `bundle-diag-evidence/` 下，使用显式临时 home 和独立新建 Git 仓库，不调用模型。

## 1. 首次初始化由谁、在何时触发

需要区分三种不同工作，避免把“创建了 .sopify 目录”当成全部启用完成。

| 工作 | 当前负责者与实际内容 | 何时发生 |
|---|---|---|
| 全局 prompt / payload 安装 | `scripts/install_sopify.py` 安装入口、Skills、版本化 payload 和 bootstrap helper | 执行安装命令时；默认 `workspace_value=None` 不初始化任何目标项目 |
| 项目方案和知识物化 | 宿主消费 header 与 Analyze/Design/KB 规则后，用工具创建方案/知识文档；`ProtocolStore` 写 plan 指针及 handoff | 宿主进入相应阶段并执行工具时；这些操作本身不写项目 bundle 标记 |
| 项目 bundle 绑定 | 显式调用安装后的 `sopify/helpers/bootstrap_workspace.py`，或 `scripts/sopify_init.py init`；安装器显式 `--workspace` 预热也会调用 helper | **调用这些入口后**才发生。仅输入 `~go` 不会使 Python helper 自行监听或执行 |

源码依据：

- [共同 header](/Users/weixin.li/code/github/sopify/skills/zh/header.md.template:30) 规定意图、四步读取及 writer 边界；[路由](/Users/weixin.li/code/github/sopify/skills/zh/header.md.template:42) 交给阶段 Skill，但没有调用 bootstrap helper / sopify_init 的命令。开头的 `<!-- bootstrap: lang=... -->` 是标识注释，不是执行入口。
- [KB progressive 规则](/Users/weixin.li/code/github/sopify/skills/zh/skills/sopify/kb/SKILL.md:28) 要求先建 project/preferences/blueprint，再补深层 blueprint 和方案目录；没有 `.sopify/sopify.json` 或 bundle 绑定步骤。Analyze 只消费 KB；Design 生成语义文件；writer 的 `set_active_plan` / `set_current_handoff` 只负责 state，不替项目启用。
- [安装器](/Users/weixin.li/code/github/sopify/scripts/install_sopify.py:183) 仅在显式给定 workspace 且非 user-plugin 宿主时调用 `run_workspace_bootstrap`。四个受测宿主默认安装均未指定 workspace。
- [bootstrap helper](/Users/weixin.li/code/github/sopify/installer/bootstrap_workspace.py:183) 根据自己的安装位置解析全局 payload；随后检查授权、根目录与运行模式。通过检查后调用 [stub writer](/Users/weixin.li/code/github/sopify/installer/bootstrap_workspace.py:932)，写入 `bundle_version`、`locator_mode=global_first`、capabilities、ignore 策略等项目标记。
- [sopify_init.py](/Users/weixin.li/code/github/sopify/scripts/sopify_init.py:218) 是另一条**显式**项目启用路径：写 `sopify.json`、Git ignore 规则，默认还分发 workspace-scope 指令。它也没有在 `~go` 前自动运行的 watcher。

所以，预期的责任应由宿主在首次受管写入前完成绑定；现行共同规则却没有把这项调用接入必经步骤。helper 中接受 `~go` / `~go plan` 的正则仅负责**已被调用时的写入授权**，不能证明用户输入这些文字就会触发它。

还有一个必须保留的边界：[helper 的首写检查](/Users/weixin.li/code/github/sopify/installer/bootstrap_workspace.py:519) 对显式 `interaction_mode=non_interactive` 返回 `NON_INTERACTIVE`，不创建标记。因此，后续即便补上调用，也不能把全新 headless 项目的启用描述为无条件自动成功。省略该参数时走现有默认策略，不能把默认值当成已经验证了交互模式。

## 2. 跨宿主与旧版对照实验

### 方法

实验脚本：[experiment.py](./bundle-diag-evidence/experiment.py)。每个宿主分别安装到自己的显式临时 home；每条分支使用隔离 Git 仓库，不写真实用户配置。

对照版本：

- 当前 `32687ae`：Codex、Qoder、Antigravity、Trae。
- 已发布 `8770413548b8194a2ee79c5e342717d3050456a2`：Codex、Qoder。通过 `git archive` 仅把 installer/scripts/skills/contracts/writer 提取到 scratchpad 的 `source-8770413/`，未 checkout、切换工作区或提取仓库 `.sopify`。

每个版本/宿主组合执行五条分支：

1. **按已安装规则写文件**：创建 KB progressive 列出的六个知识文件、light plan，调用 `ProtocolStore` 写 active_plan/handoff；不擅自增加规则中不存在的 bootstrap 调用。
2. **显式 helper**：在上述项目中调用安装后的 helper，传入 `--request "~go plan add zero division guard" --interaction-mode interactive`。
3. **显式 init**：新项目执行该版本 `scripts/sopify_init.py init --workspace <临时项目> --no-copilot`，避免把无关 Copilot 指令分发混入比较。
4. **安装器预热**：新项目明确传 `workspace_value=<临时项目>` 调用安装器。
5. **非交互首写**：另一个新项目对 helper 明确传 `--interaction-mode non_interactive`。

这是无模型的确定性模拟：证明规则、工具及检查器之间的机制缺口；不声称每个实际模型都会作出同一种选择。

### 结果

| 版本 / 宿主 | 规则文件 + writer state | 显式 helper | 显式 init | 显式预热 | 非交互 helper |
|---|---|---|---|---|---|
| 当前 Codex | MISSING_BUNDLE / broken | pass / up_to_date | pass / up_to_date | pass / up_to_date | NON_INTERACTIVE，无标记 |
| 当前 Qoder | MISSING_BUNDLE / broken | pass / up_to_date | pass / up_to_date | pass / up_to_date | NON_INTERACTIVE，无标记 |
| 当前 Antigravity | MISSING_BUNDLE / broken | pass / up_to_date | pass / up_to_date | pass / up_to_date | NON_INTERACTIVE，无标记 |
| 当前 Trae | MISSING_BUNDLE / broken | pass / up_to_date | pass / up_to_date | pass / up_to_date | NON_INTERACTIVE，无标记 |
| 已发布 8770413 Codex | MISSING_BUNDLE / broken | pass / up_to_date | pass / up_to_date | pass / up_to_date | NON_INTERACTIVE，无标记 |
| 已发布 8770413 Qoder | MISSING_BUNDLE / broken | pass / up_to_date | pass / up_to_date | pass / up_to_date | NON_INTERACTIVE，无标记 |

所有规则-only 分支的 `workspace_pin=null`；显式成功分支的 `bundle_version=2026-08-30.001152`，两个 workspace Doctor 项均 pass。**成功分支都没有创建 `.sopify-payload/` 本地副本**，仅通过 marker 定位全局 bundle 即可健康。

共 6 个版本/宿主组合、各 5 条分支，结果已逐项断言通过；原始结果及全部显式命令保存在 [current-results.json](./bundle-diag-evidence/current-results.json)、[released-8770413-results.json](./bundle-diag-evidence/released-8770413-results.json)，临时 home 和项目保留于对应版本/宿主目录供复查。

### 历史源代码核对

不仅当前多个宿主一致，旧版也相同。另将以下 9 个函数做无位置属性的 AST 比较，**全部与已发布 8770413 一致**：

- helper：`bootstrap_workspace`、`_authorize_first_workspace_write`、`_classify_first_write_barrier`、`_classify_workspace_bundle`、`_write_workspace_stub_overlay`；
- Doctor：`classify_workspace_version_state`、`_inspect_workspace_bundle`；
- init：`init_workspace`、`_write_sopify_json`。

[比较记录](./bundle-diag-evidence/historical-function-comparison.json)。KB 中文入口与旧版也逐字节一致；压缩前的 header 同样没有 bootstrap/helper 调用。因此，这个缺口至少早于本轮 header 压缩和 Antigravity/Trae 扁平适配，不符合“本版新增且只需修 flat.py 路径”的条件。

## 3. 三类裁定及后续决策

### 本版回归：否

没有发现扁平路径写错、安装 helper 丢失或新宿主特有的绑定失败。当前四宿主的显式 helper、init 与预热路径均有效；旧版两宿主复现相同未绑定状态。因此，本轮不改 `installer/hosts/flat.py`，也不增加只能遮住新宿主问题的补丁或回归测试。

### 老行为、用户可感知：是

实际 dogfood 证明宿主可以顺利创建 plan 和 writer state，却跳过启用标记。按现行规则完整模拟 KB 初始文件也不能补上它。用户看到“方案 Ready”并不意味着项目通过绑定健康检查；这是当前规则入口与已存在初始化工具之间的接线缺口。

需要校正一处前提：**当前 README 没有“首次 ~go 自动初始化”这句原文**。明确承诺实际在 [英文安装输出](/Users/weixin.li/code/github/sopify/installer/distribution.py:591)、[中文安装输出](/Users/weixin.li/code/github/sopify/installer/distribution.py:660) 及 `scripts/install_sopify.py:62` 的描述中；README 则写“安装后用 ~go 启动全托管工作流”，容易形成同样预期。本轮依写集没有修改这些位置。

若暂不修共同入口，README/安装说明建议采用：

> 安装提供宿主入口、Skills 和全局 bundle。输入 `~go` 可请求宿主按工作流处理任务；仅生成方案或 state 不代表项目初始化完成，项目是否已绑定可用 bundle 以 Doctor 的 workspace 检查为准。当前尚未保证新项目首次 `~go` 自动完成绑定。

英文可对应：

> Installation provides host instructions, Skills, and a global bundle. `~go` asks the host to follow the workflow; creating a plan or state does not by itself initialize the project. Use Doctor's workspace checks to verify the bundle binding. Automatic binding on the first `~go` in a new project is not yet guaranteed.

**需要大脑决策，但不阻塞本次诊断交付：**是后续把现有 helper 调用补入共同宿主首写入口并保留授权/目录选择/非交互边界，还是明确项目启用为前置条件并统一下调 README、安装输出及支持说明。该决定影响全部 prompt 宿主和用户使用步骤，超出“仅新宿主 flat.py 小修”的授权；不应在本轮偷偷扩展成初始化机制重做。

### Doctor 误报：本例不是

[workspace 检查](/Users/weixin.li/code/github/sopify/installer/inspection.py:964) 查的是 `.sopify/sopify.json`，缺失就返回 `MISSING_BUNDLE`；[版本检查](/Users/weixin.li/code/github/sopify/installer/inspection.py:450) 从该文件取 `bundle_version`，无 pin 则 `broken`。这两个事实在原 dogfood 项目和实验里都确实成立。

它没有要求复制本地 payload，正向实验也证明仅有合法全局绑定即可通过。`MISSING_BUNDLE` 的名称容易让人误以为“全局库不存在”，但这只是措辞可读性问题，不能把本次缺少绑定标记的失败判为假阳性。对一个根本没有启用 Sopify 的普通目录是否应降为 skip，是另一项产品策略讨论，不改变本次已经写入受管 plan/state 的事实。

## 4. 已落实的 Antigravity 文档降级

实际修改：[docs/antigravity-host.md](/Users/weixin.li/code/github/sopify/docs/antigravity-host.md)。

- 将“规范要求”与“已实测行为”区分开，入口可见、普通问答、一次 plan-only 局部执行分别表述，不把小修/继续/收口列作全部已通过。
- 补列两个 workspace 检查，明确全局安装通过不等于项目绑定成功。
- 保留候选 `a9a0f95` 的实际 `--dangerously-skip-permissions` 条件，不将其推荐为默认 CI 配置。
- 明示 dogfood 项目 `MISSING_BUNDLE / broken`、首次绑定未保证及恢复/finalize/追问等未验证边界，行为项继续 `BLACK_BOX_NOT_VERIFIED`。

没有上调支持 tier、改 Doctor 行为、增加新命令/配置或把文档写成完整协议认证。

## 5. 验证与体验

- 隔离实验与历史对照均成功执行；30 条分支的结果与关键 pin、检查状态、本地 payload 缺席等断言一致。
- `git diff --check` 通过；仓库 diff 仅有 `docs/antigravity-host.md`。文档现有 recipe 链接仍指向存在文件。
- 本轮没有产品代码变更，未为文档改词新增测试或重复全量测试；验证重点是上述真实安装 API、已安装 helper、显式 init 和旧版对照实验。实验与报告均在仓库外；没有触碰本仓库 `.sopify` 或真实 home。

作为使用者：最容易误会的是“方案已 Ready”和“项目已启用”看起来像同一件事，而当前工具把两者分开了。现有绑定工具本身可用，缺的是首轮入口的明确调用与真实状态提示；单独修某个新宿主会掩盖共同问题。
