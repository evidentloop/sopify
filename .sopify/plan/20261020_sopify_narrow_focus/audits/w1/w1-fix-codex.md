# W1 返工报告

**六项返工已完成。** 相对本轮开始的未提交 W1 改动，生产代码净减 **97 行**；全量 **386 passed, 97 subtests passed**，preflight 和 `git diff --check` 均退出 0。代码仍未暂存、未提交、未推送，交大脑审 diff 与验收官复核。

## 本轮修改与行数

基线是 `feat/sopify-narrow-focus@43ee5f5a605d6a753c3ec52a147574097befc30b` 上已有的 W1 未提交内容，**不是相对 HEAD 的累计 diff**。只修改下面 7 个仓库文件。

| 分类／文件 | 新增 | 删除 | 净变化 | 本轮变化 |
|---|---:|---:|---:|---|
| 生产：`installer/hosts/base.py` | 14 | 140 | **−126** | 删除历史哈希、当前模板逐字匹配与独立 home block 实现；home/Copilot 共用 upsert；树比较改为公开名。 |
| 生产：`installer/bootstrap_workspace.py` | 59 | 29 | **+30** | 集中唯一 block upsert、严格标记解析与旧 header 锚点识别；删除路径复用同一解析器。 |
| 生产：`installer/cursor_plugin.py` | 2 | 2 | 0 | 引用公开的 `skill_tree_matches`，不再跨模块引用私有函数。 |
| 生产：`scripts/regenerate-golden-snapshots.py` | 2 | 3 | **−1** | 注释明确手动评审后的生成、release-sync 生成、preflight 只检查的职责。 |
| 测试代码：`tests/test_home_host_integrity.py` | 107 | 102 | **+5** | 合并重复组合，81 例收敛为 44 例；增加 Copilot 和独立 helper 一致性检查。 |
| 测试夹具：`tests/fixtures/legacy-home-headers/en.md` | 102 | 20 | **+82** | 原位替换为真实 2026-06-10 英文 header；未增加夹具文件。 |
| 文档：`docs/getting-started.md` | 7 | 18 | **−11** | 卸载正文压为 7 行，保留项目资产、删除入口受管块和宿主自有目录。 |
| **合计** | **293** | **314** | **−21** | 生产代码净减 97；测试含夹具净增 87；文档净减 11。 |

测试代码净增 5 行，是在删掉重复组合后补了独立部署路径和 Copilot 的保护检查；测试夹具净增 82 行来自真实旧版正文比新版长，未为每个版本新增一份文件。计算按 UTF-8 文本行、包含注释与空行，明细见 [line-metrics.json](./w1-fix-evidence/line-metrics.json)。

## 六项返工的证据

### 1. 旧头文件按锚点迁移

已删除 `_LEGACY_HEADER_HASHES`、哈希归一逻辑和「当前模板逐字匹配」路径，无保留例外。现在只识别唯一的 bootstrap 首行、方案包路径末行，以及该区间内恰好一个完整 `SOPIFY_VERSION` 注释；版本号和正文变化不影响迁移。区间整体视为旧 Sopify 生成区，区间外字节保留。

使用现有两个夹具，不新增文件：

| 夹具 | 真实来源 | 与该 tag 源文件一致 |
|---|---|---|
| `zh.md` | `2026-08-30.001152:skills/zh/header.md.template`，commit `8770413548b8194a2ee79c5e342717d3050456a2` | 字节完全一致 |
| `en.md` | `2026-06-10.191940:skills/en/header.md.template`，commit `fb1983396a48b9e4e5c946080a6df636fb1d778f` | 字节完全一致 |

`test_legacy_migration_is_version_independent` 的 4 个组合覆盖两个版本、中英文、三个 home 宿主、LF/CRLF、整份旧文件及带用户前后内容的文件；候选版本模板还被改成不同正文，证明迁移不依赖新模板。重复安装返回 skipped。

`test_ambiguous_legacy_header_is_rejected_without_writes` 的 7 例覆盖缺首/尾锚点、重复首锚点、重复整段、缺版本注释、损坏版本注释、重复版本注释；都明确拒绝且已有安装快照不变。旧正文仅因内容不同而拒绝的测试已删除，因为它与本轮授权的生成区认定规则相冲突。

### 2. 一个 upsert 实现，统一标记语义

唯一写入实现为 `installer.bootstrap_workspace.upsert_managed_instruction_block`。调用关系：

- Claude/Codex/Qoder 和 Copilot 安装：`base._write_managed_block` → 公共 upsert；base 的薄包装只将 `ValueError` 转为已有的 `InstallError`，不再解析标记或生成另一套 block。
- bootstrap 同步 Copilot 指令：直接调用同一公共 upsert。
- `_remove_managed_instruction_block`：复用同一个 `_managed_instruction_block_span`；不再用另一条宽松正则或忽略文件归一逻辑删除内容。

放在已有的 bootstrap helper 中，是为了让安装后的独立脚本直接携带同一份实现，无新增模块分发、依赖或 fallback 副本；原有独立部署 fallback 保留。

**Copilot 行为边界：** 正常追加、合法块更新和重复安装跳过的流程保持；缺标记、顺序错误、重复块或嵌套标记，从原来的静默追加/替换第一块/跳过，改为明确拒绝且不写入。按统一的字节保留要求，更新时也不再顺带归一块外 CRLF、空行或文件末尾换行。

证据：

- `test_user_only_header_is_preserved_and_reinstall_is_idempotent`：4 宿主通过。
- `test_valid_managed_block_repairs_content_and_preserves_outside_bytes`：4 宿主通过，含相同版本下内容损坏。
- `test_malformed_markers_fail_without_writes`：home/Copilot 两条入口、5 种异常，共 10 例通过；重复块第一块即使已是正确内容，也不能提前 skipped。
- `test_standalone_helper_uses_strict_blocks_and_preserves_outside_bytes`：把 helper 复制到临时目录，通过 `python -I` 脱离仓库运行，验证更新、删除、异常拒绝及外部字节保留。
- 既有 `CopilotInstructionSyncTests` 和独立 bootstrap 回归仍通过。

`.gitignore` 使用另一组 `# BEGIN sopify-managed` 标记，属于不同格式，本轮未改。

### 3. 不跨模块引用私有函数

`_skill_tree_matches` 改名为公开的 `skill_tree_matches`；home 和 Cursor 均正常引用。Cursor 顶层 CLI Skill 的覆盖参数及完整树比较行为保留，没有增加第二份比较实现。

### 4. 卸载说明压缩

正文 7 行，列出 Copilot、Claude、Codex、Qoder 的文件位置及同一组 block 标记，明确保留 `.sopify/` 和块外内容，可删除宿主内的 `skills/sopify/`、`sopify/`。旧安装只提示先重装一次完成迁移，不再要求用户手工判定、包裹或修写标记。

### 5. 清理过时注释

`scripts/regenerate-golden-snapshots.py` 顶部已删除 preflight auto-fix 描述：有意变更经评审后显式生成，release-sync 在版本更新后生成，preflight 只验证。没有改变脚本行为或刷新仓库 golden。

### 6. 合并冗余测试

原 81 例收敛为 **44 例**，减少 37 例：

- 将「当前正文旧版本」「固定旧版」「混合用户内容」「模板升级」合并为 4 个真实版本迁移组合。
- 删除依赖正文逐字相同的旧拒绝规则。
- 纯解析失败只选一个 home 宿主；home/Copilot 两条独立入口保留标记异常验证。
- 完整树修复只跑共同 home 实现与 Cursor 实现两组，不为 Claude/Codex/Qoder 的相同实现重复跑三遍。
- 将同版本 header 内容修复合入合法块更新测试；保留四个宿主的语言切换。

最终覆盖数：用户原文 4、旧版迁移 4、不可唯一识别的旧规则 7、合法块修复 4、异常标记 10、完整树修复 10、语言切换 4、独立 helper 1，总计 44。迁移矩阵四类输入均保留，PR #75 的四份测试没有删除。

## 验证记录

沿用已安装的 Python **3.11.15 / pytest 9.1.1**，仅验证子进程将其加入 PATH；设置 `PYTHONDONTWRITEBYTECODE=1` 和 `PYTEST_ADDOPTS=-p no:cacheprovider`，不改用户配置。

| 命令／阶段 | 退出码 | 关键结果 |
|---|---:|---|
| 修前：`python3 -m pytest tests/test_home_host_integrity.py -q --tb=short` | 1 | `11 failed, 33 passed`：包括旧六月版本被拒、Copilot 接受异常 markers、块外字节被改变；独立 helper 新入口尚不存在。 |
| 修后定向：上述文件加 `tests/test_installer.py tests/test_cursor_cli_install_surface.py` | 0 | `98 passed, 13 subtests passed in 10.85s` |
| `python3 -m pytest tests -q` | 0 | **386 passed, 97 subtests passed in 39.52s** |
| `bash scripts/release-preflight.sh` | 0 | golden 24 项通过；全量再次 **386 passed, 97 subtests passed in 33.04s**；catalog、五个协议 smoke、payload smoke 均通过，最后 `All checks passed.` |
| `git diff --check` | 0 | 无输出 |

日志：[修前](./w1-fix-evidence/before-tests.txt)、[定向修后](./w1-fix-evidence/targeted-after.txt)、[全量](./w1-fix-evidence/full-suite.txt)、[preflight](./w1-fix-evidence/preflight.txt)。

## 边界与交接

- 自查：未增加历史版本表、配置、用户开关或手工升级流程；公共 helper 沿用现有独立部署边界，managed block 解析与 upsert 各只有一份。生产代码和文档均减少，测试增量已单独披露。
- 本轮开始时大脑已修改方案中的验收标准及标语内容；这些既有变更原样保留。全部 **273 个 `.sopify/` 文件**相对本轮开始的内容指纹未变，index 未变、暂存区仍为空、HEAD 未变；其他 W1 未提交改动保留。证据见 [final-inventory.json](./w1-fix-evidence/final-inventory.json)。
- 未修改真实用户 home，未 commit/push，未操作 PR/issue。没有待裁决的实现分叉；下一步为大脑审 diff 和独立验收，本报告不代写验收回执。
