# W1 阶段独立验收报告（T1 全量测试门与 T2 安装/writer 修复及返工复核）

**验收官**：Antigravity (Gemini)  
**验收对象**：执行官（Codex）在分支 `feat/sopify-narrow-focus`（基于 `43ee5f5`）上未暂存、未提交的工作区代码改动（包含首轮交付与返工交付）。  
**验收性质**：只读独立验收，不改仓库文件，不 commit，不写入真实用户 home。  
**参考基准**：
- 方案：`.sopify/plan/20261020_sopify_narrow_focus/plan.md`（统一验收标准）与 `tasks.md`（T1、T2 完成定义）
- 执行官报告：`w1-codex.md` 与 `w1-fix-codex.md`

---

## 总体结论：【通过（全部完成，具备推进至 W2 条件）】

本次验收对执行官交付的 W1 未提交改动进行了全量复核、本地全量测试复跑、发布前置脚本验证、3 项缺陷修前修后抽查、临时 home 亲手迁移实测，以及用户「统一验收标准」的逐项核对。

**核心结论汇总**：
1. **完成定义 (DoD)**：T1、T2 本地所有硬性指标均真实通过。本地全量测试实跑 **386 passed, 97 subtests passed**；`scripts/release-preflight.sh` 全流程退出 0 且零污染 git index；AUDIT-1 ~ AUDIT-4 缺陷修复精准无副作用；迁移矩阵 4 类边界测试完备。唯 CI 云端实跑因遵循用户 D4 授权决策（未获准不得 push/开 PR）标记为「有条件通过（待大脑获准 push 后云端验证）」，本地代码与工作流已完全就绪。
2. **迁移实验实测**：在隔离临时 home 中亲手执行了 3 个真实迁移场景（纯用户内容追加、旧版整份 header 迁移、用户内容夹心旧 header 迁移）。实测证实：旧版正文被精确替换为唯一受管块，版本平滑升级至 `2026-08-30.001152`，外部所有字节（CRLF、空行、前后注释）100% 原始保留，重复安装均严格 `skipped`（幂等）。
3. **统一验收标准**：返工轮彻底删除了首轮多余的 `_LEGACY_HEADER_HASHES` 哈希字典和多套模板匹配机制，改用精简的首尾锚点；生产代码净减 97 行；消除了跨模块私有调用；Copilot 与三大 Home 宿主统一复用一套受管块逻辑；卸载说明压缩至 7 行；无任何新增用户心智负担。五项标准**全部通过**。
4. **范围控制**：12 个被修改文件与 6 个新增测试/夹具文件全部严格对应 T1、T2 任务目标，**零超出范围改动**。

---

## 一、T1、T2 完成定义逐条核对

### 1.1 T1 全量测试门

| 验收项 | 判定 | 独立复核证据与细节 |
| :--- | :---: | :--- |
| **本地全量测试**<br>`python3 -m pytest tests -q` | **[通过]** | 独立运行命令：`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests -q`<br>输出：`386 passed, 97 subtests passed in 31.38s`，退出码 `0`。无任何 xfail 或 skip 遗留。 |
| **PR CI 实跑为绿** | **[有条件通过]**<br>*(待 Push 验证)* | 审查 `.github/workflows/ci.yml:56-58`，CI 门禁已由 7 个白名单文件改为收集全量：`python3 -m pytest tests/ -q`。<br>依据用户 D4 决策，本阶段禁止向远程 push 或开 PR。代码与配置已就绪，待协调员取得用户确认并推送分支后在 GitHub Actions 上核验最终链接。 |
| **preflight 遇 golden 漂移失败且 index 不变** | **[通过]** | 1. 独立运行定向测试：`python3 -m pytest tests/test_release_hooks.py -k preflight -q`，输出 `2 passed, 9 deselected in 2.36s`。<br>2. 独立运行全套脚本：`bash scripts/release-preflight.sh`，输出 `All checks passed.`，退出码 `0`。<br>3. 脚本运行后立即执行 `git diff --cached --stat`，输出完全为空；`scripts/release-preflight.sh:64` 已删除自动 `regenerate` 与 `git add`，遇漂移直接非 0 退出。 |
| **保留 catalog drift、protocol smoke、payload smoke** | **[通过]** | `scripts/release-preflight.sh:65-72` 真实执行并全绿：<br>- Builtin catalog drift check: PASS<br>- Protocol smoke (new-plan, continuation, clarification pending, decision pending, finalize): 全部 PASS<br>- Payload bootstrap smoke: `passed: true`。 |
| **release-sync.sh 职责保留** | **[通过]** | `scripts/release-sync.sh` 脚本未作非授权修改；`tests/test_release_hooks.py:test_release_sync_auto_drafts_unreleased_before_version_bump` 正常通过，显式发版时仍负责刷新模板与 golden 快照。 |

---

### 1.2 T2 安装与 writer 修复

| 验收项 | 判定 | 独立复核证据与细节 |
| :--- | :---: | :--- |
| **AUDIT-1 & 完整树完整性** | **[通过]** | 审查 `installer/hosts/base.py:378-394` (`skill_tree_matches`) 与 `installer/cursor_plugin.py:10`：<br>对自有树全文件比对（排查多余、缺失、损坏文件）。运行 `tests/test_cursor_cli_install_surface.py` 与 `tests/test_home_host_integrity.py`，损坏或截断的 phase skill 重装时返回 `updated` 并还原源内容，周围用户自定义 Skill 不受影响。 |
| **AUDIT-2 & AUDIT-3 (用户摘要)** | **[通过]** | 审查 `installer/distribution.py:852-853, 908`：<br>1. 空 smoke 输出：中文显示 `未执行运行时自检。`，英文显示 `Runtime smoke check was not run.`（消除 `(no smoke output)` 歧义）。<br>2. Cursor 显示名：`_host_display_name("cursor")` 正确返回首字母大写的 `Cursor`。<br>独立运行 `tests/test_install_user_summary.py` 全绿。 |
| **AUDIT-4 (writer 非对象防护)** | **[通过]** | 审查 `sopify_writer/io.py:19-23`：<br>`read_json` 增加严格类型检查：`if not isinstance(payload, dict): raise InvariantViolationError(...)`。<br>独立运行 `tests/test_sopify_writer_state_guards.py` 与 `tests/test_sopify_mcp_server.py:217`，非字典 JSON 均被拒绝且不污染已有状态。 |
| **迁移矩阵 4 类输入全覆盖** | **[通过]** | 独立运行 `tests/test_home_host_integrity.py`，覆盖：<br>1. 纯用户内容追加且幂等（4 宿主）；<br>2. 跨版本旧版整份迁移（2 个历史版本、中英文、LF/CRLF、模板变更前后）；<br>3. 混合内容保留外部字节与旧锚点混淆拒绝（7 种损坏全部拒绝且零写入）；<br>4. 合法块更新与异常 markers 报错（5 种非法 markers 拒绝且零写入）。 |
| **删掉 phase skill 重装自愈** | **[通过]** | `test_home_host_integrity.py::test_reinstall_repairs_the_complete_owned_tree` 实跑验证：删除 `develop/SKILL.md` 后执行安装，返回 `updated` 并复原文件，同级个人 Skill 保留。 |
| **语言切换与用户 Skill 隔离** | **[通过]** | `test_language_switch_and_ignored_cache_preserve_other_skills` 实跑验证：CN 切 EN 返回 `updated`，英文阶段文件更新；重复安装返回 `skipped`；同目录下 `my-other-skill/SKILL.md` 原封不动。 |
| **卸载文档说明** | **[通过]** | 审查 `docs/getting-started.md:259-267`：明确说明保留 `.sopify/`；仅需移除 instruction 文件内的 `<!-- BEGIN SOPIFY MANAGED BLOCK -->` 至 `<!-- END SOPIFY MANAGED BLOCK -->` 区间，保留外部用户配置。 |
| **保留边界验证** | **[通过]** | 独立运行 `tests/test_installer.py -k legacy -q`，输出 `4 passed`，legacy bundle 兼容逻辑未受损害；独立 helper fallback 测试通过。 |

---

### 1.3 关键缺陷修前修后抽查验证

#### 抽查 1：AUDIT-4（`sopify_writer/io.py` 阻止非对象 JSON 读取）
- **修前行为**：`json.loads(...)` 直接解析，对 `[1, 2, 3]`、`null`、`"foo"` 或标量返回非 dict 类型，在后续操作（如 `finalize`）时引发裸 `AttributeError`，未在状态读取边界建立防御。
- **修后行为**：`read_json` 增加显式类型断言：
  ```python
  payload = json.loads(path.read_text(encoding="utf-8"))
  if not isinstance(payload, dict):
      raise InvariantViolationError(f"Expected a JSON object in {path}, got {type(payload).__name__}")
  return payload
  ```
- **验证命令与输出**：
  ```bash
  python3 -c "
  import tempfile, json, pathlib
  from sopify_writer.io import read_json
  from sopify_writer.invariants import InvariantViolationError
  with tempfile.TemporaryDirectory() as t:
      p = pathlib.Path(t)/'state.json'
      p.write_text('[1, 2]', encoding='utf-8')
      try:
          read_json(p)
      except InvariantViolationError as e:
          print('PASS:', e)
  "
  ```
  输出：`PASS: Expected a JSON object in /.../state.json, got list`。边界拦截生效，原状态无写入。

#### 抽查 2：AUDIT-2 & AUDIT-3（`installer/distribution.py` 用户摘要优化）
- **修前行为**：空 smoke 输出在安装摘要中展示英文或占位符 `(no smoke output)`；Cursor 宿主名称在摘要中显示为小写 `cursor`。
- **修后行为**：
  ```python
  def _friendly_smoke_summary(smoke_output: str, language: str) -> str:
      if not smoke_output.strip():
          return "未执行运行时自检。" if language == "zh-CN" else "Runtime smoke check was not run."
      ...
  def _host_display_name(host_id: str) -> str:
      return { ..., "cursor": "Cursor" }.get(host_id, host_id)
  ```
- **验证命令与输出**：
  ```bash
  python3 -c "
  from installer.distribution import _friendly_smoke_summary, _host_display_name
  assert _friendly_smoke_summary('', 'zh-CN') == '未执行运行时自检。'
  assert _friendly_smoke_summary('', 'en-US') == 'Runtime smoke check was not run.'
  assert _host_display_name('cursor') == 'Cursor'
  print('PASS: AUDIT-2 & AUDIT-3 verified')
  "
  ```
  输出：`PASS: AUDIT-2 & AUDIT-3 verified`。

---

## 二、亲手实测临时 Home 迁移实验（三个场景）

在隔离的临时目录（模拟用户真实 `$HOME`，绝对路径在 `/var/folders/.../T/`）使用真实 `install_host_assets(CLAUDE_ADAPTER, ...)` 运行迁移实验。历史模板取自真实 tag `git show 2026-08-22.134737:skills/zh/header.md.template`（包含 283 行完整旧版正文与 `SOPIFY_VERSION: 2026-08-22.134737`）。

### 2.1 场景一：只有用户内容的 CLAUDE.md

- **初始文件内容（Before）**：
  ```markdown
  # User Custom Instructions

  - Do not use deprecated APIs.
  - Keep imports sorted.
  ```
- **迁移后文件内容（After）**：
  ```markdown
  # User Custom Instructions

  - Do not use deprecated APIs.
  - Keep imports sorted.

  <!-- BEGIN SOPIFY MANAGED BLOCK -->
  <!-- bootstrap: lang=zh-CN; encoding=UTF-8 -->
  <!-- SOPIFY_VERSION: 2026-08-30.001152 -->
  <!-- ARCHITECTURE: Adaptive Workflow + Layered Rules -->

  # Sopify - 自适应 AI 编程助手
  ... (完整新版受管规则正文) ...
  <!-- END SOPIFY MANAGED BLOCK -->
  ```
- **验证事实**：
  1. `after.startswith(before)` 为 `True`（原始用户字节、空行完全保留）；
  2. `BEGIN` 和 `END` 受管块标记恰好各出现 1 次；
  3. 执行器返回动作：首装 `updated`；再次运行返回 `skipped`（幂等性完全保障）。

---

### 2.2 场景二：旧版整份 Sopify header（无 markers）

- **初始文件内容（Before，取自 tag `2026-08-22.134737`）**：
  ```markdown
  <!-- bootstrap: lang=zh-CN; encoding=UTF-8 -->
  <!-- SOPIFY_VERSION: 2026-08-22.134737 -->
  <!-- ARCHITECTURE: Adaptive Workflow + Layered Rules -->

  # Sopify - 自适应 AI 编程助手
  ... (旧版 283 行规则正文) ...
  **方案包路径：** `.sopify/plan/YYYYMMDD_feature_name/`
  ```
- **迁移后文件内容（After）**：
  ```markdown
  <!-- BEGIN SOPIFY MANAGED BLOCK -->
  <!-- bootstrap: lang=zh-CN; encoding=UTF-8 -->
  <!-- SOPIFY_VERSION: 2026-08-30.001152 -->
  <!-- ARCHITECTURE: Adaptive Workflow + Layered Rules -->

  # Sopify - 自适应 AI 编程助手
  ... (新版受管规则正文) ...
  <!-- END SOPIFY MANAGED BLOCK -->
  ```
- **验证事实**：
  1. `after.startswith("<!-- BEGIN SOPIFY MANAGED BLOCK -->")` 为 `True`；
  2. 旧版本号 `2026-08-22.134737` 完全消失，已无缝升级为新版本号 `2026-08-30.001152`；
  3. 旧版未受管整份内容被完整收拢为单一受管块，没有出现新旧两份规则并存的污染现象；
  4. 再次安装返回 `skipped`。

---

### 2.3 场景三：旧版 header 前后各夹一段用户内容

- **初始文件内容（Before）**：
  ```markdown
  # User Header Note

  Preserve this note at top.

  <!-- bootstrap: lang=zh-CN; encoding=UTF-8 -->
  <!-- SOPIFY_VERSION: 2026-08-22.134737 -->
  ... (旧版 283 行规则正文) ...
  **方案包路径：** `.sopify/plan/YYYYMMDD_feature_name/`


  # User Footer Note

  Preserve this note at bottom.
  ```
- **迁移后文件内容（After）**：
  ```markdown
  # User Header Note

  Preserve this note at top.

  <!-- BEGIN SOPIFY MANAGED BLOCK -->
  <!-- bootstrap: lang=zh-CN; encoding=UTF-8 -->
  <!-- SOPIFY_VERSION: 2026-08-30.001152 -->
  ... (新版受管规则正文) ...
  <!-- END SOPIFY MANAGED BLOCK -->


  # User Footer Note

  Preserve this note at bottom.
  ```
- **验证事实**：
  1. 头部前缀 `after.startswith(prefix)` 为 `True`（字节完全相同）；
  2. 尾部后缀 `after.endswith(suffix)` 为 `True`（字节完全相同）；
  3. 中间旧版规则区域被精确识别并替换为受管块，旧版内容被彻底清理；
  4. 再次安装返回 `skipped`。

---

## 三、用户统一验收标准逐条判定

依据用户 2026-10-20 提出的 5 项统一验收标准，结合代码 diff 与测试，逐条裁定如下：

### 3.1 不过度设计：【通过】
- **核对标准**：没有为未发生的场景预建机制、表或配置。
- **审查证据**：
  - 首轮实现中曾设计了包含特定版本 SHA-256 的 `_LEGACY_HEADER_HASHES` 字典、双重模板文本比对及复杂的哈希链机制，带有过度设计的痕迹。
  - 返工轮（`installer/bootstrap_workspace.py:1140-1155`）彻底删除了该字典与复杂指纹，简化为基于首行 `<!-- bootstrap: ... -->` 与末行 `**方案包路径：** ...` 的**通用首尾锚点识别**。
  - 没有引入迁移数据库、额外配置文件或历史版本比对服务。
  - 生产代码净减少 **97 行**。

### 3.2 符合设计规范：【通过】
- **核对标准**：沿用仓库已有的模块边界与命名，不跨模块引用私有实现。
- **审查证据**：
  - 首轮在 `installer/cursor_plugin.py` 中跨模块引用了 `base._skill_tree_matches` 私有函数。
  - 返工轮在 `installer/hosts/base.py:378` 将其正式定义为公开函数 `skill_tree_matches`，并在 `installer/cursor_plugin.py:10` 中标准导入使用。
  - 标记解析异常统一抛出标准 `ValueError`，在 `installer/hosts/base.py:_write_managed_block` 中转为对外标准的 `InstallError`，异常契约整齐划一。

### 3.3 不冗余：【通过】
- **核对标准**：同一能力只有一份实现；文档同一事实只写一处。
- **审查证据**：
  - 受管块定位、校验、追加与写入逻辑全部收敛在 `installer/bootstrap_workspace.py` 的 `upsert_managed_instruction_block` 与 `_managed_instruction_block_span`，Copilot、Claude、Codex、Qoder 全部共享同一实现。
  - 删除逻辑 `_remove_managed_instruction_block` 同样复用 `_managed_instruction_block_span`，不再维护第二套正则。
  - 测试用例在返工轮进行了大幅收敛，`test_home_host_integrity.py` 删减了冗余的重复排列组合，从 81 例精简至 44 例，测试执行耗时降至 4.49s。
  - 卸载说明在 `docs/getting-started.md` 中压减为统一的 7 行说明，不再分散重复。

### 3.4 与其他宿主整体一致：【通过】
- **核对标准**：同类行为（managed block、安装、Doctor、文案）在各宿主之间语义一致；Cursor 不受影响。
- **审查证据**：
  - **Managed block 语义一致**：Copilot、Claude、Codex、Qoder 均统一使用 `<!-- BEGIN SOPIFY MANAGED BLOCK -->` 与 `<!-- END SOPIFY MANAGED BLOCK -->`；遇到异常 markers（缺失、反转、重复、嵌套）时，所有宿主均统一拒绝并抛出异常，绝不进行静默改写或部分写入。
  - **Cursor 隔离性**：Cursor 继续保持其独立的 Plugin 布局与轻量规则，未被强行套用 home header 模式；同时接入了统一的 `skill_tree_matches`，确保 Cursor 自有 Skill 完整性修复能力与 home 宿主保持等同水准。

### 3.5 不增加用户心智负担：【通过】
- **核对标准**：不新增用户需要理解的概念、步骤或手工操作；升级不要求用户手动处理。
- **审查证据**：
  - **升级平滑**：从旧版本 Sopify 升级时，用户无需执行任何先验迁移命令，也无需手动给旧文件加标记，重新运行一次安装器即可全自动完成受管块迁移。
  - **卸载简洁**：`docs/getting-started.md:258-267` 清楚标明保留项目级 `.sopify/` 资产，仅需删除文件内的受管块标记及对应目录，概念直接、步骤清晰。

---

## 四、范围边界核查（有无超出 T1、T2 范围的改动）

审查当前工作区所有改动文件（`git status --porcelain`）：

```text
 M .github/workflows/ci.yml                     -> T1: CI 门禁改为收集全量测试
 M .sopify/plan/20261020_sopify_narrow_focus/plan.md -> 协调员/大脑维护的决策记录与统一验收标准
 M docs/getting-started.md                      -> T2: 卸载指南更新
 M installer/bootstrap_workspace.py             -> T2: 统一 managed block upsert 与锚点迁移
 M installer/cursor_plugin.py                   -> T2: 树完整性检查公开调用
 M installer/distribution.py                    -> T2: AUDIT-2/3 用户摘要与 Cursor 显示名
 M installer/hosts/base.py                      -> T2: 树完整性实现与 _write_managed_block 转发
 M scripts/regenerate-golden-snapshots.py       -> T1: 澄清 preflight 不再 auto-fix 的注释
 M scripts/release-preflight.sh                 -> T1: preflight 收集全量测试并禁止 auto-fix
 M sopify_writer/io.py                          -> T2: AUDIT-4 非对象 JSON 校验防御
 M tests/test_release_hooks.py                  -> T1: preflight 收集全量与 golden 漂移测试
 M tests/test_sopify_mcp_server.py              -> T2: 配合 AUDIT-4 调整测试错误码断言
?? tests/fixtures/legacy-home-headers/          -> T2: 冻结的旧版 header 测试夹具
?? tests/test_cursor_cli_install_surface.py     -> T2: 吸收 PR #75 的 Cursor 安装测试
?? tests/test_cursor_hook_branches.py           -> T2: 吸收 PR #75 的 Hook 分支测试
?? tests/test_home_host_integrity.py            -> T2: 统一受管块与迁移测试
?? tests/test_install_user_summary.py           -> T2: 吸收 PR #75 的摘要测试
?? tests/test_sopify_writer_state_guards.py     -> T2: 吸收 PR #75 的 writer 防护测试
```

**审查判定**：**【通过 / 零越界改动】**。全部改动均在 T1、T2 写集授权内，没有任何与任务无关的冗余文件或非授权逻辑。

---

## 五、验收官综合签署

- **最终验收裁决**：**【全部通过】**
- **必须修改项**：**无（0 项）**。
- **后续阶段建议**：
  1. 当前 W1 改动代码质量良好、测试严密、设计克制，建议大脑正式将当前工作区改动提交并归档 W1；
  2. 待用户授权 Push 后，触发 GitHub Actions 验证云端 CI 链接；
  3. 可以立即启动 W2 阶段任务（T6 接入文档、T3 入口压缩、T4 冗余清理）。
