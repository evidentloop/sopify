# T6-Trae 完成报告：宿主接入 recipe

日期：2026-10-20  
仓库：`/Users/weixin.li/code/github/sopify`（分支 `feat/sopify-narrow-focus`）  
写入：仅新建 `docs/host-onboarding.md`；未改其他文件，未 commit、未 push。

## 写了什么

`docs/host-onboarding.md`（英文，222 行），按任务要求覆盖：

1. **能力矩阵**：入口（全局规则、项目规则、Skill）、Skill 发现（目录、嵌套、description 限制、重名优先级）、向用户提问、持久化与重启、缺席降级。每行都写了「要确认什么 / 怎么确认 / 缺失时怎么办」。
2. **先探针后布局**：临时工作区/隔离 profile、唯一 marker、fresh session 引用 marker、确定性动作验证、重启后复验；明确区分「已安装 / 宿主能看到 / 实际按规则执行」三类事实。
3. **负向边界**：不改账号、代理、模型、API key、宿主 settings、trust；共享 home 文件只走 managed block，复用 `upsert_managed_instruction_block` 和现有 `install_host_assets` 路径，不跨模块引私有 helper；问答和小修保持 direct，只有 `new_plan` / `continue_plan` / `finalize` / 明确 managed develop 才进方案流；baseline 不碰 hooks、MCP、launcher、runtime。
4. **证据字段**：宿主版本、候选分支/tag + SHA、`--target` 与实际安装根、entry/Skill/payload 路径、关键文件 SHA-256、会话记录路径、probe 工作区、trust/approval 状态、三类事实的分项结果。
5. **支持档位**：新宿主从 `BASELINE_SUPPORTED` 起步；`declared_features` 与 `verified_features` 分开；升级到 `PROTOCOL_VERIFIED` 需要 consult 只读、Analyze 真跑评分脚本、四步读链、writer 写回、checkpoint、跨 session resume、finalize 的可重复黑盒证据。
6. **最小测试模板**：自动化测试（host 专属测试 + installer / integrity / status-doctor / golden / contract 套件 + 全量 pytest + release preflight）和 7 个真实会话检查（可见性、consult、quick fix、new plan、resume、finalize、no-`.sopify/` 负向）。
7. **代码对应**：`installer/hosts/<host>.py`、`installer/hosts/__init__.py`、`skills/hosts.yaml`、`skills/catalog/*/skill.yaml` + 生成 catalog、`installer/distribution.py` 显示名、`installer/inspection.py` Doctor、README 支持表、host 专属文档、getting-started、测试文件。
8. **漂移检查**：安装后重算 entry/Skill 树 hash，跑 Doctor，跑全量测试与 release preflight；hash 不一致即停，不拿路径存在当通过。
9. **完成定义**：能力矩阵有证据、最小可用表面、保留用户内容、问答/小修不进流程、证据包齐全、tier 正确、host 文档与共享测试就位。

## 取舍

- **只写 recipe，不写具体宿主路径**：Trae 和 Antigravity 的真实路径分别由 T7/T8 探针回填；本文件只规定“怎么确认”，避免把 R6 的本机观察写成通用事实。
- **复用现有表面**：明确优先 `header_embedded` / `single_file` / `user_plugin` 三种现有 instruction surface，不新造配置或安装路径；确实没有合适表面时，才在 `base.py` 增加并补共享测试。
- **不复制 Cursor 文档**：Cursor 只作为 worked example 链接；负向边界和 IDE/CLI 证据分离引用 `docs/cursor-host.md`，不重复抄写。
- **不新增命令/脚本**：只用现有 `install.sh --target/--ref`、`scripts/sopify_doctor.py`、`scripts/release-preflight.sh`、`python3 -m pytest tests -q`，没有引入新的 compliance 脚本或配置项。
- **三事实模型是流程要求，不是新代码机制**：把「已安装 / 能看到 / 实际执行」写进证据包和 Doctor 语义，避免用文件 hash 冒充行为证据。
- **未在 README / getting-started 加入口链接**：本任务只允许新建一个文件，链接留到 T10 或后续 PR 统一处理，避免改其他文件。

## 待 T7 / T8 回填的项

### T7 Antigravity CLI

- 全局规则与项目规则的精确路径、优先级、trust 影响；
- Skill root 是 `~/.gemini/config/skills` 还是 CLI 专属目录，嵌套是否被发现；
- 提问工具的 tool name 与纯文本回退；
- Hook schema 与 Cursor/Trae 的差异（本期 baseline 不装 hooks，但负向边界要写清）；
- 重启/新会话要求；
- 按本 recipe 产出证据包和 Doctor check 名称。

### T8 Trae CLI 2.x

- `~/.trae/skills` 扁平 `sopify-*` 布局、顶层入口 Skill、description ≤1024；
- 阶段间相对路径与共享 references 在扁平化后能否读取；
- 两层嵌套是否被发现（只记录，不依赖）；
- trust 对加载的影响：只用已有不同信任状态工作区或宿主隔离方式，无法验证就写「未验证」；
- 全局 `AGENTS.md` 是否加载仍未证实，不能写成既定入口；
- 按本 recipe 产出证据包和 Doctor check 名称。

### T9 / T10

- T9：跨宿主冷启动续做的真实闭环证据；若失败，README 按 D3 去掉跨工具承诺；
- T10：把本 recipe 链接到 README 或 getting-started 的文档入口，并确保 `check-readme-links` 通过。

## 边界说明

- 本次只新建 `docs/host-onboarding.md`；`git status` 中其他 `installer/**`、`skills/**`、`tests/**` 改动和 `docs/orca.md` 是同一工作区其他任务的改动，我没有触碰。
- 没有修改账号、代理、模型、宿主 settings、trust，没有运行安装、没有 commit/push。
