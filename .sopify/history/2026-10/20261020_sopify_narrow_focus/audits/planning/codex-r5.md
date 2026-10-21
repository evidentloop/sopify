# R5：冗余盘点、三档删减及需求评分审计

审计日期：2026-10-20。分支 `feat/sopify-narrow-focus`，HEAD `9d9b319cb06713f3f9d695bf98f629e50291bba3`。开始时已存在协调者完成的 Cursor 方案归档改动，本轮不修改这些文件、index 或 state，也不实施删除。

**推荐采用中等档：压缩高频入口，清走当前文档中的旧体系和私有残留，保留现有宿主、wire schema、已公开 Python 导出和可选 MCP 试点。** “新版”不自动等于撤销兼容承诺；不应为了少文件而删掉仍有使用路径的能力。

详细引用/最后修改记录见 [r5-inventory.json](./r5-inventory.json)，只读统计脚本见 [r5-inventory.py](./r5-inventory.py)。扫描覆盖 tracked 文件及本轮开始已有的 untracked 归档；调用方按现行代码/CI/测试/文档与 history 分开。字面引用为检索线索，**零引用不是死代码或可删素材的充分证明**。下面的体积目标和工时均为估算，未声称完成删减后的验证。

## 1. 宿主入口：逐节压缩，保留最小协议入口

当前 `skills/zh/header.md.template` 283 行、10,564 bytes；英文 11,613 bytes。主要问题是重复与入口责任过多，**不是 header 里还有可执行 runtime gate**。英文的 runtime context/variables 等普通词不能机械按“runtime 已退场”删除。

| 项 | 判定 | 证据与重复来源 | 最小处置、用户影响、成本 |
|---|---|---|---|
| 角色/核心理念，7–19 行，633 B | **[压缩]** | “AI 编程伙伴”“无缝继续”等宣传在 README/How docs 反复出现；新定位只需要说明什么时候应用可携带协议。 | 留一段意图优先与方案/证据职责，约 100–150 B；去掉无条件无缝承诺。非文件格式 breaking；随新版说明定位变化。<0.1 天。 |
| C1 配置/品牌，22–52 行，1,106 B | **[压缩]** | 默认值、品牌命名步骤及颜色说明占高频入口；`examples/sopify.config.yaml` 已是 tracked 配置示例。 | 保留优先级、语言/模式和“不自动创建配置”；详细品牌/颜色说明移到配置文档，保留既有配置键语义。目标 350–500 B。不要顺手重写配置系统。<0.2 天。 |
| C2 输出模板，53–94 行，1,228 B | **[合并]** | 与 `skills/zh/skills/sopify/references/output-contract.md:10-38`、各阶段 assets 重复。 | 入口只留结果/证据/Changes/Next 及 consult 只读边界；格式细节由 output-contract 唯一维护，约 200–300 B。更新相关静态断言，不能删实际结果/失败说明。<0.2 天。 |
| C3 模式+复杂度+命令，95–138 行 | **[压缩]** | 105–120 的文件数规则与 A4 重复；阶段分流还在 Analyze `references/analyze-rules.md:38-54`、级别在 Design `references/design-rules.md:20-26`。 | 保留三命令与 131–136 的意图、四步、版本、writer、并行信号核心；只把模式/分级细则指向阶段资源。C3 2,953 B 可约 2,200–2,600 B。不能压成只有链接而丢失第一跳边界。<0.3 天。 |
| A1/A2/A3 编码、工具映射、PowerShell，146–170 行 | **[压缩]** | A2 把宿主工具硬写为 Read/cat/Grep/grep 等；宿主已有工具 schema，且新宿主接入 recipe 将说明具体能力。 | 保留 UTF-8/遵循实际 shell 的短句；去掉通用命令对照和教程。把真正 host 差异写进接入 recipe，不做运行时工具转换层。约省 350–450 B。非 schema breaking。<0.1 天。 |
| A4 复杂度，171–178 行，185 B | **[删除]** | 与 C3 和 Analyze 相同；没有必要出现第三份文件数门槛。 | 从 header 删除；Analyze 继续拥有复杂度提示。0 行新机制，<0.1 天。 |
| A5 级别和目录树，179–205 行，1,158 B | **[合并]** | 精确语义文件集合已在 C3:133；目录职责在 KB:10-22、Templates 和 protocol 中。 | 留一份 level→语义文件映射，不重复完整 blueprint/user 树。约 250–350 B。plan.md 唯一入口必须保留。<0.2 天。 |
| A6 生命周期，207–215 行，567 B | **[合并]** | KB:24-33 管渐进初始化，Develop:170-176 管 ready_to_archive 与显式 finalize。 | 留“阶段按需物化，完成不等于归档，writer 负责状态”的边界；细则回原 owner。约 200–280 B。不能变成自动 finalize。<0.2 天。 |
| X1/X2 风险与 KB 策略，224–243 行 | **[压缩]** | 具体审批要受用户授权和宿主能力约束；KB 已有 full/progressive。 | 留授权边界与 KB 指针，不删用户已有风险/初始化配置语义；不新增权限引擎。约 180–250 B。<0.1 天。 |
| 阶段路由/Skill 列表，248–264 行 | **[保留]**（短化） | 250 行已明确 header 不复制阶段流程；catalog 是当前单一机器清单。 | 留必要路由、按需读取和缺入口降级；可约 400–550 B。新 host 需要这部分，不能只保留营销定位。<0.2 天。 |
| 快速参考，268–283 行，462 B | **[删除]**（重复部分） | 三命令已在 C3，目录/协议路径也已出现。 | 去重复命令和路径表，保持首次出现处可见。<0.1 天。 |

**[压缩] 目标预算：中文 header 约 4.0–5.5 KB、英文约 5.0–6.5 KB。** 这是按现有章节减重估算，不是已渲染结果；语义验证优先于凑字节。保守只去明显重复可先到中文 7–8 KB。Cursor 已有 3.8 KB 薄 Rule，不应为追求统一把它膨胀回通用 header；只做同义边界对齐。所有入口最后源码修改在 2026-08-30 release 版本同步，分发约束由 `tests/test_golden_snapshots.py`、`test_plan_contract_assets.py`、`test_installer.py` 覆盖。

## 2. Copilot：保留已发布 baseline，压缩平铺内容

**[压缩] 当前形态值得保留一个可用的自包含 baseline，不值得为减 20 KB 再开发一套新宿主加载器。** `installer/hosts/copilot.py:9-36` 只声明 prompt_install；`installer/hosts/base.py:252-308` 写项目 managed block，340–391 行把 header、共享 references、五个 Skill 及其全部 references/assets 顺序内联。R3 实测中文 41,941 B、英文 46,086 B。

| 内容 | 判定 | 证据 / 处置 | 影响与成本 |
|---|---|---|---|
| Skill frontmatter、触发描述、资源导航和多份完成输出框架 | **[合并]** | 五入口与后续 references 重复；flatten 中不存在“先发现该 Skill 再加载”的收益。render_single_file 已在 320–337 行专门去掉 tree-only scripts 导航，说明它已有表面差异处理。 | 平铺产物保留一份路由和一份输出契约。不得留下“去读未安装路径”的假渐进披露。约 0.5 天及既有 golden/安装测试更新。 |
| 多套长期 KB 文档正文模板、ADR 样例和可选说明 | **[压缩]** | `kb/SKILL.md`、`templates/SKILL.md`、Design assets 中目录/时机/模板解释重复；模板正文合计是可减部分。 | 留最小字段/章节结构和生成规则；可选长例不必全部预注入。现有文件语义不能丢，尤其 plan 必需章节、knowledge_sync 和 writer 边界。约 0.5 天。 |
| 主动删去全部阶段规则/全部 assets，只留外链 | **[保留]** 当前所需语义 | 当前 baseline 没安装可供读取的完整 payload。只有路径而文件不存在，会让平铺变成不可执行提示。 | 本版不以“Copilot 可能支持 Skills”推断已经可迁移；要换加载表面应另有实测。 |
| Copilot 入口/目标与用户 managed block | **[保留]** | `tests/test_installer.py:1374-1384` 直接验证用户规则保留；`docs/getting-started.md:128-140` 承诺当前入口。 | 删除 host 是用户可见 breaking；不纳入推荐档。移除整个 `.github/copilot-instructions.md` 也不能作为卸载方式。 |

目标为中文约 **22–28 KB**、英文约 **24–31 KB**，先利用 header 压缩，再去平铺重复。**产物节省已经包含 header 节省，不能重复相加。** `tests/test_plain_language_contracts.py:82-94` 还记录 Copilot 体积基线；改产物后要同步经审查的基线，不将字节完全相等当语义正确，也不通过自动刷新 golden 掩盖遗漏。

## 3. 协议与蓝图：让当前契约可读，保留历史证据

| 项 | 判定 | 证据、最后修改与依赖 | 用户影响、成本 |
|---|---|---|---|
| protocol 中 RETIRED runtime 列、EAR 旧字段、legacy mapping | **[压缩]** | `protocol.md:111-126,165,276-308,371-381,545-559`；最后 2026-07-19。旧 EAR 保留了已失效的 MUST 字段，和现行 §8 混读成本高。 | 当前文档缩成一段退场说明+已归档 P8/ADR 的定位，不改历史文件。约减 80–130 行，非 wire breaking；0.5 天。 |
| Producer/Knowledge Provider/Review Wire 的 informative-draft | **[压缩]** | §6 的 200–211、252–263 与 §7 的 407–424；均明确 draft/informative，不能当已实现能力。 | 当前规范只留 draft 状态和引用；有明确本版需求的 source/evidence 例子放现有模板。不要趁清理升格成新 schema。约减 30–50 行，0.2 天。 |
| Verifier normative、Subject Identity、四步入口、writer/finalize 边界 | **[保留]** | `protocol.md:213-250,316-369,383-405,426-541` 是现行声明；`tasks.md:131` 也明确清理不能改 §6/§7 normative 语义。 | 可改“旧进程”误导措辞并说明代码/host 分工，不能一见 Validator 就整节删除。改变其义务属于协议变更，超出“不改 schema”的最小范围。 |
| protocol 的陈旧“现役映射” | **[压缩]** | 334、377–379 行仍出现 current_plan/state.py/action_projection；现行 state 已两文件。 | 删除旧实现定位或标历史引用，保留规范语义。避免借此新增一个 Parser/Validator 进程。与上项同批。 |
| `blueprint/design.md` 714 行 / 52,956 B | **[压缩]** | 293–348、369–483、577–588、649–662 等明确 pre-P8/retired；最后 2026-08-29。现行架构、host capability、协议主体细则又与 protocol 重复。 | design 留模块、部署、所有权/取舍；规范细节链接 protocol，历史脉络链接已归档方案/ADR。预计减 250–350 行；约 0.5–1 天。保留关键决定及证据，不重写 history。 |
| `blueprint/skill-standards-refactor.md` | **[删除]** 当前入口 | 260 行 / 10,454 B，2026-06-10 最后修改；3–8 行已 deferred/dormant，33–35、63、126 等仍声称 runtime metadata/权限/eval gate 当前存在。仅当前 blueprint README:30 链接它，无产品代码依赖。 | 已落地的少量原则归 design/接入 recipe，未做事项只留有重访条件的一行；从当前入口删除旧全文，可从 Git 历史和原阶段档案追溯。不另复制一个同体积“归档新文档”。维护者说明即可，0.3–0.5 天。 |
| `blueprint/tasks.md` 已完成项、旧 compare/runtime roadmap | **[压缩]** | 118–119、127、135–140、142–164；最后 2026-07-20。Templates:101 规定长期 tasks 不保留已完成项，当前却仍大量记录已关闭工作。 | 只留未完成且仍符合本次定位的项；关闭/停止的项目用一行链接 history，不保留未来 runtime orchestrator 等失效候选。约减 50–80 行，0.2 天。 |
| ADR-013/016/017 与 history | **[保留]** | ADR 有具体决策与 P8退场边界，history 是核心承诺的证据本体；重复出现在当前说明不意味着原始记录冗余。 | 不批量去重/改写旧方案，不把历史删除计作瘦身收益。 |

## 4. scripts 全量调用方盘点

下表列出当前 **22 个 scripts 根脚本**。日期是 `git log -1` 的源码最后修改日期，不是本地 mtime；完整调用位置在 inventory。`保留` 行没有独立重构工时，正常随相关任务验证；删除/合并项需联动列出的调用方。

| 脚本（LOC / 最后修改） | 判定 | 现行调用方 / 证据 | 用户影响、工作量 |
|---|---|---|---|
| `_yaml_subset.py`（260 / 06-10） | **[保留]** | generate-builtin-catalog:17、test_plan_contract_assets:10。 | 真正的 stdlib 解析依赖，不能因是 helper 删除。 |
| `check-enhancement-declaration.py`（78 / 06-10） | **[删除]** | 现行 CI/代码/测试/文档无调用；25–29 行把 baseline 默认当成应有 CONTINUATION。本轮只读运行对 Copilot/Cursor 发 WARN 并始终 exit 0。 | 删旧 advisory，不删 capability enum/Doctor。内部维护面，无已发布 host breaking；<0.1 天。 |
| `check-install-payload-bundle-smoke.py`（252 / 06-10） | **[保留]** | CI:85、release-preflight:85、CONTRIBUTING、release-process:135。 | 发布安装主链证据，不能当旧 runtime smoke 删除。 |
| `check-readme-links.py`（311 / 08-30） | **[保留]** | test_check_readme_links:14、release docs、CONTRIBUTING。 | 文档删并后仍需要链接验证。 |
| `check-version-consistency.sh`（176 / 08-22） | **[保留]** | CI:17、preflight:59、release-sync:306、hook 和 tests。 | 版本/源码/文档对齐的发布约束。 |
| `generate-builtin-catalog.py`（113 / 06-10） | **[保留]** | CI:35、preflight:31；bundle/validate 仍要求 catalog 文件。 | 不用“runtime 已删”推断 catalog 可删；否则改 bundle 契约。 |
| `install-sopify.sh`（15 / 03-25） | **[保留]** | maintainer 入口、payload smoke:223，转发 install_sopify。 | 仅 15 行，删除一个有文档/测试的入口收益不足。 |
| `install_sopify.py`（320 / 08-22） | **[保留]** | 根 install.sh/ps1、distribution、inspection、多个安装测试。 | 本版修复和新 host 的主入口。 |
| `regenerate-golden-snapshots.py`（91 / 05-31） | **[保留]** | preflight:64、release-sync:309、release hook tests。 | 保留显式更新工具；校验器自动接受语义漂移的行为应调整，见第 7 节。 |
| `release-draft-changelog.py`（328 / 06-10） | **[保留]** | release-sync:13，test_release_hooks:260,348。 | 有实际 release 调用，不按 LOC 删除；本版不重做发版架构。 |
| `release-preflight.sh`（87 / 07-19） | **[合并]** 测试口径 | hook:122、release docs、tests；71–79 行仍是七文件白名单。 | 与 CI 同时改全量 tests，避免“CI 修了但 release 仍漏测”；不是新建第二个 gate。约 0.2 天并入 T1。 |
| `release-sync.sh`（311 / 08-22） | **[保留]** | pre-commit:123、tests；301–309 行更新四个版本源并再生成快照。 | 保留既有版本约定与回滚；不新增版本服务。 |
| `render-host-skills.py`（186 / 08-19） | **[合并]** 重复 parser | test_plan_contract_assets:89,122、host metadata 和 sync helper；32–98 行另写二级 YAML parser。 | 复用 `_yaml_subset.load_yaml(text)`；本轮对现有五 host 解析结果实测相等。约省 50–60 行，但仍需检查引号/null/bool 语义；保留 stdout/--output 调试入口。0.2–0.3 天。 |
| `render-release-installers.py`（80 / 05-22） | **[保留]** | release-process:92、test_distribution:603,628。 | 必须生成稳定 tag-pinned install assets，不能直接上传 dev root wrapper。 |
| `sopify_doctor.py`（40 / 03-24） | **[保留]** | getting-started:175、cursor-host:45、status_doctor tests。 | 用户诊断入口，行数小且有当前用途。 |
| `sopify_init.py`（361 / 06-10） | **[保留]** | install_sopify:41、getting-started:52、init smoke tests。 | bootstrap 功能仍在，不因提倡轻量就断现有安装路径。 |
| `sopify_mcp_register.py`（211 / 07-16） | **[保留]** 可选试点 | project.md:41、CONTRIBUTING 双语、223 行专属测试。 | 文档明确用官方 CLI 管用户持久配置；删除会让既有使用说明失效。暂不扩两个新 host，不并入默认安装。 |
| `sopify_mcp_server.py`（274 / 07-19） | **[保留]** 可选工具面 | register:118、project.md:40、blueprint/design:545、509 行专属测试；64、161、218–250 行提供 lite/read/write 工具。 | 已有注册/调用记录，不能当无人使用的死 pilot。删除需 MCP 迁移说明，列入激进档，不进推荐档。 |
| `sopify_protocol_check.py`（510 / 07-19） | **[保留]** | CI 五 smoke、preflight、MCP、tests；检查结构/禁用旧状态等现行约束。 | 保留行为检查；不拿静态通过冒充宿主真实行为。 |
| `sopify_status.py`（40 / 03-24） | **[保留]** | test_installer_status_doctor:28；inspection 的薄 CLI。 | 无 README引用不等于无外部用户，删 40 行不值得兼容变更。 |
| `sync-skills.sh`（99 / 05-27） | **[删除]** 推荐档 | 自己 10–19 行明确 local cache only；CONTRIBUTING:15 使用；hook:91 只是相关路径白名单，**不是实际调用**；test_release_hooks:150 将它复制进夹具。 | 以 render-host-skills 的 stdout/--output 替代，改开发文档/夹具/白名单，保留 ignore。属于维护者调试命令迁移，写简短 release note；0.2–0.3 天。 |
| `w33_qoder_proof.py`（405 / 07-19） | **[删除]** | 无现行调用；10–12 行明确模拟 A/B sessions，R3 已验证历史 proof 的局限。 | 保留 history 中原始 transcript；不删除 Qoder host。以已规划 T9 的真实样本承担新证据，不能把 405 行模拟改名当新认证。维护者 note，0.2 天。 |

**[保留] MCP 与原生文件协议并存，不构成默认依赖。** `.sopify/project.md:38-42` 已明确 repo-local/已有环境/非默认扩展；本版不扩 MCP、也不额外为它建立试点平台。若以后决定下线，必须处理既有客户端指向 repo 脚本的路径，不能只删 485 行脚本和 732 行测试后宣称零影响。

## 5. 文档、Pages 与图片

| 项 | 判定 | 证据与最后修改 | 最小处置、breaking/发布影响、成本 |
|---|---|---|---|
| README 中英文 | **[压缩]**，按需重写 | 226/223 行、11,731/11,017 B，08-30；职责与 How docs、getting-started、Pages 同时重复。 | 最后一次集中写“价值、一个安装/开始示例、已验证范围、证据/深入链接”；架构与详细安装留现有文档。不为了换定位重画全部图。无 schema breaking，0.5 天。 |
| `how-sopify-works*.md` | **[压缩]** | 两文件各120行，08-29；32 行与46–59行两次读链，63行重复整个 EvidentLoop 安装策略，104–112行又维护宿主表。 | 保留机制解释与目录/状态区别；安装策略链接 getting-started，宿主支持只保留必要语义而不复制表。约减40–60行/双语总计，0.2–0.3 天。 |
| `getting-started.md` | **[保留]** 并纠错 | 273行/10,695 B，08-29；承担安装/更新/诊断。128–140、218–219 的 Copilot未来承诺有旧日期；259–267 卸载示例直接删 `.sopify/` 和整个 Copilot 指令文件。 | 安装细节只在此维护；删除过时“将来会有”的承诺。卸载说明必须区分受管入口与用户计划/历史/已有指令，避免让使用者丢掉核心资产；只改文档，不另建 uninstall 工具。0.3 天。 |
| `docs/dev/development-guidelines.md` | **[合并]** | 81行/2,951 B，03-28；大部分通用 Git/topic/main 约定，41、71 行仍以 runtime 为例。 | 把少量项目特定规则并入 CONTRIBUTING，删除独立长文；发布步骤只链接 release-process。维护文档路径迁移需修链接，非用户协议 breaking。0.2 天。 |
| `docs/dev/release-process.md` 与 CONTRIBUTING 双语 | **[合并]** 重复步骤 | release-process200行，08-22；CONTRIBUTING各170行左右，07-16。release-process:23 仍声称有 skill eval gate，实际 preflight 没有；179–200 再重复完整流程。 | release-process 唯一拥有发版步骤，CONTRIBUTING保留入口/开发验证；去旧 eval 说明和二次长命令抄本，更新全量口径。0.3–0.5 天。 |
| `index.html / zh-CN.html` | **[压缩]** 事实内容，保留布局 | 275/268行、合计26,107 B，08-29；有价值、流程、支持清单、安装命令和 FAQ，多处和 README 重复。 | 本版必须同步定位/支持/安装事实，**不用重建网站、引入内容生成器或再造设计系统**；详细用法链接文档，保留现有布局和公共入口。0.2–0.5 天，Pages 文案变化需随 release核对。 |
| CHANGELOG | **[保留]** 历史，压短新条目 | 710行/25,792 B；release-sync、version guard 和release notes使用。 | 不删旧版本历史；本版新增用户可见结果、移除项/迁移说明，不抄完整审计/任务记录。 |
| `assets/` 未引用图 | **[保留]** 当前不能证明可删 | 扫描22图、4,141,317 B，无同 SHA 重复图；唯一无全文字面引用的是 `assets/readme-visuals/codex-dogfood.svg`，18,832 B。它与 GIF 同在 08-30提交 `0ccd58e` 新增，SVG:1、151表明其为可编辑图/动效解释源。 | 无引用只说明网页未直接加载，不能证明源资产无用；不把4 MB全部算作冗余。若以后正式放弃该源，最多省18.8 KB。当前保留，不重做配图。 |

## 6. 代码、测试、examples 与本地生成物

| 项 | 判定 | 证据 | 影响与工作量 |
|---|---|---|---|
| `sopify_writer/_resume.py` | **[删除]** | 84行，最后06-10；定义旧 active_run_stage/checkpoint resume 校验。全仓当前 Python 无导入或调用，writer `__init__.py:11-18` 不导出它，store也不使用；docstring“needed by ProtocolStore”已不实。 | 私有遗留，不改现行 JSON schema；删除后仍跑 writer/完整回归，不能称已完成删除验证。<0.2 天。 |
| contracts 的旧 Runtime/Decision/Proposal 模型群 | **[保留]** 本版；激进档候选 | core/artifacts/decision/proposal/handoff 的22个旧类约981 class LOC，除包内互引外无现行 Python 直接调用；但 `sopify_contracts/__init__.py:7-58` 公开导出。最后均在P8附近。 | 移除约1.0–1.1k行有价值，但会改公开 Python API；不能用内部零引用证明外部无使用。本版保持 schema/API边界，单列未来退役决定，不加兼容桥延长旧体系。 |
| `RuntimeHandoff`、`PlanPackageSnapshot`/inspect、skill_schema/catalog | **[保留]** | writer IO/store 使用 RuntimeHandoff；inspect 返回 Snapshot 即使外部没直接点名该类；catalog generator用 skill_schema，bundle/validate检查生成物。 | 此项说明零点名引用检测有局限，不能把它们与旧 RuntimeResult 一起删。 |
| installer 的 legacy bundle 读取分支 | **[保留]** | `validate.py:151-183` 支持旧 bundle布局；`tests/test_installer.py:995-1053` 明确验证；bootstrap:943–952也有旧manifest/标签路径。 | 是升级兼容面，不是已退场 runtime 执行。直接删可能让既有安装无法升级；需迁移证明后再决定，不进推荐档。 |
| bootstrap/helper 的独立 fallback 与重复常量 | **[保留]** | helper 可复制到用户目录单独运行，缺 repo import时有本地fallback；已有 test_bootstrap_helper_fallback_keeps_outcome_contract_in_sync。Cursor Hook同理。 | 不为减少几十行引入运行时包路径依赖。保留差分/一致性测试，别抽成不可部署的共享模块。 |
| tests 中对 retired 文件/旧状态的拒绝断言 | **[保留]** | `sopify_protocol_check.py:43-57` 的禁用面、writer/installer兼容测试在约束当前行为。 | “测试里出现runtime/legacy”不代表测试过期；不删负向边界以换绿灯。 |
| 只固定正文措辞/输出体积的断言 | **[压缩]** | golden snapshots 与 plain_language contracts 检查渲染字节/markers；`test_golden_snapshots.py:188-223` 会对多个 adapter调用 flatten helper，即使真实 Codex安装并不如此。 | 保留真实安装产物和核心语义负向测试；修改入口时让措辞断言跟随新职责，不保留无用户意义的逐句冻结。它们不是本轮可整文件删除的旧测试。约0.3天并入对应实现。 |
| `examples/external-repo-quickstart/` | **[合并]** | README132行，最后06-10；48–61、79–87、123–124 仍出现 .sopify-runtime/runtime_gate/旧卸载方法；10行 JSON example还有preferences_preload。被getting-started:271、README引用。 | 留一个短的“外部仓库开始/交接”示例，和T9共享讲述入口；删除失效 JSON样本或用真实当前产物替换，安装步骤链接getting-started。无需新demo app。约0.2天，无schema变更。 |
| `examples/sopify.config.yaml` | **[保留]** | tracked 76行/2,689 B；header C1明确指向它。 | 入口压缩后更需要一份可查配置说明；只清已退场注释，不删除配置兼容语义。 |
| 根 `Codex/`、`Claude/` 生成目录 | **[删除]** 本地缓存候选 | gitignored；本机各48文件，112,927+112,929 B；不是release源，CONTRIBUTING:15明确可重建。 | 可回收 **225,856 B** 本地磁盘，**发布包收益为0**；不要把它和改全局 `~/.codex`/`~/.claude` 混为一谈。本轮不删，<0.1天。 |
| `.orca/handoffs/final-pr-audit`、`final-title` | **[删除]** 空目录候选 | 两目录当前0文件，Git不跟踪，容量0；不是Sopify功能。 | 只能算本地收尾，不能作为release瘦身或功能任务，不需要新清理脚本。本轮不动。 |

## 7. 另两个应合入既有任务的发现

**[合并] 发布检查和快照写入职责。** `release-preflight.sh:61-66` 在 golden失败时自动 regenerate并 `git add`，而 golden测试注释要求确认变化后人工更新；`release-sync.sh:308-309` 又在合法版本变更后生成一次快照。应保留 regeneration工具及版本同步动作，让“检查失败”不能自行变成接受新语义；用已有显式生成/评审步骤承担更新。调整release-hook测试以保护回滚和用户index。是维护流程行为变化，需维护者release note，约0.3–0.5天；本轮没运行可能写仓库/index的preflight。

**[合并] 用户文件保留门槛必须落实到 T2/T4。** `brain-audit-r3.md` 的全局门槛6要求共享文件用managed block，但当前 `installer/hosts/base.py:234-236,394-401` 对home header仍整份write_text；Copilot才已有managed block。不能把“默认不覆盖现有用户AGENTS/GEMINI”等写进release宣传而不检查现有路径。最小做法是在触及的安装路径中区分Sopify受管块和用户内容，加入真实保留/重复安装/旧安装迁移验收；已有用户文件的处理是已定门槛，合入installer工作，不另造权限层。

**[压缩] 卸载文档与价值定位一致。** getting-started:259-267、quickstart:118-125直接删方案/历史和共享指令文件，与“资产随仓库走”和门槛6冲突。改成用户选择保留方案证据，移除受管入口；不新增自动卸载器。归档不是可随意删的缓存。

## 8. 三档删减方案

以下是**毛删减/目标预算**；未扣除必要说明、managed-block修复、负向回归等新增行。文档源、安装产物和本地缓存是不同口径，不能相加包装成一个虚大的节省数字。

| 档位 | 包含项 | 节省量/目标 | 风险、breaking | 估算工作量 |
|---|---|---|---|---|
| **保守** | 去header明显重复；删除 `_resume.py`、w33 proof、enhancement advisory；修旧术语/卸载/发版说明；保持Copilot形态、sync调试入口、全部公开API/MCP/宿主。 | 定点 **567行Python**（84+405+78）；中文header约10.6→7–8KB；文档约100–200行。可另清226KB本地缓存，发布包不因此变小。 | 无已声明schema/host breaking；私有/内部proof脚本移除写维护者说明。可能留下大量当前蓝图历史负担。 | 约1–2天，和已定T1/T2可重叠。 |
| **中等（推荐）** | 保守档 + 删除sync helper、合并renderer YAML parser；清掉当前skill-standards全文、收束design/protocol历史段；压缩header/Copilot；合并重复开发文档；README/Pages最后统一事实；保留正式历史、公开导出、MCP和现有宿主。 | 定点 **666行代码**（保守567+sync99），parser再约50–60行；中文header→4–5.5KB，英文→5–6.5KB；Copilot中文→22–28KB、英文→24–31KB；当前Markdown/HTML约减 **0.9–1.2k行/50–75KB**，是估算。 | 不改wire schema和host支持；**有维护者debug命令迁移**，并非“所有接口零breaking”。主要风险是删掉必要first-hop语义、golden误刷新、用户文件被覆盖；已有测试/最小真实场景负责约束。 | 约3–5天冗余/文档工作量，部分已经包含在T1/T2/T3/T4/T10，不能重复累计。 |
| **激进** | 中等档 + 清除公开legacy contracts模型；下线repo-local MCP及测试；撤销Copilot平铺或换新加载路径；大幅收束Pages/旧公开入口。 | 在中等档外，旧模型约1.0–1.1k生产LOC；MCP另485生产+732测试LOC；Copilot/Pages按最终选择另算，当前不伪造精确净收益。 | **breaking**：Python导出、已注册MCP路径、既有Copilot用户和文档URL。与本轮“不改contracts schema/保留已有能力”方向存在边界冲突，需要独立迁移与范围决策。不能仅因用户说“新版”自动采用。 | 至少另增3–5天兼容/迁移验证；不推荐混入本版。 |

推荐中等档，因为最大收益在“每次都读的入口”和“仍被当现行规范的旧文档”，而不是删除真实证据或可选工具。它能与已确认的六项共享一次全量回归、一次新host安装/加载验证和一次真实交接样本，不需要建立新的删减治理系统。

## 9. 与已确认任务的依赖及最小范围

| 依赖 | 处理方式 |
|---|---|
| T1全量CI与release | CI和preflight两处一起收敛为全量 `tests/`；保留catalog drift、protocol/payload smoke。不要只改CI。 |
| T2安装修复与入口压缩 | 先固定安装完整性/用户内容保留语义，再验压缩产物的重装、语言切换、旧内容清理；避免同一个目录连续迁移两次。 |
| Golden/文案测试 | 压缩必然改header/Copilot/Skill tree哈希和部分marker；由真实目标产物与核心行为审查后更新，不用自动regenerate掩盖失败。 |
| Trae/Antigravity | 直接消费压缩后的canonical入口，按实际能力做最薄投影；不要先复制10KB旧header、随后再改。验证入口/提问/缺文件降级和用户内容保护，各自取得证据。 |
| Orca/findings/task packet | 三者是一套可选bridge文档/Skill的不同章节或assets，合成一个交付物；陈旧handoff核对是接续步骤，不新建checker daemon/状态文件。 |
| T9真实交接 | 作为上述bridge/host工作的共享验收证据，不单独造演示产品或评测平台；结构单测与真实会话证据分别标明。 |
| 最后重写README | 按用户最新指令，合并原T6/T10的两次README写作，等已验证的支持范围稳定后一次收口；Pages只同步事实和链接，保留布局。 |

**[合并] 不必固定每波都增加一个用户审批。** 波次适合排序和汇报；真正改变范围、待用户拍板或未授权副作用时才停车。已经确认的可逆实现不应因计划机械分波重复确认；若用户明确要求逐波确认，则尊重该要求。

**[压缩] 统一方案包仍用 `plan.md + tasks.md`。** `brain-audit-r3.md` 的步骤2把standard写成“background/design/tasks”，与 `sopify_contracts/plan_package.py:11-16` 和当前模板不符。修正这处即可，不需新增文档；没有真实架构变更时不补design.md，不再预建审计空目录。

## 10. analyze-v1 的8/10：两段最小补充即可补满

本轮运行现有评分脚本，`3/2/1/2` 确实输出 **8/10**；假设下面的范围和完成条件被采用，`3/3/2/2` 输出 **10/10**。脚本只做确定性求和，不证明文字已经充分；当前草稿仍是8分，不能为了好看直接改成10。

### scope_boundary 1→2：建议直接补这一段

> 本版采用中等档删减：压缩入口和平铺重复，合并当前重复说明，删除已核实的私有残留/历史试验脚本与本地缓存；保留所有history证据、现有宿主目标、wire schema、公开Python导出、可选MCP及用户自有文件，不新增调度/锁/状态/内容生成框架。Pages随最终README同步已验证的价值、支持表、安装事实和链接，保留布局。Antigravity与Trae真实加载验收、T9真实冷启动接续都是本版范围内门槛；未通过先修复或由owner明确重定发布范围，不自动删宿主、降低证据要求或宣称已支持。

这段解决“删哪一档、哪些不删、Pages是否改、新host失败怎么办”，不增加新机制。维护者sync入口删除有替代命令和release note；公开API移除放下个明确breaking版本。

### expected_outcome 2→3：建议直接补这一段

> 完成为：已确认的可靠性修复及中等档删减通过同一全量CI/preflight和受影响安装回归，两个新host取得真实规则/Skill加载与负向边界证据，T9留下两执行身份、方案版本、起止代码SHA与真实验收结果。最终README中英文首屏说清保存什么、怎样开始和已验证边界，一个可复制安装/开始示例可用，证据/限制/深入文档可达，Pages事实一致；不以“吸引用户”或虚构30秒收益作验收。沿用现有 `YYYY-MM-DD.HHMMSS` build版本，版本源/badge/CHANGELOG一致；从获准交付的main提交生成匹配tag的stable安装assets，发布正式GitHub Release及latest，release notes列本版成果、维护者命令变更和迁移边界，最后从远端assets做隔离安装/来源版本核对。只有实际发布及post-release smoke完成才叫release完成，只有代码/文档就绪则写release-ready。

现有依据是 `docs/dev/release-process.md:25-33,85-144`、`scripts/render-release-installers.py`、version guard与payload smoke，不需新版本命名、发布服务或营销测量框架。Git/发布动作按上层已给出的授权和必要执行检查点处理，不能把已授权动作再包装成新审批交付物；本轮worker仍保持只读。

### [合并] v1中可减的交付物与下版本项

- #3 的bridge docs/Skill、findings、packet、stale检查合为一件可选适配；#4 recipe与两host共享一份能力/验收约定，不产生三份相同规范。
- #5 T9是#3/#4的真实验收证据，不另造工具线；#6冗余盘点是本次改动的白名单与删除记录，不需要长期新registry。
- #7 README/Pages/release是一条最终交付链，合并前后两次README工作，避免在能力未验证前写一次、验证后再改一次。
- EARS/Delta只是原分析/设计中可选例子，最多少量段落，不要求独立模板包、独立评测或额外级别；若挤占可靠性与真实交接验证，应推迟其完整样例，已批准的核心六项保留。
- 公开legacy contracts API清理、MCP下线、Copilot替换加载表面、Pages重建、自动历史迁移/清理放后续版本，不能以“凑满分”加入本版。

## 本轮验证与边界

执行了只读文件/调用方/最后提交统计、两种host YAML parser在当前五host数据上的等价检查、enhancement advisory观测和8/10→条件性10/10的评分算术检查；未删仓库文件，未运行会自动更新golden或git add的preflight，未把静态无调用方当删除后的测试通过。结束时对照 `r5-inventory.json` 验证：既有Git状态与全部归档改动内容哈希均未变，HEAD与分支未变，index仍无diff；报告、统计脚本/JSON是本轮唯一新增审计产物。
