# R6-Trae：Trae CLI 加载面自检（只读 dogfood 预检）

日期：2026-10-20  
宿主：TRAE CLI `traecli 0.209.1`（`trae-cli --version`，installation: public）  
工作目录：`/Users/weixin.li/code/github/sopify`  
模型：`DeepSeek-V4.1-Flash-1017`（`~/.trae/traecli.toml`）  
本轮未安装任何东西、未改 `~/.trae/`、未改仓库、未 commit。

## 结论先行

**有条件认可：Trae 适配应优先走「项目根 `AGENTS.md` + 扁平化的全局/项目 skill」，不要先碰 hooks。**

- **入口**：项目级最稳的是仓库根 `AGENTS.md`；全局最稳的是 `~/.trae/skills/<name>/SKILL.md`。`~/.trae/AGENTS.md`、`~/.trae/rules`、`~/.trae/user_rules` 在本机都不存在，且 2.0 CLI 文档没有承诺这些全局规则路径。
- **Skills**：本会话实际从 `~/.trae/skills`、`~/.trae/skills/.system`、`~/.agents/skills`、`~/.trae/cli/managed/skills` 四类 root 扫描；项目 `.trae/skills` 和 `.agents/skills` 在 Sopify 仓库里不存在，所以没有项目 skill 被加载。
- **Hooks**：本机只有空的企业 managed hooks；项目 `.trae/hooks.json`、用户级 hooks 都没有实际文件。最小适配不需要 hooks，且 hooks 另有 hook trust 门槛。
- **必须先验证**：两层嵌套 skill 是否真能注册、`~/.trae/AGENTS.md`/`~/.trae/user_rules` 是否被 2.0 读取、自定义斜杠命令在 2.0 的路径/格式、PreToolUse 的 CLI 工具名（是 `Bash` 还是 `RunCommand`）。

## 证据基线

本会话的系统注入上下文（`~/.trae/cli/sessions/2026/10/20/rollout-2026-10-20T14-31-48-01a15802-4ada-7852-b2f0-01996a5dfbdd.jsonl`，`world_state`）显示：

- `agents_md = {}`：**本会话没有加载任何 AGENTS.md 正文**。
- `plugins_instructions = false`，`environments_instructions = false`。
- `host_skills.body`：注入了 13 条可用 skill 目录，路径分别指向 `~/.trae/skills/.system/...`、`~/.trae/skills/orchestration/SKILL.md`、`~/.agents/skills/...`。
- 记忆正文来自 `~/.trae/cli/memories/memory_summary.md`（developer message 中明确列出该路径）。
- `turn_context`：`cwd=/Users/weixin.li/code/github/sopify`，`approval_policy=never`，`sandbox_policy=danger-full-access`，`permission_profile=disabled`。

运行日志（`~/.trae/cli/logs_2.sqlite`）对本会话给出：

```text
skills config cache hit cwd=/Users/weixin.li/code/github/sopify root_count=11 skills_count=14 errors_count=0
```

即：11 个 skill root，14 个已加载 skill，0 个错误。下面逐题回答。

---

## 1. 全局规则：TRAE CLI 自动加载哪些全局指令？

**结论：本会话没有加载 `~/.trae/AGENTS.md`、`~/.trae/rules/`、`~/.trae/user_rules/` 中的任何内容；实际加载的“全局上下文”是 memory 和 skill catalog。**

证据：

1. 路径不存在：
   ```text
   ls: /Users/weixin.li/.trae/AGENTS.md: No such file or directory
   ls: /Users/weixin.li/.trae/rules: No such file or directory
   ls: /Users/weixin.li/.trae/user_rules: No such file or directory
   ```
2. 本会话 `world_state.agents_md = {}`，且没有 rule/instruction 注入块。
3. `~/.trae/cli/rules/` 存在，但它是 **exec-policy `.rules`** 目录，不是指令规则：
   ```text
   DEBUG codex_core::exec_policy: loaded 0 .rules files in /Users/weixin.li/.trae/cli/rules
   DEBUG codex_core::exec_policy: loaded rules from 0 files
   ```
   目录内只有 `.rules-migrated` 空标记，没有规则文件。
4. 官方文档对 AGENTS.md 的加载机制写的是“当前目录与上级目录中的 AGENTS.md 会始终加入上下文”（[TRAE CLI 记忆](https://www.volcengine.com/docs/86677/2227867)）。按这条规则推断，`~/.trae/AGENTS.md` 不在项目目录的上级路径上，不应被自动加载；但这是文档推断，**没有用存在的文件做正例验证**。
5. IDE 的全局规则文档写的是 `~/.trae/user_rules`（[Rules](https://docs.trae.ai/ide/rules)）；CLI 1.0 文档写的是“个人规则 `$HOME/.trae-cn/rules`”（同 1 的链接）。本机 `~/.trae/user_rules`、`~/.trae-cn/rules` 都不存在，**2.0 CLI 是否读取 `~/.trae/user_rules` 无法核实**（没有文件可做正例，且禁止创建）。

实际加载的全局面：

| 面 | 路径 | 证据 |
|---|---|---|
| 记忆 | `~/.trae/cli/memories/memory_summary.md` | developer message 的 Memory 段 |
| 系统 skill | `~/.trae/skills/.system/skill-creator/SKILL.md`、`~/.trae/skills/.system/skill-installer/SKILL.md` | `host_skills.body` |
| 用户/全局 skill | `~/.trae/skills/orchestration/SKILL.md`、`~/.agents/skills/*/SKILL.md` | `host_skills.body` |
| 指令规则 | 无 | `agents_md={}` |

**适配含义**：不要把 Sopify 的全局入口写成 `~/.trae/AGENTS.md` 或 `~/.trae/rules`；全局入口应做成 skill（或 memory），除非真实安装后验证了 `~/.trae/user_rules`。

---

## 2. 项目规则：仓库 AGENTS.md / CLAUDE.md / .trae/rules 是否加载？依赖 trust 吗？

**结论：本仓库没有这些文件，所以没有项目规则被加载；本目录已是 `trust_level = "trusted"`，但因为没有规则文件，无法用本仓库实测“trust 是否是加载前提”。**

证据：

1. 文件不存在：
   ```text
   ls: /Users/weixin.li/code/github/sopify/AGENTS.md: No such file or directory
   ls: /Users/weixin.li/code/github/sopify/CLAUDE.md: No such file or directory
   ls: /Users/weixin.li/code/github/sopify/.trae: No such file or directory
   ```
   仓库里也没有 `.agents/`。
2. 本会话 `world_state.agents_md = {}`，再次证明没有 AGENTS.md 正文被注入。
3. `~/.trae/traecli.toml` 明确记录：
   ```toml
   [projects."/Users/weixin.li/code/github/sopify"]
   trust_level = "trusted"
   ```
   所以“目录刚被信任过”这一点成立；`turn_context` 也显示当前是 `approval_policy=never` / `permission_profile=disabled`。
4. 官方文档说 AGENTS.md 的加载是“当前目录与上级目录始终加入”，并未把 trust 写成 AGENTS.md 的加载前提；trust 主要用于工作区/工具权限。Hooks 则是另一套 hook trust（见第 4 题）。
5. **未核实**：`trust_level` 从 `untrusted` 变为 `trusted` 时，AGENTS.md / `.trae/rules` 的加载行为是否不同。本仓库没有规则文件，无法构造对照；且任务禁止修改仓库。

**适配含义**：项目级入口可以放心用 `AGENTS.md`，但要在真实安装后用“有文件/无文件”两组会话确认 trust 的影响。

---

## 3. Skills：可用列表来自哪些目录？两层嵌套能否发现？

**结论：本会话的 catalog 来自 `~/.trae/skills`（含 `.system`）、`~/.agents/skills` 和空的企业 managed skills；项目 `.trae/skills` 没有被加载，因为仓库里没有这个目录。两层嵌套没有可对照样本，按保守策略应先扁平化。**

实际扫描的 root（日志原文）：

```text
skills root scan complete root=/Users/weixin.li/.trae/cli/managed/skills scope=Admin visited_dirs=1 parsed_files=0
skills root scan complete root=/Users/weixin.li/.trae/skills scope=User visited_dirs=2 parsed_files=0
skills root scan complete root=/Users/weixin.li/.trae/skills/.system scope=System visited_dirs=7 parsed_files=3
skills root scan complete root=/Users/weixin.li/.agents/skills scope=User visited_dirs=76 parsed_files=9
```

说明：

- `~/.trae/cli/managed/skills` 是 Admin root，本机为空。
- `~/.trae/skills` 下有 `orchestration -> ../../.agents/skills/orchestration` 的符号链接；catalog 中 orchestration 的路径写的是 `~/.trae/skills/orchestration/SKILL.md`。
- `~/.agents/skills` 是实际用户 skill 的主来源，catalog 中 anatomy、archify、beautiful-feishu-whiteboard、computer-use、evidentloop、orca-agent-tab、orca-cli、orca-update、read-book、zh-tech-writing 都指向这里。
- Sopify 仓库的 `skills/` 不是 `.trae/skills`，也未被当作 skill root；catalog 中没有 Sopify 相关条目。

### 两层嵌套

- 文档只承诺 `skills/<skill-name>/SKILL.md` 这一层：`~/.trae/skills` / 项目 `.trae/skills`（[Skills](https://docs.trae.cn/ide/skills)、[TRAE CLI 技能](https://www.volcengine.com/docs/86677/2272059)）。
- 运行日志显示 loader **会递归遍历目录**（`~/.agents/skills` 的 `visited_dirs=76` 远大于顶层 skill 目录数），但本机没有任何 `skills/a/b/SKILL.md` 形式的样本，**两层嵌套是否会被注册为独立 skill 无法核实**。
- 保守结论：**Sopify 的 `skills/zh/skills/sopify/analyze/SKILL.md` 这种两层布局不能当作已被支持**；先渲染成 `skills/sopify-analyze/SKILL.md` 这类一层结构，再在真实安装后做嵌套实验。

### 一个真实坑：skill 会被加载但不进 catalog

本会话 `skills_count=14`，但 `host_skills.body` 只列了 13 条。最可能的差异项是 `~/.agents/skills/luna-exec`：它是本机唯一一个 `SKILL.md` frontmatter 合法、但没有出现在 catalog 里的顶层 skill，且带有：

```yaml
# ~/.agents/skills/luna-exec/agents/openai.yaml
policy:
  allow_implicit_invocation: false
```

**推断（未核实）**：这个 policy 让它被加载但不进入“可用 skills”列表。若属实，Sopify 希望被模型自动发现时就不要设置 `allow_implicit_invocation: false`；真实安装后应做一次对照验证。

另一个长度限制信号：历史日志里出现过

```text
failed to load skill /Users/weixin.li/.agents/skills/orchestration/SKILL.md:
invalid description: exceeds maximum length of 1024 characters
```

说明 `description` 有 1024 字符上限；Sopify 的 skill description 应控制在 1024 以内。

---

## 4. Hooks：配置位置、事件名、PreToolUse 输入输出

**结论：本机只有“企业 managed hooks”文件且全为空；项目级 hooks 路径在二进制里是 `.trae/hooks.json`；用户级 hooks 路径没有实际文件，2.0 的准确位置未核实。最小适配不需要 hooks。**

### 已观察到的位置

| 位置 | 状态 | 证据 |
|---|---|---|
| `~/.trae/cli/managed/hooks.json` | 存在，14 个事件数组全为空 | 文件内容 |
| `~/.trae/cli/hooks/commit-attribution/...` | 存在，但这是 **git commit-attribution 的 git hooks 模板**，不是 Agent hooks | 文件头 `#!/bin/sh`、`TRAE_GIT_ATTRIBUTION_HELPER` |
| `~/.trae/hooks.json` | 不存在 | `ls` |
| `~/.trae/cli/hooks.json` | 不存在 | `ls ~/.trae/cli` |
| 项目 `.trae/hooks.json` | 仓库中不存在 | `ls /Users/weixin.li/code/github/sopify/.trae` |
| `.trae/hooks.json` 字面量 | 二进制中存在 | `strings traex \| grep '.trae/hooks.json'` |

官方文档（IDE Hook 配置）给的位置是 `~/.trae-cn/hooks.json`（全局）和 `$PROJECT_FOLDER/.trae/hooks.json`（项目），并支持合并 Claude Code 的 `~/.claude/settings.json` / `.claude/settings.json`（[Hook 配置详解](https://docs.trae.cn/ide_hook-configuration-reference)）。这页是 IDE 文档，CLI 2.0 的用户级路径**未核实**。

### 事件名

`~/.trae/cli/managed/hooks.json` 里出现 14 个事件：

```text
PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure,
Notification, SubagentStart, SubagentStop, PreCompact, PostCompact,
SessionStart, SessionEnd, UserPromptSubmit, Stop, Interrupt
```

IDE 文档只详细写 6 个（SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Stop / Notification），CLI 的 managed schema 是超集。`features list` 中 `hooks stable true`，`turn_context` 的 features 也包含 `CodexHooks`，说明本会话 hooks 能力是开着的，只是没有配置。

### PreToolUse 输入/输出（官方文档字段）

stdin 通用字段：

```json
{
  "session_id": "string",
  "cwd": "/path/to/workspace",
  "hook_event_name": "PreToolUse",
  "workspace_roots": ["/path/to/workspace"]
}
```

PreToolUse 专有字段：

```json
{
  "tool_use_id": "toolcall-id-string",
  "tool_name": "RunCommand",
  "llm_tool_name": "RunCommand",
  "tool_input": { }
}
```

stdout：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "决策原因说明",
    "updatedInput": { },
    "additionalContext": "附加给模型的上下文"
  }
}
```

`permissionDecision` 可选 `allow` / `deny` / `ask`；另有通用 `continue` / `stopReason`。退出码 `2` 等价于 `deny`，`stderr` 作为原因进入模型上下文；其他非 0 退出码为非阻断错误。文档：[Hook 配置详解](https://docs.trae.cn/ide_hook-configuration-reference)。

**必须注意**：这页文档的标准化工具名是 IDE 的 `RunCommand`；本会话 CLI 的工具表是 `Bash`、`Read`、`Write`、`Edit`、`Grep`、`Glob` 等。**真实安装后要先确认 CLI 的 `tool_name` 映射，再写 matcher；不要直接照抄 `RunCommand`。**

### Hook trust

二进制里有：

```text
--dangerously-bypass-hook-trust
Run enabled hooks without requiring persisted hook trust for this invocation.
```

说明 hooks 有独立的 persisted trust；本次任务也明确禁止使用 `--dangerously-bypass-hook-trust`。最小适配不应依赖 hooks。

---

## 5. 斜杠命令与“向用户提选择题”

**结论：有内建 `AskUserQuestion`；斜杠命令在 2.0 有内建面板，但“自定义命令”在 2.0 文档中没有稳定路径，1.0 文档写的是 `.traecli/commands/*.md`，不要把它当作 Sopify 的入口。**

### 自定义斜杠命令

- TRAE CLI 2.0 官方文档只列内建命令，包括 `/skills`、`/hooks`、`/agents`、`/plugins`、`/mcp` 等，**没有写自定义命令目录**（[斜杠命令 2.0](https://docs.trae.cn/cli_slash-command)）。
- TRAE CLI 1.0 文档写的是：在项目根创建 `.traecli/commands/`，放 Markdown 文件，`/<command-name>` 调用；frontmatter 支持 `description`、`argument-hint`、`tools`、`model`（[TRAE CLI 斜杠命令 1.0](https://www.volcengine.com/docs/86677/2227864)）。
- IDE 文档写的是 `.trae/commands`，项目命令最多 3 层目录（[更新日志](https://docs.trae.cn/ide_changelog)）。
- 本机 `~/.traecli` 不存在，Sopify 仓库也没有 `.trae/commands`；二进制里只有 `Prefix with /name to invoke an enabled skill or custom command` 和 `slash-commands.json`（Lark 相关），没有 `.trae/commands` 字面量。

**适配含义**：Sopify 不要依赖自定义斜杠命令；用 skill 的 `description` 触发，或用 `/skills` 选择。

### 提问工具

- 本会话工具表里有 `AskUserQuestion`，可直接向用户提选择题。
- 二进制里有 ACP 兼容描述：“Disable the ACP AskUserQuestion/request_user_input compatibility tool”。
- Hook 的 `Notification` 事件有 `notification_type = "ask_user_question"`（官方 Hook 文档）。
- 结论：**Sopify 的 analyze 阶段可以放心用 `AskUserQuestion` 做选择题**，不需要自己造问答协议。

---

## 6. 结论：Sopify 的 Trae 适配最小方案

### 推荐落点

| 层 | 推荐 | 理由 |
|---|---|---|
| 项目入口 | 仓库根 `AGENTS.md` | 官方明确承诺 cwd 及上级 AGENTS.md 自动加载；本仓库现在没有这个文件，新增成本最低 |
| 全局入口 | `~/.trae/skills/<skill>/SKILL.md` | 本会话实测 `~/.trae/skills` 是 User root；`~/.trae/AGENTS.md` 未被证实 |
| 项目 skill | `.trae/skills/<skill>/SKILL.md` | 文档承诺的项目 skill 目录；本仓库尚未创建，需真实安装验证 |
| 备选 skill root | `.agents/skills/` 或 `~/.agents/skills/` | 本会话实测 `~/.agents/skills` 被加载；文档说同名时 `.trae/skills` 优先 |
| Hooks | **v1 不碰** | 需要 hook trust、事件 schema 与工具名映射都还没在 CLI 2.0 上验证 |

### Skills 布局

Sopify 现有模板是：

```text
skills/zh/skills/sopify/
  analyze/SKILL.md
  design/SKILL.md
  develop/SKILL.md
  kb/SKILL.md
  templates/SKILL.md
  references/...
```

建议渲染成**一层**：

```text
.trae/skills/sopify-analyze/SKILL.md
.trae/skills/sopify-design/SKILL.md
.trae/skills/sopify-develop/SKILL.md
.trae/skills/sopify-kb/SKILL.md
```

或全局：

```text
~/.trae/skills/sopify-analyze/SKILL.md
...
```

原因：

1. 文档只承诺一层 `skills/<name>/SKILL.md`；
2. 两层嵌套在本机没有样本，不能假设会被注册；
3. 每个 stage 独立成 skill 才能让 `description` 精确触发；
4. 共享 `references/` 若放在 skill 目录外，可能无法通过相对路径读取；建议复制到每个 skill 目录内，或用 `@` 引用绝对路径（需验证）。

### 硬约束

- `description` ≤ 1024 字符（日志已见超限失败）。
- `name` 用小写字母、数字、连字符。
- 不要设置 `policy.allow_implicit_invocation: false`，否则 skill 会被加载但不进“可用 skills”列表。
- 不要用 `~/.trae/cli/rules/` 放 Sopify 规则：那是 exec-policy `.rules` 目录，日志明确写 `loaded 0 .rules files`，不是指令规则。
- 不要用 `~/.trae/cli/hooks/commit-attribution/` 当作适配入口：那是 git commit-attribution 模板。

### 真实安装后必须验证的点

1. **全局规则路径**：`~/.trae/AGENTS.md` 是否被 2.0 读取；`~/.trae/user_rules` 是否被 2.0 读取（文档有 IDE 版本，CLI 2.0 未写）。
2. **项目 trust 与规则**：`trust_level = trusted` 是否是 `.trae/rules` / `AGENTS.md` 的加载前提；用 trusted/untrusted 两组会话对照。
3. **项目 skill root**：新建 `.trae/skills/<name>/SKILL.md` 后，`/skills` 是否出现；是否需要重启 TUI。
4. **两层嵌套**：在临时目录构造 `skills/sopify/analyze/SKILL.md`，确认是否注册为独立 skill；未确认前保持扁平。
5. **自定义斜杠命令**：2.0 是否支持 `.trae/commands` 或 `.traecli/commands`；当前 2.0 文档没有承诺。
6. **Hooks 用户级路径**：`~/.trae/hooks.json` 还是 `~/.trae-cn/hooks.json`；项目 `.trae/hooks.json` 的 hook trust 提示流程。
7. **PreToolUse 工具名**：CLI 的 `tool_name` 是 `Bash` 还是 `RunCommand`；matcher 必须按实际值写。
8. ** skill 安装/更新后的可见性**：新增或修改 `SKILL.md` 后，catalog 是否热更新；本会话日志里能看到 skills watcher，但未做增删实验。

## 一句话给编排方

**Trae 适配按“项目 `AGENTS.md` + 一套扁平 `sopify-*` skills”落地；hooks 与全局规则文件都先不碰，等真实安装后用 `/skills`、`/hooks` 和一次最小增删实验确认。**

## 参考链接

- [TRAE CLI 记忆 / AGENTS.md](https://www.volcengine.com/docs/86677/2227867)
- [TRAE CLI 技能](https://www.volcengine.com/docs/86677/2272059)
- [TRAE IDE Skills](https://docs.trae.cn/ide/skills)
- [TRAE IDE Rules](https://docs.trae.ai/ide/rules)
- [TRAE CLI 2.0 斜杠命令](https://docs.trae.cn/cli_slash-command)
- [TRAE CLI 1.0 斜杠命令](https://www.volcengine.com/docs/86677/2227864)
- [Hook 配置详解](https://docs.trae.cn/ide_hook-configuration-reference)
- [TRAE CLI 2.0 配置文件参考](https://docs.trae.cn/cli_config-file)
