# W1 执行报告：T1 全量测试门与 T2 安装、writer 修复

结论：**受限写入任务已完成，可以交大脑审 diff 和验收官复核。** 最终全量为 **423 passed, 97 subtests passed**，preflight 也退出 0；未 commit、push 或操作 PR。T1 的「真实 PR CI 为绿」尚未执行，不能把本地通过写成 T1 全部完成。

## 1. 基线、范围与保留边界

- 分支：`feat/sopify-narrow-focus`。
- HEAD：`43ee5f5a605d6a753c3ec52a147574097befc30b`，开始和结束一致；开始工作区干净。
- 仅修改下表 16 个仓库文件，全部未暂存；另写本报告及同目录 `w1-evidence/` 取证文件。
- `.sopify/plan`、`.sopify/state`、`.sopify/history` 共 **259 个文件**，结束时路径集合及 SHA-256 与开始快照相同。
- 仓库 index 自开始至结束保持同一 SHA-256：`ff577ab16442c8f5c4c012de477b3a08fa4eb9ec25920dda76875d0f077739df`；`git diff --cached --stat` 为空。
- 安装实验都传入临时 `home_root`，未安装到真实用户 home；Git hook 回归只在测试自建的临时仓库中执行。
- `sopify_contracts`、writer 公开导出、`release-sync.sh`、legacy bundle 测试和独立 helper / Hook fallback 均未修改。
- PR #75 只执行了获准 fetch 和 `git show` 取文件；来源为 `fb8a6965abc0dda1246ee0e3ed123b66f29635d5`，本地 `pr75-tests` 分支已删除，未动 PR 本身。

文件和内容指纹见 [final-inventory.json](./w1-evidence/final-inventory.json)。

## 2. 实际文件清单

| 文件 | 改动 |
|---|---|
| `.github/workflows/ci.yml` | pytest 从七文件白名单改为收集整个 `tests/`，保留 catalog drift、五个 protocol smoke 和 payload smoke。 |
| `scripts/release-preflight.sh` | 跑全部测试；golden 失败直接退出，移除自动 regenerate 和 `git add`，保留其余检查。 |
| `tests/test_release_hooks.py` | 增加真实 golden 漂移/index 保留、白名单外失败用例可被收集的隔离回归；加强显式 release-sync 仍刷新 golden 的检查。 |
| `installer/hosts/base.py` | home 头文件改为保留用户字节的 managed block；识别已知旧产物、拒绝不明归属或异常 markers；对完整 Sopify 自有 Skill 树做内容比较。 |
| `installer/cursor_plugin.py` | 复用完整树比较，保留 Cursor 顶层 CLI Skill 的模板覆盖、独立 Plugin 布局和既有 manifest/Rule/README 检查。 |
| `installer/distribution.py` | 空运行时自检输出在双语用户摘要中明确为「未执行」；补齐 Cursor 产品显示名。 |
| `sopify_writer/io.py` | `read_json` 拒绝数组、null、标量等非对象 JSON，抛已有的 `InvariantViolationError`，消息含文件路径。 |
| `docs/getting-started.md` | 卸载保留 `.sopify/` 方案与历史；共享指令文件只移除受管块，保留用户内容及其他 Skill/settings。 |
| `tests/test_cursor_cli_install_surface.py` | 吸收 PR #75 的 6 项 Cursor 安装/Doctor/语言切换回归，移除 AUDIT-1 xfail。 |
| `tests/test_cursor_hook_branches.py` | 原样吸收 PR #75 的 Hook 分支回归。 |
| `tests/test_install_user_summary.py` | 吸收 PR 测试并移除 AUDIT-2/3 xfail，补空白输出、双语「未执行」与双语产品名检查。 |
| `tests/test_sopify_writer_state_guards.py` | 吸收 PR 测试并移除 AUDIT-4 xfail，补全部非对象类型及缺失/合法对象/语法损坏 JSON 的区别。 |
| `tests/test_home_host_integrity.py` | 新增 81 个参数化案例，覆盖迁移矩阵、旧版迁移不依赖新模板、CRLF、用户字节保留、完整树修复及语言切换。 |
| `tests/fixtures/legacy-home-headers/zh.md` | 固定 `2026-08-30.001152` 中文整份 header 为历史迁移夹具，不能随新模板自动刷新。 |
| `tests/fixtures/legacy-home-headers/en.md` | 同上，英文历史夹具。 |
| `tests/test_sopify_mcp_server.py` | 两个非对象输入的期望错误码改为 `InvariantViolationError`；对象缺少有效 plan_id 仍为 `ValueError`，状态不变断言保留。 |

## 3. T1 完成定义与证据

### 3.1 修前、修后

新写测试先在原 preflight 上运行，得到：

| 测试 | 修前实际 | 修后 |
|---|---|---|
| `ReleaseHookTests::test_preflight_collects_tests_outside_former_whitelist` | 临时 `tests/future/test_new_regression.py` 中明确失败的测试未被收集，preflight 仍返回 0，回归测试失败。 | preflight 收集新文件、返回非 0，输出包含 `full-suite sentinel`，回归通过。 |
| `ReleaseHookTests::test_preflight_rejects_golden_drift_without_changing_index` | 写入真实 golden 漂移后，preflight 自动生成并暂存新 golden；index 字节比较失败。 | preflight 非 0，输出 `Golden snapshot mismatch`；golden 文件及 index 字节均不变。 |

命令：

```text
python3 -m pytest -p no:cacheprovider -q tests/test_release_hooks.py -k preflight
```

修前退出 **1**，`2 failed, 9 deselected`，见 [t1-before.txt](./w1-evidence/t1-before.txt)。

修复后运行整个 release-hook 文件，退出 **0**，`11 passed in 10.21s`，见 [t1-after.txt](./w1-evidence/t1-after.txt)。随后加强了 release-sync golden 断言，最终全量和实际 preflight 再次覆盖并通过该测试。

隔离 preflight 夹具运行真实 golden 测试和生成脚本；无关 smoke 使用占位脚本，避免把测试变成全仓库递归 preflight。最终仓库 preflight 另行运行真实 smoke，结果见下。

### 3.2 逐条 DoD

| 完成定义 | 证据与裁定 |
|---|---|
| 本地 `python3 -m pytest tests -q` 退出 0 | 已完成；**423 passed, 97 subtests passed in 37.18s**，退出 0。 |
| PR 上 CI 全量实跑并为绿 | **未执行。** CI 配置已改为 `python3 -m pytest tests/ -q`，但本任务禁止 push/PR 操作；无 CI 链接，须大脑获准推送后补验。 |
| golden 漂移时非 0、index 不变 | 已完成；上述隔离夹具检查真实 `.git/index` 原始字节及 golden 原始字节。 |
| 保留 catalog/protocol/payload 检查 | 已完成；实际 `bash scripts/release-preflight.sh` 退出 0，catalog 无漂移，五个协议场景均 `PASS`，payload 报告 `passed: true`。 |
| release-sync 继续负责显式版本更新后的 golden | 脚本未改；`test_release_sync_auto_drafts_unreleased_before_version_bump` 现在复制真实 installer 到夹具，断言 `Golden snapshots regenerated`，并核对新版本 header 对应 SHA-256。 |

实际 preflight 输出还包含：

```text
[release-preflight] Check golden snapshots
24 passed in 0.10s
[release-preflight] Check builtin catalog drift
[release-preflight] Run full test suite
423 passed, 97 subtests passed in 41.29s
...
[release-preflight] All checks passed.
```

实际 preflight 运行前后仓库 index SHA-256 相同，golden 未改；见 [preflight.txt](./w1-evidence/preflight.txt)。

## 4. T2 缺陷修复与修前证据

四个 PR 测试文件全部取入，移除四个 xfail 后，先执行以下定向回归，再改生产代码：

```text
python3 -m pytest -p no:cacheprovider -q --tb=short \
  tests/test_cursor_cli_install_surface.py \
  tests/test_cursor_hook_branches.py \
  tests/test_install_user_summary.py \
  tests/test_sopify_writer_state_guards.py \
  tests/test_home_host_integrity.py
```

修前退出 **1**，pytest 原始汇总为 **69 failed, 25 passed, 7 subtests passed**，见 [t2-before.txt](./w1-evidence/t2-before.txt)。其中 failed 数包含失败子测试，不能简单当作 69 个独立函数。

| 缺陷 | 关键回归名 | 修前实际 | 修后 |
|---|---|---|---|
| AUDIT-1：Cursor 已存在但损坏的阶段 Skill 被跳过 | `test_reinstall_restores_phase_skill_that_differs_from_source` | 内容 `truncated`，重装仍 `skipped`。 | `updated` 并恢复源字节。 |
| 共同安装器漏检缺文件、references/scripts 和多余旧文件 | `test_reinstall_repairs_the_complete_owned_tree` | 除 Cursor 已有路径检查能捕获的缺文件场景外，缺失/损坏/多余自有文件仍多次被判 `skipped`。 | 四宿主 20 个案例均恢复完整源树，并保留旁边的个人 Skill。 |
| 同版本语言切换被跳过 | `test_language_switch_and_ignored_cache_preserve_other_skills` | Claude/Codex/Qoder 从 CN 切 EN 仍 `skipped`。 | 四宿主均 `updated`，英文阶段内容正确，下一次同语言安装 `skipped`。 |
| 头文件内容坏了但版本不变 | `test_header_corruption_with_matching_version_is_repaired` | 三个 home 宿主仍 `skipped`。 | managed block 内内容复原。 |
| AUDIT-2：空 smoke 展示英文占位 | `test_success_summary_does_not_print_empty_smoke_placeholder`；`test_empty_smoke_is_explicitly_not_run_in_both_languages` | 用户摘要含 `(no smoke output)`，空白输出也不表达「未执行」。 | 中文为「未执行运行时自检。」，英文为 `Runtime smoke check was not run.`；真实 passed 文案仍通过。 |
| AUDIT-3：Cursor 显示名缺失 | `test_cursor_summary_uses_the_product_display_name` | 中文下一步含 `打开 cursor`。 | 中文/英文分别含 `打开 Cursor` / `Open Cursor`。 |
| AUDIT-4：非对象 active plan | `test_finalize_rejects_non_object_active_plan`；`test_active_plan_rejects_all_non_object_json_without_writes` | finalize 抛裸 `AttributeError`；读取数组/null/布尔/数字/字符串未被边界拒绝。 | 都抛 `InvariantViolationError`；原状态字节不变，未归档。 |
| 共享 home header 覆盖用户内容 | 下节迁移矩阵全部案例 | 用户前后内容被覆盖、合法块变成整份 header、异常 markers 未拒绝。 | 按矩阵保留、迁移或明确拒绝，不静默损失用户内容。 |

首轮修复后同命令退出 **0**，`87 passed, 14 subtests passed`，见 [t2-after.txt](./w1-evidence/t2-after.txt)。

后续边界检查又先记录三组失败再修复：

- 新版模板改变后，已发布旧 header 不能迁移；旧规则之后用户尾部没有换行时被多加换行：`-k 'after_source_template_changes or outside_bytes'`，退出 1，**9 failed, 3 passed**，见 [migration-edge-before.txt](./w1-evidence/migration-edge-before.txt)。
- 旧 header 为 CRLF 时，被当成无旧规则而追加一套：`-k crlf`，退出 1，**6 failed**，见 [migration-crlf-before.txt](./w1-evidence/migration-crlf-before.txt)。

- 旧规则仍在但版本注释丢失或损坏：`-k unrecognized_legacy_mix`，退出 1，**6 failed, 3 passed**；补充旧规则痕迹判定后明确拒绝且零写入，见 [migration-version-before.txt](./w1-evidence/migration-version-before.txt)。

以上新增案例均已纳入最终 **423 passed** 的全量结果，没有 xfail 或临时跳过。

## 5. 迁移矩阵验收

以下测试均在临时 home，三种宿主为 Claude、Codex、Qoder；最终全部通过。

| 输入类型 | 对应测试及覆盖数 | 最终行为 |
|---|---|---|
| 只有用户内容，没有 Sopify 块 | `test_user_only_header_is_preserved_and_reinstall_is_idempotent`，3 例 | 追加一块；用户原始 CRLF/空行保留；重装 `skipped`，不增加块。 |
| 能确认是旧版整份产物 | `test_known_legacy_whole_header_migrates_to_one_block`，6 例；`test_shipped_legacy_header_migrates_after_source_template_changes`，12 例 | CN/EN、不同版本戳及固定已发布产物可迁移；新版模板已改变也能迁移；LF/CRLF 均覆盖；只剩一套规则。 |
| 旧产物混有用户内容 | `test_known_legacy_header_with_user_content_preserves_outside_bytes`，6 例；`test_unrecognized_legacy_mix_is_rejected_without_changing_install`，9 例 | 能确认的旧正文被替换，外部前后字节不变，包括末尾无换行；不能确认时报 `migration incomplete`，整套已有安装快照不变。 |
| 合法块，或不完整/重复 markers | `test_valid_managed_block_updates_only_its_contents`，3 例；`test_malformed_markers_fail_without_writes`，15 例 | 合法块只换内部正文；缺 BEGIN、缺 END、顺序反了、重复块、嵌套 BEGIN 均拒绝且不写文件。 |

另有完整树修复 20 例、语言切换/忽略缓存/其他 Skill 保留 4 例、同版本 header 修复 3 例；合计 `test_home_host_integrity.py` 为 **81 例**。

### 识别边界与取舍

1. **不靠版本号猜整份文件归属。** 当前 CN/EN 模板正文可精确识别，允许版本戳不同；对 `2026-08-30.001152` 冻结两份历史正文指纹，先定位候选区间再核对完整哈希，因此 T3 压缩模板不会丢掉迁移旧安装的能力。
2. 未知历史正文、用户改入旧正文内部、无法唯一定位归属等情况明确报错，提示用户确认受管范围后再试；不自动把未知内容整份包入块，不制造旧新两套规则同时生效。没有新增迁移数据库、备份服务或安装时 Git 读取。
3. 完整性范围是安装器原本拥有的 `skills/sopify/**`；多余旧受管文件会随修复清除。`skills/` 下其他用户 Skill 保留；忽略 `.DS_Store`、`Thumbs.db`、`__pycache__` 与既有 copytree 政策一致。
4. Copilot 的既有 managed block 实现未改；Cursor 继续用独立 Plugin，不改成通用 home header。Cursor 只升级了完整树判断。
5. writer 的缺文件仍返回 `None`；合法对象原样返回；语法损坏 JSON 仍是 `JSONDecodeError`；只有合法 JSON 但非对象的情况改为明确的协议异常。

## 6. 全量结果、回归调整与保护检查

本机 `/usr/bin/python3` 为 3.9.6 且没有 pytest，使用已安装的 `/opt/homebrew/opt/python@3.11/libexec/bin/python3`（**3.11.15 / pytest 9.1.1**）。验证子进程将该目录置于 PATH 首位，并设置 `PYTHONDONTWRITEBYTECODE=1`、`PYTEST_ADDOPTS=-p no:cacheprovider`；没有修改全局 Python 或用户配置。

| 最终命令 | 退出码 | 关键输出 |
|---|---:|---|
| `python3 -m pytest tests -q` | 0 | `423 passed, 97 subtests passed in 37.18s` |
| `bash scripts/release-preflight.sh` | 0 | 全量再通过；catalog 无漂移、五个 protocol PASS、payload passed、`All checks passed.` |
| `git diff --check` | 0 | 无输出 |
| `git diff --cached --stat` | 0 | 无输出 |
| `git branch --list pr75-tests` | 0 | 无输出，临时分支已删 |

证据：[full-suite.txt](./w1-evidence/full-suite.txt)、[preflight.txt](./w1-evidence/preflight.txt)、[final-inventory.json](./w1-evidence/final-inventory.json)。

第一次全量发现两处旧 MCP 断言仍期望非对象 JSON 报 `ValueError`，见 [full-suite-first.txt](./w1-evidence/full-suite-first.txt)。按 T2 要求，读取边界现在抛已有的 `InvariantViolationError`（本身是 `ValueError` 子类），MCP 通用错误包装会呈现更精确的类名；只调整对应测试期望，未改 MCP 实现、工具返回结构或 writer/contracts schema。`{}` 与空 plan_id 仍期望 `ValueError`，无写入断言全部保留。

`tests/test_installer.py` 原 legacy bundle 兼容测试未删未改；独立 helper/Hook 源未改，相关既有测试和吸收的 Hook 分支测试都包含在本次全量中。主仓库 golden 未刷新，版本也未更新。

## 7. 交接事项

实现自查：`spec_compliance` 符合 W1 写集与授权边界，外部 CI 待补；`code_quality` 已核对共用读取/安装边界，完整性比较集中复用、异常迁移先拒绝再写入，最终全量和 preflight 均通过。这是执行方自查，不替代独立验收。

- **需要大脑继续：** 审这 16 个文件的 diff，交验收官独立复核，然后在用户允许 push 后取得真实 PR CI 链接。当前 worker 的本地通过不等于独立验收 pass，也不代写 receipt。
- **没有待裁决的实现分叉。** 对未知旧文件采用任务矩阵允许的明确拒绝；已知旧版的自动迁移已经有固定历史证据。
- **T3 注意：** 两份 `tests/fixtures/legacy-home-headers/*.md` 是冻结兼容夹具，不是当前生成物，不应跟随瘦身或版本 bump 重写；保留对应已发布正文指纹。
- **后续文案同步：** `scripts/regenerate-golden-snapshots.py` 顶部仍有旧注释称 preflight 会 auto-fix；它不在本任务允许写集，实际 preflight 已无此调用，可在后续维护文案清理时移除。T11 的 release notes 应说明 preflight 不再自动接受 golden、共享 home header 的迁移边界。
- 本报告没有将真实宿主加载、云端 CI 或独立验收写成已通过，也没有触碰方案进度、状态、history 或真实用户 home。
