# R7：新版 Sopify 方案可执行性审计

结论：**建议修改后执行。** 工作方向和 standard 包结构成立，T2→T3 的顺序正确；当前不能按“W2 文件边界互斥、W3 全部可并行”直接派单。主要问题是共享文件归属、T6 的循环完成条件、D1–D3 尚未落实到任务分支，以及候选版本与发布版本的验证边界。

审计日期：2026-10-20。仅审执行官职责，不替代验收官对定位、新手测试独立性和用户决策清单的判断。未改仓库、state、index，未操作 PR，也未执行安装或发布。

## 审计对象与证据边界

- 分支：`feat/sopify-narrow-focus`；HEAD：`9d9b319cb06713f3f9d695bf98f629e50291bba3`。
- 方案目录：`.sopify/plan/20261020_sopify_narrow_focus/`。
- `inspect_plan_package` 实测返回 `valid=True`、`level=standard`，版本为 `sha256:0a5cdbdc6a3a4d0c4dea96860b68ede4b8652041aebc88b18158a2a445b16003`。
- `plan.md` 101 行，SHA256：`80689867728cfbfb7161a92fcaa955b79c9a50db2d6ba19e3a6fc24ff8530d66`。
- `tasks.md` 64 行，SHA256：`fe3f7b1f2848b2f4a3c660ab7cc843527e94906cf11e6ab358d5972080b840b6`。
- 复核了现行安装、渲染、测试、发布入口以及 codex-r5；收口时已收到并读取 trae-r6。Trae 自检中的未验证项仍按未验证处理，本轮没有独立重跑其宿主实验。

以下位置未写目录时，均指被审方案的 `plan.md` / `tasks.md`；代码位置相对仓库根。测试建议是执行期验收要求，不是本轮已经通过的结果。

## 认可项

### A1 [认可] 包级别、实现边界和总体顺序

位置：plan.md:53、68–74、79–83；tasks.md:T2、T3。

`plan.md + tasks.md` 已满足 standard 的真实结构，不需要再补一个 design.md。保留 schema、公开 Python 导出、已有宿主、历史证据及可选 MCP，不新增调度器/锁/第二套状态，符合本轮范围。T2 安装语义先稳定，T3 再压缩产物，能避免重复迁移。

最小修改：保留这些决定；不要把后述共享文件问题解释成必须新增架构层或全面重构安装器。

### A2 [认可] T1 和 T2 的主要验收可落到现有命令与回归

位置：tasks.md:9–16；plan.md:38。

全量 pytest、真实 PR CI、golden 漂移失败且 index 不变、修前失败/修后通过、缺阶段文件后重装修复，均可验证。当前 CI 和 preflight 都是挑选测试文件；preflight 还会自动重生成并暂存 golden，T1 确实命中实际问题。四个 PR 测试文件与四个 xfail 缺陷是不同计数，方案写“四个测试文件”无误，见 codex-r1 第 1 节。

最小修改：T1 的 index 不变试验在隔离夹具/临时仓库做；T2 增加下述旧安装迁移矩阵。保留 `release-sync.sh:301–309` 在显式版本更新时同步模板和 golden 的职责，不能把它与“preflight 检查失败后自动接受新快照”一起删掉。

## 必须修订的执行缺口

### M1 [不认可] W2“文件边界互斥”和 W3 无条件并行

位置：plan.md:60–61；tasks.md:18、21、25、29、37、40、44。

当前任务名划分不能证明文件互斥。逐项检查如下：

| 任务 | 实际文件边界及顺序判断 | 最小落点 |
|---|---|---|
| T1 | CI、preflight、release-hook 测试；边界清楚。T4 也会改 release-hook 夹具，但已依赖 T1。 | 保留 T1→T4，不必另设任务。 |
| T2 | Cursor/common installer、distribution、writer IO、安装回归及卸载文档。 | 保留 T1→T2；共享安装器随后交 T3/T7/T8，避免并写。 |
| T3 | 不只有两个 header；Copilot 去重可能触及 `installer/hosts/base.py`、共享正文/资源、golden 和体积 fixture。 | 列出选定的去重文件；T2→T3 已解决两者先后冲突。 |
| T4 | renderer、蓝图、开发文档、hook 白名单/夹具。renderer 被 T3 的模板测试使用，可能与 T3 改同一 contract 测试；CHANGELOG 又与 T11 共享。 | 能并行的独立文档可先做；renderer/测试/生成物合入由同一执行者负责。 |
| T5 | Analyze/Design/Develop 源与资源是 Copilot 平铺和 Skill tree golden 的输入。 | 文档/packet 可先并行；阶段源合入后再形成 T3 的最终快照与体积证据。 |
| T6 | 新 recipe 文档本身可独立写。 | 修 M2 的完成条件后可前置，不需要等待安装实现。 |
| T7/T8 | 新模块与各自宿主文档能并行；注册、catalog、Doctor、共有测试不能视为互斥。 | 独立文件并行，公共接入由一个执行者串行合入。 |
| T9 | 真实 pending 任务仍会有代码文件修改；owner 写方案/receipt。 | 派单时给出所选任务的写集；不要和仍在修改相同文件的任务并发。 |
| T10 | 双语 README、两份 Pages；与 T4 的 How/开发文档原则上分开，链接须等相关文件稳定。 | 保持末尾执行，链接验收针对最终路径。 |
| T11 | 版本源、header、golden、CHANGELOG、发布资产及最终归档。 | 串行收口；冻结已验源码后再生成发布资产。 |

代码依据：

- `installer/hosts/base.py:340–391` 的平铺输入包含 header、顶层 references、五个阶段 SKILL 及其 references/assets，因此 T5 改动会改变 T3 的最终产物。
- 新宿主至少涉及 `installer/hosts/__init__.py:10–23` 的公共注册、`skills/hosts.yaml`、`skills/catalog/*/skill.yaml` 的 `host_support` 与生成 catalog。展示名还有 `installer/distribution.py:900–906`。
- `installer/inspection.py:330–332、383–384、422–423` 当前仅对 Cursor 构造 IDE/CLI 行为检查；若 T7/T8 要在 Doctor 显示安装/行为区别，必须明确共有检查层的责任，不能只写两个新 host 模块。

最小修改：删除“文件边界互斥”，加一段“独立文件可并行；公共注册、renderer/flatten、共有测试和生成物由指定执行者合入”。T3/T4/T5 合入后统一复核 golden/体积即可；不需要引入锁或另建编排系统。

### M2 [不认可] T6 的完成定义形成依赖循环

位置：tasks.md:34–35、41、45；关联 T5:31、T9:52。

T7/T8 依赖 T6，但 T6 要“T7、T8 都按 recipe 完成”才完成。如果按任务完成状态派单，两边都不能先过门。

最小修改：把 T6 完成定义改为“recipe、负向边界和可执行验收步骤已评审，可供 T7/T8 使用”；“两宿主实际遵循 recipe”放到 T7/T8 的证据中回填。无需拆新任务。

T5 的完整 Orca 实现/审查/receipt 链与 T9 可共享同一个真实样本。若选择共享，T9 的前置条件应是“T5 文档/packet 已可用”，而不是“T5 已跑完同一个闭环”；T5 最终证据随 T9 收口。当前两者并非必然循环，但不澄清会重复做样本或人为制造循环。

### M3 [不认可] D1–D3 选项没有形成相应任务分支

位置：plan.md:96–98；tasks.md:16、21、25、41–46、52、59、63。

| 选择 | 当前不一致 | 最小修订 |
|---|---|---|
| D1 保守/中等 | T4 写“档位按 D1”，但 T3 仍固定中等档 header/Copilot 目标。 | 用户选定后把 T3/T4 改成唯一实际写集和预算，不同时挂两套目标。 |
| D2 全宿主/仅新宿主 | T2 产物写范围按 D2，DoD 却始终要求现有 CLAUDE.md/AGENTS.md 安装保留用户内容。 | 列清本轮变更的 host/入口；未纳入的旧行为不得被记为已修复。 |
| D3 不阻塞/阻塞 release | “不阻塞”下 T7/T8 可能失败，但 T10/T11 仍无条件依赖所有任务完成。 | 区分“通过”与“已评估、按批准范围排除/延期”；后续依赖基于已裁定结果，不能把失败标成通过。 |
| T9 改用 Antigravity | 写了替代执行者，但仍只依赖 T8，没有声明替代路线要求 T7 通过。 | Trae 路线依赖 T8 的真实加载证据；Antigravity 路线依赖 T7；两者都未通过时按 D3 留失败结果或阻塞。 |

失败能力也要在实际交付面保持一致：列明是否保留为显式未验证/实验入口，或不纳入可安装目标；同步注册/能力标志、catalog、Doctor 和文档。只从 README 藏掉名称，不足以证明默认安装器没有继续暴露该能力。

这不是新增一个决策机制，只是把已有选择写成可执行条件。本审计不替用户决定 D3 应取哪一项。

### M4 [建议修改] T2 的旧整份安装迁移缺少可判定规则

位置：tasks.md:14–16；plan.md:97。

“managed block 并迁移旧整份安装”包含不同输入。现有 `_write_managed_block` 在没有完整 markers 时追加，有 markers 时仅替换第一块（`installer/hosts/base.py:415–441`）；直接复用会在旧整份 Sopify header 后再追加一份。`read_sopify_version` 只是找到版本标记（445–450），不能据此证明整份文件都归 Sopify 所有。

最小修改：在 T2 补一个短的迁移验收表，至少包括：

| 输入 | 期望 |
|---|---|
| 仅有用户内容、没有 Sopify 块 | 追加一块，保留用户内容；后续重复安装不增加块。 |
| 可确认的旧 Sopify 整份产物 | 迁移为单块，不留下旧规则与新规则同时生效。 |
| 旧产物混有用户内容 | 保留非受管内容；不能可靠识别的部分不做破坏性自动改写，并明确提示未完成迁移。 |
| 已有合法块 / 不完整或重复 markers | 合法块更新且保留外部内容；异常结构有明确拒绝或保守处理结果，不静默丢内容。 |

同时沿用损坏文件修复、语言切换、重复安装和用户其他 Skill 不受影响的回归。无需旧安装迁移数据库、新备份服务或新的权限框架。

### M5 [建议修改] 新宿主验收应绑定本次产物，先证明路径再承诺布局

位置：tasks.md:T3、T7、T8；plan.md:80。

“真实会话加载了规则/Skill”还缺候选版本身份。已有全局 Skill、旧会话的启动上下文或另一条安装路径，均不能证明新代码生成的产物已经生效。

trae-r6 现在已可读，但它明确写了：本轮没有安装；项目 AGENTS.md 没有正例；两层嵌套 Skill 未核实；trust 对加载的影响未核实。它支持 T8 从候选入口开始实验，不支持直接把“项目入口 + 扁平布局”当作本版已经验收。扁平化还可能需要调整阶段间相对路径和共享资源，不能只新增 `trae.py`。

最小修改：

1. T7/T8 先完成临时安装探针，确定规则、Skill 发现和资源引用路径，再定投影；重启/新会话要求按实际加载机制记录。
2. 每份会话证据记录宿主版本、候选代码 SHA、实际安装路径、关键文件 hash、加载/读取来源和行为结果；安装成功、catalog 可见、实际执行规则分别记事实。
3. T8 的 trust 对照写明不修改现有 `traecli.toml` 的实现方式，例如可用的已有不同信任状态工作区或宿主支持的隔离测试配置；当前没有可行方式时标未验证并按 D3 处理，不能静默突破禁止范围。
4. plan.md:80 明确“允许本任务安装的 Sopify 受管入口/Skill/payload，禁止修改账号、代理、工具 settings 与信任配置”，消除“全局配置”是否包含安装目标本身的歧义。

T3 可以先在已有支持宿主验证入口语义，Trae/验收官复核证据；不必反向等待尚未实现的 T7/T8。

### M6 [建议修改] 把 R5 的必要保留项和联动文件补进 T2–T4

位置：tasks.md:21、23、25、27；对应 codex-r5 第 1、6、7、9 节。

| 项 | 当前缺口与现行证据 | 最小补齐 |
|---|---|---|
| Copilot 双语体积实测 | T3 已说“体积基线”，但没有点明 fixture 和单位。`tests/test_plain_language_contracts.py:82–98` 只断言当前值和 `copilot_after` 各自小于旧 baseline，并不保证 `copilot_after` 等于新实测值。 | 明确同步 `tests/behavior-scenarios/plain-language-output-v1.json` 的实测 after 值，记录 CN/EN UTF-8 bytes；保留原始 baseline 的含义。中等档英文 24–31KB 可作 R5 预算参考，不用为了数字删语义。 |
| Cursor 薄入口 | T3 只列通用 header，Cursor Rule/CLI Skill 是独立模板。`test_plan_contract_assets.py:121–159` 验证薄 Rule 的路由标记。 | 补 `skills/{zh,en}/cursor-plugin-rule.mdc.template`、`cursor-cli-skill.md.template` 的语义对齐检查；无需把通用长 header 塞进 Cursor。 |
| legacy bundle 兼容 | plan 保留公开 contracts 不自动等于保留安装升级兼容。`tests/test_installer.py:995–1053` 明确覆盖旧布局与仅 active_version 的解析。 | T2/T4 写明保留这些兼容测试和独立部署 helper/Hook fallback；不能按“legacy”一词批量删分支。 |
| 删除后的链接 | 删除 standards 文件会留下 `.sopify/blueprint/README.md:30` 的现行链接。 | 把蓝图 README 索引列入 T4，而不只列 design/tasks。 |
| external-repo quickstart | T2 只明确改卸载；R5 指出的 runtime_gate、旧 runtime JSON 示例未明确归属。 | 合入 T4 清理当前无效示例，沿用现有示例目录，不新增演示应用。 |

“删除前后的引用检查无残留”（tasks.md:27）也需限定：当前执行入口、安装、测试、现行文档无失效引用；history/ADR 中的历史记载保留。否则与 plan.md:82 的不批量改历史冲突，且无法诚实达到“全仓零引用”。负向测试里对退役路径的禁止断言不算应删除的残留。

### M7 [建议修改] T10/T11 区分候选验收、正式发布和归档交付

位置：tasks.md:59、62–64。

T10 在发布前按 README 安装，如果命令指向 GitHub latest，取得的是旧 release，无法证明本次 README 和新版宿主适配有效。T11 的远端 smoke 是正确的最终门槛，不能提前用本地测试代替。

最小修改：

- T10 用明确候选 SHA/ref 验证同一安装流程和第一条 `~go plan`，记录“候选版本验证”；需要远端 ref 时使用根 `install.sh` / `install.ps1` 的既有能力。`installer/distribution.py:113–118` 明确拒绝 repo-local 安装的 `--ref`，不要写不存在的测试命令；当前 Python CLI 也没有 `--home-root` 参数。
- T11 发布后，按公开 README 的正式命令从远端安装，核对 tag、来源/版本和关键产物，再记正式通过。不要把旧 latest 安装成功当成本版证据。
- 更新 blueprint、writer finalize 会在合并/发布后产生新的 tracked 归档变化。T11 补一句这些收尾变化如何按 D4 交付：纳入获准的后续提交/PR，或明确列为尚未交付；不能代码已发就把本地未交付的归档也宣称完成。无需重打已发布 tag。

## 可合并或删减的工作

### O1 [建议修改] findings 只用于缺陷；正常任务证据保持简短

位置：plan.md:55；tasks.md:T5、T9。

每项任务都填写位置、复现、预期/实际和测试 ID，会让纯文档任务产生空字段。最低公共证据用“代码/方案版本、命令或会话、结果、证据位置、审查者”；实际缺陷再展开 findings。T5 与 T9 共享一次真实闭环，避免为了两个勾选重复造实现任务。

最小修改：改一行证据规则，并按 M2 调整 T5 的可用/最终完成条件，不新增报告格式系统。

### O2 [建议修改] T5 交付形式定一个，行政留言不进入技术完成定义

位置：plan.md:40；tasks.md:29、33。

plan 写“文档 + Skill”，tasks 写“可选 Skill 或 assets”，执行者仍需猜是否要新增可发现 Skill。建议选一份可选 Skill 入口配同目录 packet/findings 小模板，或明确只做文档/资源；无论选哪种，都不要自动把它变成第六个必装 builtin 或增加新 dispatcher。

T6 在 #55 留言是管理动作，不影响 recipe 可用性；D4 的文字授权目前列 commit/push/开 PR，并没有明确 issue comment。可移到 owner 收口时处理，得到对应授权后再留言，不让执行阶段为此停车。

## 验收如何落地

以下是在既有任务中补几项证据，无需新增测试平台：

| 范围 | 命令或真实证据 | 判定边界 |
|---|---|---|
| T1/T2/T4 代码回归 | `python3 -m pytest tests -q`；已有 release-hook 隔离夹具覆盖 golden 漂移和 index。 | 保存收集范围、退出码和实际 PR CI 链接；全量绿不能替代新迁移案例。 |
| T3/T5 产物 | 针对 golden/plan-contract/plain-language 的现有测试，加最终 CN/EN bytes 实测。 | 受影响源全部合入后更新并复核一次；快照一致不等于宿主实际加载。 |
| T6/T7/T8 | recipe 评审；每个宿主候选安装与独立启动记录；缺入口/缺 Skill/非受管内容保留的负向案例。 | 不把未验证的全局路径、嵌套发现或 trust 推断写成通过。 |
| T5/T9 | 一条真实派单→实现→独立审查→owner receipt 链。 | code SHA 和 plan_version 都记录；Orca worker_done 不能替代 verify。 |
| T10/T11 | 候选 README 安装记录、既有 link checker、正式远端资产 smoke。 | 候选验证与发布后验证分开；只凭本地文档就绪不能记 release 完成。 |

## 波次工作量

以下为有效工程人日，包含实现、受影响回归与交叉复核，不是多 agent 并行后的自然日承诺；不含用户决策等待、CI 排队和外部宿主故障。R5 的删减工作已计入，不能再叠加一次“中等档 3–5 天”。

| 波次 | 估算 | 主要变量与并行上限 |
|---|---:|---|
| W1：T1–T2 | 1.5–2.5 人日 | 旧整份文件混有用户内容的迁移最不确定；CI 与小缺陷修复相对直接。 |
| W2：T3–T6 | 2.5–4 人日 | 双语压缩、Copilot/Cursor 对齐、现行文档清理与 bridge/recipe；独立文档可并行，最终生成物须统一合入验证。 |
| W3：T7–T8 | 2–4 人日（两宿主合计） | 路径/Skill 布局需探针；独立模块与 dogfood 可并行，共有注册/Doctor/tests 串行整合。 |
| W4：T9 | 0.5–1 人日 | 复用 T5 闭环及剩余真实小任务；若失败需重新修适配，另计返工。 |
| W5：T10–T11 | 1–2 人日 | 文档、候选新手安装、版本/发布资产、远端 smoke 和归档交付；不包括批准等待。 |
| 合计 | **约 7.5–13.5 人日，排期可按 8–14 人日** | 按中等档与两宿主真实验收估算；D1/D2 改范围后同步重估，不承诺单一固定日期。 |

## 必须修改

1. **M1/M2**：撤销无条件互斥/并行承诺，指定公共文件与生成物合入责任；修 T6 完成定义循环。
2. **M3**：用户选择 D1–D3 后同步任务目标、失败/排除分支和 T9 替代依赖，不把失败写成完成通过。
3. **M4/M5**：补最小迁移输入矩阵；新宿主先验证入口/布局，真实证据绑定本次候选产物，trust 实验遵守现有配置边界。
4. **M6**：补 Copilot 双语实测 fixture、Cursor 薄入口、legacy 安装兼容及当前链接/示例清理；引用检查排除应保留的历史和负向断言。
5. **M7**：分开候选 README 安装和发布后的正式 smoke；说清 finalize 后归档变更的交付归属。

## 可选修改

1. **O1**：缺陷才用完整 findings；普通任务保留最短可追溯证据，并将 T5/T9 合用一条真实链。
2. **O2**：定清可选 Orca Skill/资源的单一交付形式；#55 留言交 owner 管理，不作为技术完成门槛。

本轮只做结构检查、源码/测试边界交叉阅读与只读 Git 检查；未重跑未修改的全量测试，也未运行会写 golden/index 的现行 preflight。审计期间已有的旧方案归档改动不属于本轮修改；本轮唯一新增产物为此报告。
