# Antigravity dogfood 证据只读交叉复核

结论：**部分认可**。真实安装、规则/Skill 可见、普通问答的只读样本、评分脚本执行和 writer 写 state 均有独立原始证据；不认可“完整、可重复、端到端闭环已经通过”的表述，也不建议据此将 Doctor 行为项升级为 pass。最重要的遗漏是：原始 Doctor 在 dogfood 项目中报告 workspace bundle 缺失、版本状态 broken，原报告只列了通过和 skip 项。

本轮日期：2026-10-21；候选 `a9a0f95`；当前仓库 HEAD 为 `4b27f170c9ef028678c301a09fde78566f1d72cf`，开始时干净；收尾只读检查发现并行变更：方案目录的 `plan.md`、`tasks.md` 及新增 `audits/w3/`、`audits/w4/`。本轮没有操作这些路径，不清理或覆盖其他执行方的工作。`a9a0f95..4b27f17` 仅修改 `docs/host-onboarding.md`，本轮用于比对的 installer、Skill 源及协议代码与候选相同。未重装、未启动 agy、未重跑会写临时项目的场景；未改仓库或 `~/.gemini`，仅创建本报告。Python 使用指定 3.11 并禁用 bytecode；原生会话 SQLite 采用 `mode=ro&immutable=1` 读取，未创建 WAL/SHM。

## 证据定位

- `SP`：本报告所在目录；被复核报告为 [t7t8-accept-gemini.md](./t7t8-accept-gemini.md)。以下行号指该文件当前版本。
- `G`：`/Users/weixin.li/.gemini/antigravity-cli`。
- `P`：`G/brain/32305d4c-9279-46dd-b590-343bdde7409e/.system_generated`。其中 `logs/transcript.jsonl` 记录验收官的实际命令与工具返回，`tasks/task-*.log`、`steps/<N>/output.txt` 保存原始输出。引用 `P step N` 指其 JSON 的 `step_index`，不依赖增长中的物理行号。
- 三个已结束子会话的原生 DB：加载 `e131ed45-14c1-475d-8e0a-659f58199411`；问答 `ed879a4e-a196-448a-b7e9-77775046cf85`；方案 `e613947c-9eab-4e70-b357-0b73fd1bc1a7`。均在 `G/conversations/<id>.db`，工具调用从 `steps.step_payload` 的实参及返回值核对；不以模型自述或内部思考替代工具证据。

## 1. 实际安装与候选逻辑一致：属实

直接读取 `~/.gemini/config/`，并与候选源码的渲染规则、源文件字节和既有 payload 校验器比对：

| 核验 | 结果 |
|---|---|
| `AGENTS.md` managed block | BEGIN、END 各 1 个；正文与候选中文 header 经阶段名/路径改写后的结果一致，块外无其他正文 |
| 五个 `skills/sopify-*` 阶段与共享 `skills/sopify/references` | 23 个源资源逐一比对，0 不一致；共享两文件只有一份，无嵌套 `sopify/analyze` 布局 |
| 引用抽查 | header 和阶段入口的 26 处反引号资源/路由引用全部可达；另核对 Analyze、Design、Develop 三条 `~/.../scripts/*.py` 路径，均存在。模板中的未来项目路径不作为已安装资源 |
| payload | `validate_payload_install` 通过；版本与 active_version 均为 `2026-08-30.001152`；bundle 的 19 个源码/catalog 文件与候选逐一一致；bootstrap helper 与 Copilot 资源亦一致 |

当前额外有 12 个 `__pycache__/*.pyc`，是 Python 运行缓存，不是候选部署清单里的源文件；不应把“安装后快照新增 48 项”误写成“现在目录永远只有 48 个文件”。两份安装快照中的全部 54 个 `config/**` / 根 settings 已记录文件，当前字节仍与安装后快照一致。

关键哈希：

- `config/AGENTS.md`：`ebda9ced599a99a461a8ef152dd73d2ba197618e2a1c88ecde85a881e1be77a1`
- `config/sopify/payload-manifest.json`：`fe1f7c65429c528d869befd5bb351b67315416d8d37d511969b159460c5d8fe0`

这是安装与物理可达证据；实际执行另见第 3、4 节。

## 2. “只新增 Sopify、用户技能/配置 100% 未动”：需拆开裁定

**属实：安装保护范围内，48 个新增文件都是 Sopify 资产；已有配置文件内容保持一致。** 自行重算两份 JSON：

```text
整个 ~/.gemini：pre=6663，post=6724
新增=61，删除=0，变化=22
其中 config/** + 根 settings.json：pre=6，post=54
该范围新增=48，删除=0，变化=0
```

其余 13 个新增及 22 个变化均为 `antigravity-cli/` 下的会话记录、DB/WAL/SHM 或日志，不能归因于安装器，也不能忽略后声称整个 `~/.gemini` 严格仅增加 48 个文件。因此原报告第 3.1 节的“严格仅限”若指整个 home，**不属实**；限定为安装配置范围则属实。

以下文件在前后快照均有记录、SHA-256 相同，本轮读取时也匹配 post：`config/hooks.json`、`config/hooks.json.bak`、`config/mcp_config.json`、根 `settings.json`、`antigravity-cli/settings.json`。这支持“这些文件内容未变”，不外推为快照范围之外的全部账号/代理/系统状态均已审计。

**无法核实：三项既有 Skill 的全部目标内容在安装前后 100% 不变。** 原始快照代码在 P steps 828、845 使用默认 `os.walk`，没有 `followlinks=True`，也没有记录 `lstat/readlink`。`anatomy`、`fire`、`fireworks-tech-graph` 是目录符号链接，三者及其目录内容在两份快照中均为 0 条，不能用这些 JSON 为它们提供内容哈希证明。

有补充的有限证据：P `steps/842/output.txt` 是安装前 `ls -la`，三项链接的名字与指向和本轮现存值一致；场景 1 的 catalog 也列出 anatomy 和由 fire 路径注册的 fireworks-tech-graph。可写“链接仍指向原目录、技能条目仍可见”，不宜写“所有目标文件经过快照核验、100% 未触碰/全部功能可用”。

## 3. 场景 3 是否真实通过 writer 写 state：属实；完整闭环说法不属实

临时仓库仍存在，不必仅依赖验收官摘要。

### 真实调用与最终文件

原生会话 `e613947c…` 中：

| DB step | 实际证据 |
|---|---|
| 2、7、8 | 读取已安装 Analyze 入口、Analyze rules 和 Design rules |
| 13、14 | 读取同一份共享 output-contract 和 shared-writing-dna，证明本次会话确实跨目录读取共享资源 |
| 18 | 执行安装后的 `score_requirement.py --goal-clarity 3 --expected-outcome 3 --scope-boundary 2 --constraints 2 --require-score 7`；工具返回 `total=10`、`pass=true` |
| 19 | 执行 `select_plan_level.py --file-count 1` |
| 59 | 用已安装 bundle 的 PYTHONPATH 导入 `ProtocolStore`；调用 `store.set_active_plan(...)` 与 `store.set_current_handoff(...)`，返回 `Protocol state successfully updated.` |
| 65、67 | 修正 plan 中被 Shell 展开吞掉的 `~go` 文本后，再次执行 `inspect_plan_package`；返回最终 `Valid: True Version: sha256:b6d98e...1272ffa` |

精确区分：step 59 的 `plan.md` 是 `Path.write_text` 生成，step 65 用编辑工具修正；**state 是 writer API 写入，不是 plan 正文也由 writer API 生成**。这符合语义文件与 machine truth 的写入分工。`writer` 字段自身可被伪造，独立确认来自上述实际调用及返回，而非仅看该字段。

本轮独立检查：

- `inspect_plan_package`：`valid=True`、`level=light`、`files=('plan.md',)`；最终版本完整匹配 `sha256:b6d98e634e447fdfd9f780ec96b4ddbf4522fc139a9256b89d09769ce1272ffa`。
- 8 个实际标题齐备。该 checker 只验证 level、精确语义文件集合与摘要，本身不验证全部 frontmatter 或正文质量，不能独自承担“所有格式合规”的证明。
- `active_plan.json` 仅 `plan_id`；`current_handoff.json` 的 `writer=sopify_writer`、`required_host_action=continue_host_develop`、路径与 plan 一致。两个 JSON 均通过对应 Draft 2020-12 schema 的独立验证。
- `calc.py` 仍是原始除法代码，本次确为 plan-only，没有完成开发/恢复/归档样本。

### 不能遗漏的运行条件与 Doctor 失败

最初普通 `agy -p` 的场景 3 没有产生方案：P `tasks/task-888.log` 明确返回 command 权限被自动拒绝，尽管命令退出码是 0。验收官随后以 `--dangerously-skip-permissions` 重试（P step 900，task-901），才得到上述成功执行证据。应保留这个条件，不能宣传默认 headless 权限下已无条件走通。

更重要的是，P `steps/964/output.txt` 是 **dogfood 项目**中的 Doctor 原始输出：

```text
summary.overall_status = fail
Antigravity.workspace_bundle_manifest = fail / MISSING_BUNDLE
Antigravity.workspace_handoff_first = fail / MISSING_BUNDLE
workspace_state.version_state = broken
workspace_state.workspace_pin = null
```

临时 `.sopify/` 目前确实只有 plan 与两个 state 文件，未见项目启用/绑定 bundle 的产物。不能据此声称完整初始化、接续和收口协议已经验证，也不能将失败泛化成安装器破坏全局 payload——全局 payload 的独立校验是通过的。缺失项目初始化/绑定是否构成产品缺陷，需后续单独验收裁决，本轮不修改或修复。

报告第 3.3 节及第 4 节的“完整、可重复、端到端闭环”“整个机器真相链路完全按协议闭环”均应降级。已证实的是：**在上述重试条件下，一次 Analyze/Design 读取、评分、light 方案生成及 writer state 写入样本成功**；不是全协议认证。

## 4. 场景 1 的“能看到”与“实际照做”：前者属实，后者该场景无法核实

可见性不只来自模型一句“我已加载”：

- 成功子会话 `e131ed45…` 的 `gen_metadata.data` 原始请求记录包含与现存 `AGENTS.md` **逐字节相同**的完整内容；五个已安装阶段 `SKILL.md` 的绝对路径也全部在请求记录中。
- P `tasks/task-866.log` 的最终输出逐段引用 managed block，并列出 5 个阶段名、路径和描述。原先 task-859 是网络 eligibility EOF，成功证据来自重试 task-866，应避免写成首次运行即成功。

该子会话只有用户输入/模型回答类型步骤，**没有工具调用**，任务本身也是打印规则与技能列表，没有要求执行确定性动作。因此，“已安装”和“宿主能看到”成立；用“能识别（语义全）”替换任务要求的第三项“实际照做”，不能算三事实齐备。不能将会话复述当成规则执行。

实际照做的独立证据存在于其他场景：问答子会话 `ed879a4e…` step 2 真实读取 `calc.py`，场景 3 真实执行评分及 writer。这可以组合说明若干具体行为已观察到，不能倒填成“场景 1 自身已验证完整工作流”。

## 5. 报告中的越界表述与应改措辞

| 原说法 | 裁定 | 最小纠正 |
|---|---|---|
| 第 3.1 节：严格仅新增 48 个文件、用户技能/配置 100% 未动 | 部分属实；全域和全部 Skill 内容保证不成立 | 限定“config 安装范围新增 48 项、已记录保护配置哈希不变”；Skill 仅报告链接/可见性，注明未跟随目标哈希 |
| 第 3.2 场景 1：三事实齐备 | 不属实 | 场景 1 只验证安装/可见；执行证据分别归到场景 2/3 |
| 第 3.2 场景 2：普通问答和小修均不进流程 | 问答属实；小修无法核实 | P steps 884、886 有问答后未创建 `.sopify` 和 Git 干净的历史返回；本次没有小修请求，删除“小修已实测”的外推 |
| 第 3.2 场景 4：静态与行为项分离 | 属实；不是全项 Doctor 通过 | 列出的安装 pass 与行为 skip 正确，同时补上两个 workspace fail；P step 962 的根仓库过滤输出也含两个 GLOBAL_BUNDLE_MISSING，不能略去 |
| 第 3.3 / 第 4 节：完整、可重复、端到端闭环，可以升级行为证明 | 不属实 | 改为一次带明确权限条件的局部 plan-only 行为样本；恢复、finalize、缺信息追问、多次重复性与健康 bootstrap 未验证，暂不据此自动 pass/升级 tier |
| 第 4 节：`--dangerously-skip-permissions` 作为标准 CI/preflight 推荐 | 无法由本样本推出 | 如实记录本次失败与重试条件；不要将一次绕过阻断的成功推广成所有环境的标准配置 |

附带审阅第 3.4 节：当前 AGENTS 仅包含自有块，删除整个文件在当前快照上不会丢块外正文，但给未来读者的 `rm -f AGENTS.md` 是无条件命令；若后续加入用户内容，就不符合注释中的条件。`sopify-*` 通配符也可能覆盖未来同前缀的用户 Skill。因此“标准清理绝不影响用户资产”不能作为一般保证，应按实际 owned 资产与 managed block 描述；本轮没有执行卸载。

## 6. 可进入 release notes / 宿主文档的结论

**可以写的具体事实：**

1. 支持 Antigravity CLI 的 managed `config/AGENTS.md`、五个扁平 `sopify-*` 阶段和一份共享 references，候选 `a9a0f95` 的实际部署与源一致。
2. 本机 fresh 会话确实接收了完整 header 和五项 Skill；一次普通代码问答读取目标文件后，没有创建 `.sopify`，历史 Git 状态干净。
3. 一次使用 `--dangerously-skip-permissions` 的 plan-only 会话，实际读取 Analyze/Design/共享资源，执行评分脚本，并以 writer 写入合规 state；最终 light 方案版本校验通过。
4. Doctor 明确区分安装文件检查与行为未知项；它本身不会因一次外部 dogfood 报告自动将行为项改为 pass。

**建议直接采用的短段落：**

> 在本机 Antigravity CLI dogfood 中，候选 a9a0f95 的规则和五项阶段 Skill 已被新会话发现；普通代码问答未创建 Sopify 状态。带显式工具授权放宽条件的 plan-only 样本实际执行了评分脚本，并通过 sopify_writer 写入 state。项目 bootstrap/bundle 健康检查仍有缺失，恢复、finalize、小修复及缺信息追问尚未验证；Doctor 行为项继续保留 BLACK_BOX_NOT_VERIFIED。

**必须保留的限制：**这是本机 CLI 与单次成功样本，不能外推 IDE、Trae、全部模型或默认权限配置；不能写“四大场景全部无条件通过”“完整协议闭环”“用户所有目录与设置经快照证实 100% 无变化”。可以记录已观察到的行为证据，不应让离线 Doctor 仅因已安装或这份报告变为 pass。

## 原始证据指纹

| 证据 | SHA-256 |
|---|---|
| `gemini-pre-install-snapshot.json` | `d948b36c574b110b6b4e2ad82c029cce24dbd3dd93eabbf6d696c408d82337ed` |
| `gemini-post-install-snapshot.json` | `201fd8d056ab9f3160ae4ae5761e48eff1f792966080239a6579e48bd04bb625` |
| 被复核报告 | `cfc2ed689b252bda32291ea35d736dce730ca2e8444af2bed063009fbcb86690` |
| 加载会话 DB `e131ed45…` | `b9b4bf3246a2f430edb827c66302f6c4a7cbdf43df1fa904ed08461dddb7386b` |
| 问答会话 DB `ed879a4e…` | `cd9079b745ef0ea3fb40d7606e148005e0e8ec4a8c237570585e687c4fd5fa6d` |
| 方案会话 DB `e613947c…` | `60359c8503ec4828ec28b9d57bccef0bf2958756a7eb2b4ab5d06de31ef82578` |

方案 state 指纹：`active_plan.json` 为 `afe8bb34541992a810ae32d6299caf953948a71310e9fd695dda59c4741202d3`；`current_handoff.json` 为 `37bafd0c01f2e50b101ea7f1d557c6277f9edf9b15dd3234cdf3dba658fb5498`。这些哈希固定本轮所读产物，不替代上述行为证据。
