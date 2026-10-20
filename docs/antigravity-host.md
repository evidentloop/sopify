# Antigravity CLI 宿主接入

Antigravity 使用全局规则进入 Sopify，阶段 Skills 按需加载。支持档位为 `BASELINE_SUPPORTED`；本期依据 `agy 1.4.2` 的加载面探针选择安装路径，完整工作流行为仍待真实会话验证。

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

探针还观察到一层 `skills/<name>/SKILL.md` 可被发现、两层嵌套样本被忽略，因此使用 `sopify-*`。阶段内容来自同一套 Sopify 源文件，安装时改写名称、资源引用和脚本路径。普通问答与小修复直接处理，方案、继续和收口按共同协议进入；有 `ask_question` 时使用宿主工具，否则文本追问。

本适配不注册 Hooks 或 MCP，不改账号、模型、代理、信任或其他宿主设置。Antigravity IDE 不在本次 CLI 证据范围内。

## Doctor 与真实会话

```bash
python3 scripts/sopify_doctor.py --format json
```

- `host_prompt_present`：规则文件是否存在。
- `global_skill_tree_present`：五项阶段入口、共享资源和评分脚本是否存在。
- `payload_present`：payload/bundle 是否结构完整。
- `antigravity_cli_behavior`：静态返回 `skip (BLACK_BOX_NOT_VERIFIED)`。

文件检查不证明宿主执行了 Sopify。候选版本还需验证入口可见、普通问答、小修复、新方案评分、恢复与 finalize；按 [Host onboarding recipe](./host-onboarding.md) 记录候选版本及真实工具调用。Antigravity 是本轮主要 dogfood 宿主，加载面探针不能替代这组验收。
