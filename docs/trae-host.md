# Trae CLI 宿主接入

Trae 使用顶层 `sopify` Skill 路由到阶段 Skills，支持档位为 `BASELINE_SUPPORTED`。路径依据 `traecli 0.209.1` 的加载面记录选择；当前适配**待真实会话验证**，安装完成不等于模型已经选择或遵循入口。

## 安装面

在当前源码中安装：

```bash
python3 scripts/install_sopify.py --target trae:zh-CN
```

也支持 `trae:en-US`；省略语言默认 English，与 Cursor 一致。安装后开启新会话并检查 Skill 列表；当前没有证据保证更新在旧会话立即生效。

- 入口：`~/.trae/skills/sopify/SKILL.md`，文件开头是 Skill 元数据，managed block 中直接使用共同的 Sopify header。
- 阶段：`~/.trae/skills/sopify-analyze/`、`sopify-design/`、`sopify-develop/`、`sopify-kb/`、`sopify-templates/`。
- 共享资源：`~/.trae/skills/sopify/references/`，只安装一份，由阶段 Skill 相对引用。
- Payload：`~/.trae/sopify/`，复用现有版本化 bundle 和 bootstrap helper。

普通安装不需要 `--workspace`。重装修复自有阶段资源，保留其他 Skills 和入口 managed block 外的用户正文；入口身份元数据由安装器维护。切换语言使用同一命令，入口 description 保持简短的双语触发提示，正文随语言切换。`--with-evidentloop` 当前不支持。

## 入口与边界

已有记录证明 Trae 扫描用户 Skill 目录，未证明全局 `AGENTS.md` 被加载，因此本适配不写 `~/.trae/AGENTS.md`。两层嵌套能否注册也未证实，阶段与 Antigravity 共用扁平布局。所有安装后的 Skill description 均小于 1024 字符。

方案、开发、继续和收口请求通过模型按需选择顶层 `sopify`；如果没有选中，可在宿主 Skill 列表中显式选择。不要把自动选择描述成强制入口。普通问答与未托管的小修复直接处理；进入 Sopify 后沿用共同的意图分类、四步协议和 writer 写回边界。有 `AskUserQuestion` 时使用宿主工具，否则文本追问。

本期不写 Hooks、`traecli.toml`、账号、模型、代理或信任设置，不注册 MCP。Trae IDE 与 CLI 的加载行为不互相外推。

## Doctor 与真实会话

```bash
python3 scripts/sopify_doctor.py --format json
```

- `host_prompt_present`：顶层入口 Skill 是否存在。
- `global_skill_tree_present`：五项阶段入口、共享资源和评分脚本是否存在。
- `payload_present`：payload/bundle 是否结构完整。
- `trae_cli_behavior`：静态返回 `skip (BLACK_BOX_NOT_VERIFIED)`。

真实会话尚未验证入口选择、脚本执行、恢复、finalize 和跨阶段资源读取；这些项目保持未验证，不因安装检查通过而改为成功。Trae 按当前范围发布，后续发现问题可继续提交修复；取证方式见 [Host onboarding recipe](./host-onboarding.md)。
