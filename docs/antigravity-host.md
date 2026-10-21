# Antigravity CLI 宿主接入

Antigravity 使用全局规则进入 Sopify，阶段 Skills 按需加载。支持档位为 `BASELINE_SUPPORTED`；路径依据 `agy 1.4.2` 的加载面探针选择。已有本机可见性、普通问答和一次 plan-only 局部行为证据，完整工作流仍未通过验收。

## 安装面

在当前源码中安装：

```bash
python3 scripts/install_sopify.py --target antigravity:zh-CN
```

也支持 `antigravity:en-US`；省略语言默认 English，与 Cursor 一致。安装或更新后启动新会话，再检查规则和 Skill 是否可见。

- 规则：`~/.gemini/config/AGENTS.md` 中的 Sopify managed block，保留块外用户内容。
- Skills：`~/.gemini/config/skills/sopify-analyze/`、`sopify-design/`、`sopify-develop/`、`sopify-kb/`、`sopify-templates/`。
- 共享资源：`~/.gemini/config/skills/sopify/references/`，只安装一份，由阶段 Skill 相对引用。
- Payload：`~/.gemini/config/sopify/`，复用现有版本化 bundle 和 bootstrap helper。

普通安装不需要 `--workspace`。重装会修复自有 Skill 资源并清除自有阶段目录中的过期文件；其他 Skills 与块外规则保持原样。切换语言沿用相同安装命令。`--with-evidentloop` 当前不支持。

## 入口与边界

探针观察到四个全局文件依次可见：`~/.gemini/AGENTS.md`、`~/.gemini/GEMINI.md`、`~/.gemini/config/AGENTS.md`、`~/.gemini/config/GEMINI.md`，随后是项目规则。这个顺序证明加载可见性，不证明冲突规则的优先级。本适配只管理其中一个文件。

探针还观察到一层 `skills/<name>/SKILL.md` 可被发现、两层嵌套样本被忽略，因此使用 `sopify-*`。阶段内容来自同一套 Sopify 源文件，安装时改写名称、资源引用和脚本路径。共享规则要求普通问答与未托管的小修复直接处理，方案、继续和收口按共同协议进入；宿主提供 `ask_question` 时使用该工具，否则文本追问。这些规则要求不等于各场景均已实测通过。

本适配不注册 Hooks 或 MCP，不改账号、模型、代理、信任或其他宿主设置。Antigravity IDE 不在本次 CLI 证据范围内。

## Doctor 与真实会话

```bash
python3 scripts/sopify_doctor.py --format json
```

- `host_prompt_present`：规则文件是否存在。
- `global_skill_tree_present`：五项阶段入口、共享资源和评分脚本是否存在。
- `payload_present`：payload/bundle 是否结构完整。
- `workspace_bundle_manifest`、`workspace_handoff_first`：当前项目是否已绑定可解析的 bundle 及所需契约；全局安装通过不代表项目绑定完成。
- `antigravity_cli_behavior`：静态返回 `skip (BLACK_BOX_NOT_VERIFIED)`。

候选 `a9a0f95` 的本机新会话实际接收了完整 header 和五项 Skill；一次普通代码问答未创建 `.sopify/`。一次带 `--dangerously-skip-permissions` 的 plan-only 会话读取规则、执行评分脚本，并通过 `sopify_writer` 写入 state；这是该次运行的权限条件，不作为标准 CI 配置推荐。

该项目没有完成 bundle 绑定，Doctor 的两个 workspace 项报 `fail (MISSING_BUNDLE)`，版本状态为 `broken`。只生成方案和 state 不代表项目初始化成功；现行规则也没有保证首次 `~go` 自动调用绑定入口。小修复、缺信息追问、恢复、finalize 和重复运行稳定性仍待验证；行为项继续保留 `BLACK_BOX_NOT_VERIFIED`，不因本次局部样本升级为通过。后续按 [Host onboarding recipe](./host-onboarding.md) 分场景记录真实工具调用，CLI 证据不外推到 IDE。
