# 技术设计: EvidentLoop 可选方案审计接入与 CrossReview 收口

## 设计目标

本设计只解决四个已确认问题：Sopify 方案入口与生成器不一致、CrossReview 当前执行面仍未退场、EvidentLoop 正式产物缺少可供通用消费者直接使用的版本值、用户选择配套安装时仍需手工执行两套安装。它不建设跨产品审计平台、通用依赖管理器，也不把 Sopify 工作流写进 EvidentLoop。

## 产品边界

| 层 | 负责 | 不负责 |
|---|---|---|
| EvidentLoop | 审计本地 Git diff，生成和修订正式报告，提供 `diff_version / report_version` | Sopify plan、blueprint、receipt、目录和默认触发 |
| Sopify | 生成和接续方案，计算 `plan_version`，决定审计是否成为方案证据 | 审查模型、diff 解析、finding 锚定和报告渲染 |
| Receipt | 关联方案版本、代码版本、报告版本及产物路径 | 自动授权、默认阻断或替代用户裁定 |

EvidentLoop 是独立产品，Sopify 是其通用能力的一个消费者。双方只通过正式报告和简明版本值连接，不增加专用 adapter 或共享运行状态。

Sopify 的默认能力是接收产品无关的 `verdict / evidence / source`，不是内置某个验证器。EvidentLoop 是官方推荐、完成真实 dogfood 的首个验证器，但不默认安装、不默认执行，也不排斥其他实现。

## 合法使用形态

| 形态 | Sopify 行为 | 安装所有权 |
|---|---|---|
| 仅 Sopify | plan、develop、handoff、receipt 正常工作；不运行外部审计 | 无 |
| 其他验证器 | 用户显式指定后按其 Skill/契约运行；正式证据仍可写通用 receipt | 该验证器自身 |
| 独立安装 EvidentLoop | 用户显式请求时直接做兼容探针并使用 | EvidentLoop 自身 |
| `--with-evidentloop` | 同一次 Sopify 安装中补齐缺失的官方 CLI 与 Skill；运行时与独立安装完全相同 | 安装便利由 Sopify 编排，产物仍归 EvidentLoop |

`--with-evidentloop` 不是 capability flag。Sopify 不记录“由谁安装”，也不以安装参数决定运行资格；运行时只认用户意图、当前可发现的 Skill/CLI 和兼容性证据。

## 可选配套安装

`--with-evidentloop` 面向 Sopify 的多宿主安装入口。直接在现有安装器增加一个布尔分支和一组 EvidentLoop 常量/辅助函数，并在现有 `HostAdapter` 增加标准 Skills CLI agent id；不抽象 installer component framework，也不另建宿主注册表。

当前 Sopify 宿主复用现有 `HostAdapter`，只增加下列 Skills CLI 官方映射和用户级全局发现路径：

| Sopify target | Skills CLI agent | 全局发现路径 |
|---|---|---|
| `codex` | `codex` | `~/.codex/skills/` |
| `claude` | `claude-code` | `~/.claude/skills/` |
| `qoder` | `qoder` | `~/.qoder/skills/` |
| `copilot` | `github-copilot` | `~/.copilot/skills/` |

Skill 安装固定使用 `-g`，不跟随 Sopify 核心资产的 workspace/global scope；兼容与结构探针也必须检查上表对应的 agent 全局发现路径，不从 Sopify `destination_dirname` 推导。这一点尤其适用于 Copilot：Sopify 核心资产可以是 workspace scope，EvidentLoop Skill 仍安装到 `~/.copilot/skills/`。后续 Sopify 新增宿主时，只有明确提供该映射才开放配套安装；缺映射只影响可选项，不影响 Sopify 核心安装。

安装分支固定为：

1. 未传参数：走现有 Sopify 安装路径；不查找 `uv / npx / evidentloop`，不访问 EvidentLoop 网络来源，不改变核心 payload、`stdlib_only` 依赖声明或安装成功语义；只在 help/文档中披露可选参数。
2. 已传参数：在核心写入前检查 target 是否有标准 Skill 安装映射，以及 `uv` 和 `npx`；缺映射或前置条件缺失时明确失败，不把可选依赖变成所有用户的基础要求。固定公开来源只用于随后安装缺失项，不建设额外远程解析层。
3. CLI 与 Skill 都缺失：使用本次 Sopify 发布中固定的 EvidentLoop package 版本、Git tag 和已验证的 Skills CLI 版本安装；Skill 命令固定带 `-g -a <agent> -y`，随后运行 doctor、兼容探针和目标 agent 全局发现路径的 Skill 文件校验；不调用浮动的 `skills@latest`。
4. 任一项已存在：先完成只读兼容检查；CLI 核对 package/schema/prompt 与必要命令，Skill 只核对目标 agent 全局发现路径的官方必备文件结构。兼容项复用，只安装缺失项。已有项不兼容时停止，既不替换已有安装，也不先安装另一半形成可预见的混合状态；Skill 是否被宿主真实发现仍由后续新会话 dogfood 证明。
5. 安装中途失败：报告已完成和未完成项；不删除刚安装的外部产物。相同命令可根据只读探针复用成功项并补齐缺失项，不增加 rollback manager。

所有外部安装调用使用固定版本/tag 组成的 argv，不拼接用户输入，不读取或输出凭据。Skills CLI 子进程显式关闭其匿名遥测，但不修改用户持久环境。用户显式传入 `--with-evidentloop` 即授权本次缺失项安装，但不授权替换已有不兼容安装。

安装成功只证明目标宿主具备 CLI 和 Skill 结构，不代表 Skill discovery 或审计已经运行。真实 E2E 由本方案在 Codex 上单独 dogfood；其他宿主沿用各自证据状态，后续可独立补证，不阻塞本次多宿主安装契约。

## 升级边界

本方案不自动升级、降级或卸载 EvidentLoop，也不新增版本范围求解和持久 component state。

- 用户按 EvidentLoop 官方方式独立升级后，Sopify 在下一次显式审计时重新执行兼容探针；通过即可使用，与最初安装来源无关。
- 再次运行 `--with-evidentloop` 时，兼容安装只复用；不兼容安装只报告当前值和本次 Sopify 已验证值，不自动改写。
- 后续 Sopify 发布可以更新自己验证过的 package/schema/prompt/Skill tag 常量，但“由 Sopify 自动升级已有 EvidentLoop”需等真实用户阻塞后另立任务。

这样保留未来升级入口，但当前不把可选安装便利扩张成包管理器。

## 方案包契约

| 级别 | 必备语义文件 | 适用场景 |
|---|---|---|
| light | `plan.md` | 单一目标、少量步骤 |
| standard | `plan.md + tasks.md` | 多任务、需逐项验收 |
| architecture | `plan.md + tasks.md + design.md` | 协议、状态模型、跨产品边界或架构取舍变化 |

`plan.md` 始终是唯一语义入口。宿主从 Plan Snapshot 取得目标、状态和下一步，需要执行时再读取 tasks，需要架构判断时再读取 design。缺少 `plan.md` 的 managed plan 无效；handoff 只提供恢复提示，不能覆盖方案文件。

`level` 必须写在 `plan.md` frontmatter，且文件集合精确对应上表：light 出现 `tasks.md` 或 `design.md`、standard 缺少 `tasks.md` 或多出 `design.md`、architecture 缺少 `tasks.md` 或 `design.md` 都是无效结构；方案根目录遗留的 `background.md` 同样视为结构不匹配。`audits/`、`receipts/`、`assets/` 和其他非语义附件不影响级别判断；history 中的旧方案不按新结构迁移或判错。

本方案调整方案版本、writer、入口预检和跨产品边界，因此使用 architecture 级别；不因级别名称自动创建 ADR、图、assets 或空 receipts。

## 方案版本

对外只使用 `plan_version`。它表示当前可执行方案的完整版本，不等同于单个 `plan.md` 文件版本。

计算规则固定为：

1. 先按 `level` 校验结构，再按固定顺序读取 `plan.md`、该级别必备的 `tasks.md`、`design.md`。
2. 每个文件按固定顺序写入“相对路径长度、相对路径、原始字节长度、原始字节”，避免路径与内容边界歧义。
3. 对完整输入计算 SHA-256，值使用 `sha256:<hex>` 格式。
4. `audits/`、`receipts/`、`assets/`、state 和其他文件不参与计算。
5. `level` 缺失、未知或语义文件集合不匹配时先判为结构无效，不计算部分版本。

底层算法写在规范和代码中，用户面只称“方案版本”。既有 history 和 receipt 中的旧名称、旧值不迁移。

实现只增加一个确定性计算函数，并由现有消费面复用：

- `workspace_status_lite` 增加一个 `active_plan_package` 客观事实，内部只含 `level / valid / error / version`。无 active plan 时为 `null`；结构无效时返回错误事实而不把整个 lite tool 判错。既有非法 active-plan state 仍沿用原错误行为。
- `sopify_writer.write_plan_receipt` 及现有同名 MCP wrapper 增加可选 `expected_plan_version`：写入前始终按共享函数重算，结构无效则拒绝；调用方提供的预期值不一致也拒绝。writer 自己把当前值固定写入 `provenance.plan_version`，调用方不得用 provenance 另造第二个位置。
- 现有 `ProtocolStore.finalize_plan` 收口既有非原子顺序，不新增第二个 finalize 入口：先按公共规则校验 `plan_id` 与 `YYYY-MM` 月份，再校验最终 `expected_plan_version`；writer 在源方案目录写 `receipts/final.json` 和待归档 `receipt.md`，确认语义文件未再变化后把整个目录迁到未占用的 `history/<YYYY-MM>/<plan_id>/`，仅在迁移成功后清理 active plan 与 handoff。写 receipt 或迁移失败时保留源目录和 state，拒绝覆盖既有历史目标。finalize checker 拒绝残留 state，并只对带 `plan_version` 的新归档复算版本；旧历史保持原样。history index 是归档后可重建的派生索引，由宿主随后更新；索引失败必须告警和单独重试，但不回滚已完成归档或恢复 state。
- protocol check 对缺失/未知 level、文件集合不匹配和版本不稳定给出失败项。
- entry-preflight 的并行推进信号比较 `plan_version` 或匹配 handoff，不再只观察单个文件。

host 仍按现有意图和 fail-open 表处理：consult/quick fix 不受无关 active plan 影响，managed continuation/finalize 遇到无效活动方案时停车。三个消费面复用同一计算函数和错误码，不各自解析 frontmatter 或实现哈希。

不增加版本 manifest、缓存、锁、state 文件或新 MCP tool。每次需要时对最多三个短文本文件重新计算，成本可忽略。

## 审计方式

本节是 Sopify 消费 EvidentLoop 时的目录约定，不是所有验证器必须实现的协议。其他验证器只需遵守已有通用 Verifier evidence 边界，并按自身产物格式提供证据。

### 独立审计

用户直接使用 EvidentLoop 审计 Git diff，沿用 EvidentLoop 默认输出目录。它不绑定 Sopify 方案、不写 Sopify receipt，也不影响 active plan。

### 方案主审计

用户显式要求把审计作为方案整体证据时，最终报告固定附着到：

```text
audits/plan/audit.json
audits/plan/audit.html
```

主审计必须写 plan receipt。报告本身不包含 Sopify plan 字段；receipt 负责关联 `plan_version / diff_version / report_version / audit_path`。

### 附加审计

用户可以按目的生成 `audits/<scope>/`，例如 `audits/security/`。目录名只表达用途，不创造 EvidentLoop 尚未提供的 `--focus` 能力。附加报告只有被明确采纳为正式方案证据时才写 receipt；否则不会出现在 4 步入口的默认读取链。

不使用 `overall`、自动编号、manifest、latest 指针或报告索引。Git 历史负责保存同一逻辑槽位的旧版本。

## EvidentLoop 通用版本能力

EvidentLoop 对外只新增两个语义名称：

- `diff_version`：本次实际 Git diff 的确定版本。
- `report_version`：正式 `audit.json` 原始字节的确定版本。

底层继续复用现有 SHA-256 计算，但字段名不暴露算法。新报告在 `finalize` 时把 `diff_version` 写入 `audit.json` 的 `extensions.evidentloop.diff_version`，并返回非空的 `diff_version / report_version`；`report_version` 不能写进自身，只在结构化结果中返回并允许消费者按正式 JSON 原始字节复核。

`revise` 不猜测已丢失的 diff 身份：带 `diff_version` 的报告原样继承该值并返回新的 `report_version`；既有 schema `0.4` 报告缺少该扩展时仍允许修订，返回 `diff_version: null` 和非空 `report_version`。Skill 对新报告要求两个版本非空，对 legacy revise 接受这一明确降级。需要覆盖 legacy `0.4`、连续两轮 revise、copy、in-place 和 recovery 路径，避免反馈修订兼容被新字段破坏。

新增字段保持 additive：不修改 code-diff schema 核心字段、不升级 schema 版本，也不迁移反馈 schema 已发布的 `source_audit_sha256`。EvidentLoop 不新增 `plan_id`、`plan_version`、Sopify 输出目录、receipt、plan/design profile、宿主 adapter、模型 SDK 或 provider 配置。未来出现第二种真实 artifact profile 时，再按 EvidentLoop 自身门禁扩展，不在本次预埋通用 target 平台。

## Sopify 消费契约

Sopify 只在用户显式请求 EvidentLoop，或用户在多个可用验证器中选择 EvidentLoop 时调用其官方 Skill。是否由 `--with-evidentloop` 安装不参与判断。正式主审计流程为：

1. 核对公开 CLI 和 Skill discovery，取得 package/schema/prompt 版本。
2. 先完成所有可能改变产品的测试、修复、残留清理、blueprint/protocol 同步和方案语义更新，再冻结“实现与契约 staged diff”及当前 `plan_version`。
3. 审计主体包含产品实现、测试、Skill/模板、当前 blueprint/protocol 和方案语义；排除 `audits/**`、`receipts/**`、忽略的报告目录及 finalize 的纯状态/归档差异，避免报告审计自身。
4. 在 Git 忽略的 `reports/` 中完成 `prepare → host review → finalize`，然后显式停车，把初次报告交给用户裁定；宿主不得自行认定“人工裁定完成”。
5. 用户反馈要求改变审计主体时，废弃旧结论并回到步骤 2；用户提交会改变报告裁定的有效反馈块时，宿主只按反馈确定性执行 `revise`；用户明确接受初始报告且没有有效反馈变化时，不调用 `revise`，直接使用 `finalize` 生成的正式报告对。
6. 将最终 `audit.json + audit.html` 附着到 `audits/plan/`，验证可搬移性；writer 以冻结时的版本作为 `expected_plan_version` 写未占用的 `verify_NNN` receipt。
7. 冻结后只允许报告附着、receipt 和 finalize 的机械状态/归档动作；任何非机械的实现或契约变化都使旧审计失效。finalize 前先完成任务/生命周期状态更新并冻结最终 `plan_version`；归档后复算语义文件，必须与 `final.json` 的 `provenance.plan_version` 一致。

`plan_version` 在所有 plan receipt 中只放 `provenance.plan_version`。本次 EvidentLoop 主审计的 `evidence` 使用现有对象，不建立通用 Review Wire，仅固定九个扁平键：`source`、`package_version`、`schema_version`、`prompt_version`、`run_id`、`review_status`、`diff_version`、`report_version`、`audit_path`；最终结论继续使用 receipt 顶层 `verdict`，不在 evidence 重复。`pass_candidate` 仍是 advisory 证据，不代表用户授权或自动放行。

其他验证器不需要生成上述 EvidentLoop 字段或 `audits/plan/` 报告对；若用户要求把其结论作为正式方案证据，宿主只按现有通用 `verdict / evidence / source` 与 `provenance.plan_version` 写 receipt。用户泛指“验证”且宿主明确知道有多个可用实现时，只询问一次使用哪个，不建立默认优先级或验证器注册表。

## 跨仓与发布边界

EvidentLoop 通用增强在其独立仓库建立最小方案、测试和发布证据；Sopify 方案只记录依赖和最终消费证据。跨仓执行前必须保护 EvidentLoop 现有用户改动，不在 Sopify 工作区直接修改或提交它们。

下一 EvidentLoop Alpha 必须在 tag、PyPI 和 GitHub Release 前再次取得用户明确授权。Sopify dogfood 只使用已发布安装物；doctor 成功不等于 Skill discovery 成功，源码 checkout 或 editable install 不构成公开版本证据。

## 失败与停车规则

- 方案结构无效、`plan_version` 不一致、目标 diff 变化或报告版本无法复核时，不写正式 verification receipt。
- 新报告缺少任一版本时不写正式 receipt；legacy 报告的 `diff_version: null` 只保证独立修订兼容，不能作为本方案主审计证据。
- EvidentLoop 缺少通用版本输出时，在跨仓 checkpoint 停止，不在 Sopify 内复制一套临时字段实现。
- 审计发现需要修改 EvidentLoop 产品语义、正式 artifact profile 或 Sopify 默认工作流时，列出证据并等待用户新决策。
- 发布未获明确授权时，只完成候选验证，不创建 tag、不上传 PyPI、不创建 GitHub Release。
- 未选择 `--with-evidentloop` 时，任何 EvidentLoop 缺失或不兼容都不得影响 Sopify 安装、doctor 或核心工作流。
- 选择配套安装但 target/前置依赖不受支持时，在安装写入前停止；已有不兼容 EvidentLoop 时不自动替换。
- 历史目录出现非预期修改时立即停止，不用批量迁移或重渲染掩盖差异。
- finalize 的 history 目标已存在、最终版本冲突、final/history receipt 写入失败或目录迁移失败时，不清理 active plan/handoff；history index 更新失败不属于上述阻断条件，不改变已经完成的归档事实。

## 图与 ADR 判断

现有 P8 入口关系不变，可选安装也只是 installer 到两个官方安装物的单向编排；上述表格与流程已经足够表达，不生成新图。当前决策由本方案 `design.md` 和后续 blueprint/protocol 承载，不新建 ADR；若实施中出现新的状态、调用方向或跨产品所有权，再重新判断。
