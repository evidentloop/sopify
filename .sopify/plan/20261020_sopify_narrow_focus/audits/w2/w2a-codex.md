# W2-A：T5 可选执行适配与 T3 入口压缩

**本派单范围已完成：先落 T5，再压缩 T3，源码、体积记录和 golden 已同步。** 全量 **386 passed, 97 subtests passed**，preflight 与 `git diff --check` 均退出 0。未 commit、push 或安装到真实用户 home；T3 的真实宿主 dogfood、T5 的完整交接链仍按方案交给 T7/T8、T9。

基线为 `feat/sopify-narrow-focus@a26a335b8660a4c0f40f224b2b2bbe12793c0ec1`，验证对象是该基线加本轮未提交改动。共修改／新增 **23 个仓库文件**，不含大脑的方案补充和 Trae 的 `docs/host-onboarding.md`。

## 1. 实测体积

单位为 UTF-8 字节。header 计规范模板；Copilot 计 `render_single_file()` 的实际内容，不含外层 managed block 标记。Copilot 已含 header，节省量不能再与 header 相加。

| 产物 | 压缩前 | 压缩后 | 减少 | 降幅 |
|---|---:|---:|---:|---:|
| 中文 header | 10,564 | **5,357** | 5,207 | 49.29% |
| 英文 header | 11,613 | **6,257** | 5,356 | 46.12% |
| 中文 Copilot | 41,941 | **27,690** | 14,251 | 33.98% |
| 英文 Copilot | 46,086 | **31,000** | 15,086 | 32.73% |

四项均落在本任务的目标范围。header 中英文均为 60 行；Copilot 中英文分别 627、626 行。

数据见 [metrics-after.json](./w2a-evidence/metrics-after.json)、[final-inventory.json](./w2a-evidence/final-inventory.json)；完整前后平铺产物保存在 `w2a-evidence/copilot-{zh,en}-{before,after}.md`。

## 2. T5 实施与真实任务单对照

新增英文 `docs/orca.md`，约定 owner、executor、reviewer 的职责、派单前检查、结果回传和 owner 写回。task packet 和缺陷 findings 均内嵌，未另建模板文件或中文重复文档。

已对照真实用过的 `task-codex-w1.md`、`task-codex-w2a.md`、`task-trae-t6.md` 收敛内容：

| 文档里的内容 | 真实任务单中的用法 |
|---|---|
| Task、Repository / baseline、Plan | 明确 W1/T1/T2、W2-A/T5/T3 或 T6；指向实际分支、SHA、方案路径及任务章节。 |
| Allowed / protected | W1 禁止真实 home、状态和 Git 写入；W2-A 避开 T4；T6 只允许新增一个文档。 |
| Check | W1/W2-A 有具体 pytest、preflight、diff 命令；T6 是明确的文档验收内容，不凭空加测试命令。 |
| References | 引用前轮报告、源码和适用证据；说明哪些事实可继承，哪些需要重新验证。 |
| Report、Return | 每单都有报告路径；Orca 注入合同或 T6 任务单给出确切回传命令。不能只在本终端说“完成”。 |

`plan_id`、`plan_version` 从已有方案解析、核对，不让用户填写另一份 manifest；packet 可携带 owner 已读到的值。继承证据和待重验项放入 References，不扩成独立状态系统。

派单前仍读四步入口，核对 handoff 主体、checkpoint、下一动作及适用版本；陈旧内容由 owner 经 writer 校正。worker_done 只是返回结果，不能当 verify pass；执行结果与独立复核分开，只有 owner 经现有 `sopify_writer` API 写回，Orca IDs、代码 SHA、命令和证据仍放既有 `evidence`。

按大脑补充，文档已提示：当前配置中 `worker-start` 不支持的宿主标签（如 Trae）需要手动 dispatch，并在任务单给出实际回传命令。这条来自协调者的本轮使用事实，未在本任务另行启动宿主复现。

阶段规则的双语变化：

- Develop 增加同一 UI/CLI/API 表面上的「最小复现与失败证据 → 根因 → 修复 → 同一复现验证」；不能复现要说明原因，单元测试不冒充原界面验证，不强制所有任务 TDD。
- Analyze 加一段可选 EARS 例子；Design 加一段可选 Added / Changed / Removed 例子。均明确不增加评分维度、必需章节或流程步骤。

先完成 T5 的源文件记录见 [t5-source-review.json](./w2a-evidence/t5-source-review.json)；之后才开始 header/flatten 压缩。最终 Develop 压缩版保留了该 bug 分支。

## 3. Header 删并及唯一详细来源

| 原内容 | 本轮处理 | 详细规则的来源 |
|---|---|---|
| 角色与五条宣传式理念 | 收为一段方案／证据职责；去掉无条件“无缝继续”承诺。 | header 的首段，只陈述入口职责。 |
| C1 配置流程、默认值大块示例 | 保留优先级、不自动创建、全部原默认键、品牌推导和 auto_capture 边界，改为紧凑说明。 | header 配置段；未改配置键或加载机制。 |
| C2 完整回复模板、状态／阶段名列表 | header 只留结果、证据、Changes/Next 和只读边界；通用格式集中到共享输出契约。 | `skills/{zh,en}/skills/sopify/references/output-contract.md`；阶段 assets 仅作示例。 |
| C3/A4 重复的文件数与复杂度门槛 | 从 header 删除，保留三模式及阶段路由。 | `analyze/references/analyze-rules.md`。 |
| A5 分级表与完整目录树 | 精确语义文件集合只留在受管入口；选择级别和知识目录职责不再重复。 | Design 负责选级；KB 的目录／保留政策负责长期文件职责。 |
| A6 生命周期细节 | 留 ready_to_archive 不等于归档、显式 finalize、writer 边界；初始化和同步不再复制完整列表。 | KB 初始化／knowledge_sync；Develop 完成态；正式 Protocol。 |
| A1/A2/A3 工具对照与 PowerShell 教程 | 合为 UTF-8、实际宿主工具和当前 shell 的通用原则。 | 真实宿主能力；未增加工具转换层。 |
| X1/X2 风险与 KB 策略 | 保留原风险档位语义及 full/progressive 选项，不新增审批机制。 | header 风险边界；KB 定义具体物化策略。 |
| 快速参考中的重复命令 | 删除重复一份，三个命令在入口保留一次。 | header 命令表。 |

六段关键协议保留原义及既有断言：意图优先、四步顺序、level 对应精确文件集合、plan_version、旧指针与 checkpoint、writer／非 active audit、并行推进信号。**首行 bootstrap 和末行方案包路径锚点保持**，W1 旧版迁移测试通过。

## 4. Copilot 与 Cursor

### Copilot

没有改加载方式，也没有改成只给外链：

- 删除平铺中的 Analyze/Design/Develop 发现元数据、导航和重复执行摘要，直接内联各自完整规则。
- KB/Templates 的规则在 SKILL.md 内，保留正文，只去 frontmatter。
- 不重复内联回复示例，输出字段由共享输出契约维护；仍内联 plan、tasks、design、ADR 四份文档模板，以及知识库文档结构。
- Develop 将重复总流程、字段展开和状态说明收成一套：八个验证字段、一次自动重试、五类根因、两阶段复审、知识同步、完成态和回滚边界均保留。
- 去掉 Project 模板里重复的目录职责说明，职责由 KB 维护；Design/Templates 不再要求读取未安装的 `assets/`。
- Copilot 不声明全局配置目录，因此平铺去掉该层路径；明确使用本文件的内联章节，不查找外部 Skill、来源路径或未安装脚本。

平铺语义断言覆盖保留的规则／模板、EARS/delta/bug 内容、writer 和 knowledge_sync，以及无脚本源码、无源树导航、无伪全局配置路径。

### Cursor

Rule 只做必要对齐：显式列出三个命令与 ready_to_archive 边界，读取统一输出契约，取消咨询不带 Changes/Next 的特殊例外，继续省略空章节。未复制通用长 header。

Rule 中英文大小为 **3,897 / 4,339 字节**。两个 `cursor-cli-skill.md.template` 经核对 **未修改**：仍先读取同一 Plugin Rule 再路由，缺失时不冒充进入 Sopify。支持档位及真实加载证据要求未变。

## 5. 修改文件

以下 `{zh,en}` 每项代表两个真实文件，共 23 个：

| 文件 | 变化 |
|---|---|
| `docs/orca.md` | 唯一新增产品文档，内含 task packet 与 finding 示例。 |
| `installer/hosts/base.py` | 仅调整 flatten：去重入口／回复示例、保留规则和文档模板、说明内联消费方式。 |
| `skills/{zh,en}/header.md.template` | 入口压缩，保留首尾迁移锚点及关键协议。 |
| `skills/{zh,en}/cursor-plugin-rule.mdc.template` | 命令、完成态和输出契约的小幅对齐。 |
| `skills/{zh,en}/skills/sopify/analyze/references/analyze-rules.md` | 可选 EARS 例子。 |
| `skills/{zh,en}/skills/sopify/design/references/design-rules.md` | 可选增量例子；模板归属不依赖未安装路径。 |
| `skills/{zh,en}/skills/sopify/develop/references/develop-rules.md` | bug 调查分支及同义规则去重。 |
| `skills/{zh,en}/skills/sopify/references/output-contract.md` | 承接通用格式和完整回复字段。 |
| `skills/{zh,en}/skills/sopify/templates/SKILL.md` | 去掉重复目录职责；保持文档结构。 |
| `skills/{zh,en}/skills/sopify/analyze/assets/question-output.md` | 只示例实际关键问题及影响，补完整 footer；移除凑三个问题和直接跳过追问的提示，与原分析规则一致。 |
| `tests/test_installer.py` | 通过实际安装产物检查 header footer 边界及共享契约详情。 |
| `tests/test_plain_language_contracts.py` | 核对实测值等于记录；检查平铺自包含和关键语义。 |
| `tests/test_plan_contract_assets.py` | 验证 Cursor 渲染后的命令、完成态、共享契约路径。 |
| `tests/behavior-scenarios/plain-language-output-v1.json` | 更新 copilot_after、新增 header_after；保留历史 baseline/source_revision/scenarios。 |
| `tests/golden-snapshots.json` | 显式更新已审查的 8 项内容哈希。 |

逐文件最终指纹见 [final-inventory.json](./w2a-evidence/final-inventory.json)。

## 6. 验证与快照审查

先在旧 golden／体积记录上验证：**9 failed, 131 passed, 38 subtests passed**；失败只来自 8 个内容哈希和旧 after 体积值，见 [before-snapshot-update.txt](./w2a-evidence/before-snapshot-update.txt)。

执行方逐项核对源差异、内联产物和协议断言后，显式运行 `scripts/regenerate-golden-snapshots.py` 更新 8 个哈希，并同步实测体积。审查记录见 [snapshot-review.md](./w2a-evidence/snapshot-review.md)；这不代替大脑或验收官的独立审查。

| 最终命令 | 退出码 | 结果 |
|---|---:|---|
| `python3 -m pytest tests -q` | 0 | **386 passed, 97 subtests passed in 41.39s** |
| `bash scripts/release-preflight.sh` | 0 | golden 24 项；全量再次 **386 passed, 97 subtests passed in 34.29s**；catalog、五个 protocol smoke、payload smoke 通过。 |
| `git diff --check` | 0 | 无输出 |

使用已安装 Python 3.11.15 / pytest 9.1.1，验证子进程设置 `PYTHONDONTWRITEBYTECODE=1`、`PYTEST_ADDOPTS=-p no:cacheprovider`。全量及 preflight 前后 index、golden 均不变；没有再次自动接受漂移。日志见 [full-suite.txt](./w2a-evidence/full-suite.txt)、[preflight.txt](./w2a-evidence/preflight.txt)。

## 7. 统一验收标准自查

- **不过度设计：** 未增 builtin Skill、dispatcher、命令、配置或运行态 schema；Orca 只新增一份说明文档，packet 取自真实任务单。
- **符合规范：** 双语树文件对称，writer/contracts 未改；沿用现有 renderer、输出契约和模板所有权。
- **不冗余：** 平铺只留一份阶段规则与输出要求，header 删除重复分级／目录／模板，文档模板中不再复制 KB 职责。
- **宿主一致：** 通用语义来自同一组源文件；Cursor 通过薄 Rule/CLI 入口复用，Copilot 按实际表面内联，不伪造树式读取。
- **不增加用户心智负担：** 无新增命令或必填用户表单；旧 header 自动迁移锚点保留；小修和咨询仍不自动接续方案。

以上为执行方自查；不把文件安装、静态断言或模型自述当作真实宿主行为认证。

## 8. 作为使用者的体验

这些来自我在本轮及前面 W1 执行中的实际经历，不是新功能提案：

1. **明确写集和回传路径比多一组字段更有用。** 我按 W2-A 的限制避开了 T4 和 Trae 文档；真实任务单里的“报告写哪里、怎么通知 owner”不可省略。因此本次 packet 补这两项，把继承证据／重验要求并入已有 References。
2. **过细的旧版本识别曾制造真实返工。** W1 初版用了历史指纹和独立 home block 逻辑，大脑审查后必须返工；本轮压缩继续保留锚点和共享实现，不再扩大机制。已有模板职责比再造一套压缩专用规范更合适。
3. **快照检查与接受变更必须分开。** 本轮先看到 9 项预期漂移，其余断言仍能独立判断；审查后显式更新更容易说明“接受了什么”，而不是让 preflight 自动变绿。
4. **命令成功的环境条件要在证据里说清。** 实际测试需要已安装的 Python 3.11；裸系统 Python 在 W1 曾没有 pytest。沿用同一解释器并记录环境足够，本轮没有据此增加安装器或配置层。
5. **协调者的新观察需要从真实回传读取。** 本轮通过 Orca check 收到 dogfood 补充，才将真实任务单和手动派单说明纳入文档。Trae 标签限制、旧 handoff 长期未更新及 writer 手写 Python 的失误是大脑记录的观察；我未亲自复现后两项，也没有据此擅加 CLI 或状态工具。

## 9. 保留边界与未完成项

- 大脑在执行中给方案补了 Dogfood 观察；该已知外部变更保留。我没有写 `.sopify/**`。除这份 owner 的 plan.md 外，其余受保护文件相对开始的指纹未变；index 与 HEAD 未变。
- Trae 新增的 `docs/host-onboarding.md` 未读取改写，也不计入本轮改动清单。T4 的脚本、protocol、blueprint、dev 文档及真实用户 home 均未修改。
- **后续仍需：** 大脑审 diff、验收官复核；T7/T8 真实宿主 dogfood 覆盖压缩后的入口；T9 共用真实冷启动交接链验证 T5。没有在本报告声称这些已通过。
- 本轮没有 Git 对外动作或 receipt 写回。T4 后续若继续改源文件／renderer，仍应按方案统一复核最终快照与体积。
