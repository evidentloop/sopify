# Sopify 发布流程

面向维护者，作为 hook、版本同步、stable assets、发布与正式 smoke 的唯一步骤来源。stable 必须来自已合入 `main` 的提交；commit、push、merge、发布等动作按当前授权执行。

## 1. 设置 hook 与准备说明

每个 clone 启用一次：

```bash
git config core.hooksPath .githooks
```

在 `CHANGELOG.md` 的 `[Unreleased]` 写简短的用户变化或维护命令说明，保留该标题。正常提交流程中，pre-commit 先执行 preflight，再由 release-sync 以 `YYYY-MM-DD.HHMMSS` build version 同步 README badge、CHANGELOG、四个 header/Rule 版本源及 golden，并将受管文件加入同一提交。commit-msg 只在存在这次同步记录时附加 Release-Sync / Release-Version / Release-Date。

`[Unreleased]` 为空时，release-sync 可按 staged files 生成分类摘要；它不代替维护者审核。共享 prompt 的有意变更应先按 [贡献指南](../../CONTRIBUTING_CN.md) 审查快照。

## 2. 执行 preflight，确认待发布版本

使用 Python 3.11+：

```bash
bash scripts/release-preflight.sh
bash scripts/check-version-consistency.sh
```

preflight 只检查：版本、golden、builtin catalog、全部 `tests/`、五个协议 smoke 和 payload smoke；不会自动刷新或暂存漂移的 golden。失败先处理原因。

正常 hook 已处理版本更新，不要再手工改四份版本源。确需显式同步时使用现有命令，再重新验证并提交：

```bash
bash scripts/release-sync.sh 2026-08-30.001152 2026-08-30  # 示例；替换为实际新版本和日期
```

版本段格式为 `## [TAG] - YYYY-MM-DD`。待合入后，确认发布提交、版本和 CI 结果，以下 `RELEASE_TAG` 取版本一致性检查的实际输出。

## 3. 渲染 stable assets

根目录 `install.sh` / `install.ps1` 保持 dev 默认值，不直接作为 stable asset 上传：

```bash
RELEASE_TAG="2026-08-30.001152"  # 替换为已确认的发布版本
RELEASE_ASSETS_DIR="$(mktemp -d)"
python3 scripts/render-release-installers.py --release-tag "$RELEASE_TAG" --output-dir "$RELEASE_ASSETS_DIR"
rg 'SOURCE_CHANNEL|SOURCE_REF' "$RELEASE_ASSETS_DIR/install.sh"
rg 'SourceChannel|SourceRef' "$RELEASE_ASSETS_DIR/install.ps1"
```

两份产物的 channel 必须为 `stable`，source ref 必须等于 `RELEASE_TAG`。

## 4. 发布 GitHub Release

创建以该 tag 指向已合入 `main` 提交的 GitHub Release，说明取自对应 CHANGELOG 段。上传刚渲染的 `install.sh`、`install.ps1`，公开发布并设置为 latest；记录 tag、代码 SHA 和 asset URL。不要上传工作区的 dev wrapper。

## 5. 正式远端 smoke

从公开 latest 下载，在临时 home 验证；示例使用 Codex，涉及其他宿主时再覆盖相应 target：

```bash
SMOKE_ROOT="$(mktemp -d)"
curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/install.sh -o "$SMOKE_ROOT/install.sh"
env HOME="$SMOKE_ROOT/home" bash "$SMOKE_ROOT/install.sh" --target codex:zh-CN --verbose
```

保留输出，核对 `source channel: stable`、`resolved source ref` 等于发布 tag，以及 `asset name: install.sh`。确认受管文件放置正确；安装 smoke 不代替真实宿主加载或行为验证。

本地 `scripts/check-install-payload-bundle-smoke.py` 是 preflight 的源码验证，不能代替这个正式远端 smoke。远端失败时检查公开状态、latest、asset 名称和 source ref，不能把本地通过写成 release 已完成。

## 6. 核对公开文档

公开 README 仍指向 latest stable，主命令不带 `--workspace`；开发用 `raw/main` 路径留在开发资料中。只有实际发布和远端 smoke 通过，才宣布发布完成。

```bash
python3 scripts/check-readme-links.py
bash scripts/check-version-consistency.sh
```

## 维护调试开关

仅在维护／调试中显式使用；跳过检查不等于通过发布验收。

| 变量 | 作用 |
|---|---|
| `SOPIFY_DISABLE_RELEASE_HOOK=1` | 关闭整个 release hook 链 |
| `SOPIFY_SKIP_RELEASE_PREFLIGHT=1` | 跳过 hook 内的 preflight |
| `SOPIFY_AUTO_DRAFT_CHANGELOG=0` | 关闭空 Unreleased 的自动草稿 |
| `SOPIFY_RELEASE_HOOK_DRY_RUN=1` | 只报告是否会触发发布同步 |
| `SOPIFY_FORCE_RELEASE_SYNC=1` | 忽略路径筛选，触发同步 |

误上传 dev asset 时，重新按第 3 步渲染并替换，随后重跑正式 smoke。署名政策只在 [贡献指南](../../CONTRIBUTING_CN.md) 维护。
