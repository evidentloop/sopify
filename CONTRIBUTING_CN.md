# 贡献指南

非 trivial 工作先对齐范围与责任。一个 PR 聚焦一个可验证改动；用户可见变化同步中英文 README，维护者命令或用户行为变化写简短 CHANGELOG。

## 如何贡献

- `main` 是唯一长期分支。使用短生命周期 `<type>/<topic>` 主题分支，通常经 PR 合入；stable 使用已合入 `main` 的提交、tag 和 GitHub Release。只有并行维护多个版本、确需 backport 时才重评 release branch。
- 修复当前错误链路，不顺手扩路由、状态或功能；延后问题留在对应方案或 backlog。
- 保留已有改动，准备提交时显式纳入新增源码；`git commit -am` 不会包含新文件。
- 协议、checkpoint、bridge、installer 或 status/doctor 行为变化需对应回归证据。纯文档修改做相关链接和内容检查，不要求无关代码测试。

## Prompt 层与 Skill Authoring

`skills/{zh,en}` 是单一来源：`header.md.template` 加 `skills/sopify/`。双语保持一致，遵循对应 Skill 入口；安装产物由 adapter 生成，不手工维护第二棵源树。

在仓库根目录预览一份 header：

```bash
python3 scripts/render-host-skills.py --host codex --lang zh --output /tmp/sopify-preview/AGENTS.md
```

不带 `--output` 时输出到 stdout；`--verify-all` 可比较全部 header 变体。该命令只预览 header，Skill 正文直接查看 `skills/{zh,en}/skills/sopify/`。旧 `Codex/`、`Claude/` 缓存目录仍被 gitignore，不参与发布。

- route 绑定使用 `supports_routes`，`skill.yaml` 经 `sopify_contracts/skill_schema.py` 校验。
- `tools / disallowed_tools / allowed_paths / requires_network` 目前是声明字段。
- catalog 元数据变化时，用 `python3 scripts/generate-builtin-catalog.py` 再生成 `skills/catalog/builtin_catalog.generated.json`，不手改产物。
- 有意改变输出后先审查，再显式运行 `python3 scripts/regenerate-golden-snapshots.py`；preflight 只检查，不自动接受漂移。

## Payload Bundle 与宿主接入

能力探针和 adapter 变更遵循 [宿主接入 recipe](./docs/host-onboarding.md)。[Protocol](./.sopify/blueprint/protocol.md) 定义入口与写入归属，协议状态只能经 `sopify_writer` 写入；workspace marker 定位 bundle，任务进度属于方案文件。

- root `install.sh` / `install.ps1` 保持 thin wrapper，只下载同 ref 源码并调用 `scripts/install_sopify.py`。
- 分发逻辑走 host registry；保留 legacy bundle 读取和独立 helper/Hook fallback。
- 安装、更新、可选组件和卸载统一查 [Getting Started](./docs/getting-started.md)。开发用 `raw/main` 入口不作为 README 的公开主入口。

### MCP 试点

repo-local `scripts/sopify_mcp_server.py` 使用已有 Python 3.11+ 与 `mcp[cli]>=1.27,<2` 环境，不自动安装依赖或改变 payload。

```bash
# 默认 dry-run，检查注册。
python3 scripts/sopify_mcp_register.py --python /path/to/python3
# 明确授权后，通过宿主官方 CLI 应用。
python3 scripts/sopify_mcp_register.py --python /path/to/python3 --apply
```

注册委托 `codex mcp get/add`，不直接改 TOML；同配置为 no-op，冲突配置不覆盖。Codex 是首个验证对象；其他宿主、依赖打包和 doctor 集成需各自的证据。

## 校验命令

使用 Python 3.11+，按变更选相关检查。共享工作区可设置 `PYTHONDONTWRITEBYTECODE=1` 和 `PYTEST_ADDOPTS="-p no:cacheprovider"`，避免缓存噪声。

```bash
python3 -m pytest tests -q
python3 scripts/check-readme-links.py
```

协议或 payload 修改另跑对应 smoke：

```bash
python3 scripts/sopify_protocol_check.py check --scenario new-plan --fixture tests/fixtures/minimal_plan
python3 scripts/check-install-payload-bundle-smoke.py --target codex:zh-CN
```

## Release Hook 与 CHANGELOG

[发布流程](./docs/dev/release-process.md) 是 hook 设置、版本/CHANGELOG 同步、preflight、stable assets、发布和正式 smoke 的唯一步骤来源；对外 Git 动作仍按当前任务授权执行。

## 许可说明

AI 协作声明见 [CONTRIBUTORS.md](./CONTRIBUTORS.md)。仓库不自动添加标准 AI `Co-authored-by` trailer，可按需手动署名。

贡献遵循目标文件许可：代码与配置为 Apache 2.0，文档为 CC BY 4.0。
