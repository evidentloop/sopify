# Sopify 交用户前最终验收独立报告（只读）

**验收者**：独立验收官（Antigravity / Gemini 3.8 Flash，Orca worker `task_77904a394946` / `ctx_fb106e059e8e`）  
**候选版本**：[`2bee037`](file:///Users/weixin.li/code/github/sopify)（包含 `b81b93e..HEAD` 共 2 个增量提交：[`a49ac51`](file:///Users/weixin.li/code/github/sopify) 与 [`2bee037`](file:///Users/weixin.li/code/github/sopify)）  
**代码状态**：分支 `feat/sopify-narrow-focus`，工作区完全干净（`git status` 无未提交或未跟踪文件）  
**验收基准**：
- 前序验收报告：[`t10-accept-gemini.md`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/t10-accept-gemini.md)
- Qoder 图片验收报告：[`images-accept-qoder.md`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/images-accept-qoder.md)
- 新手测试问答与卡点记录：[`newbie/answers.md`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/newbie/answers.md)
- Codex 修复报告：[`newbie-fix-codex.md`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/newbie-fix-codex.md)
- 协议与任务大纲：`tasks.md`、`plan.md` 统一验收标准

---

## 一、综合验收结论

| 验收项目 | 裁决 | 核心结论 |
|---|:---:|---|
| **交用户前全量最终验收** | **【通过】** | **全线闭环，具备直接交付条件。** 上一轮 T10 的所有条件项（快速开始 Target 表缺失、宿主表克隆说明、产品形态图细节）均已完全修正；新手冷启动测试暴露的 8 项认知与操作卡点（A1、A4、B1、B4–B7、Qoder 语言变体、"no runtime" 术语冲突）全部以极小且精准的改动闭环修复；实测系统 Python 3.9 优雅拦截零 traceback；实测队友 clone 仓库自动修复 `.git/info/exclude` 忽略规则且完全幂等；全量 422 项测试、Preflight 7 大环节、链接与格式检查 100% 绿灯。无任何未决阻塞项或高风险隐患。 |

---

## 二、上一轮 T10 条件项与细节建议复核

在 commit [`a49ac51`](file:///Users/weixin.li/code/github/sopify) 中，针对 T10 报告中的条件项与 Qoder 的可选建议进行了集中修正，逐项复核如下：

| # | 条件项 / 建议 | 目标位置 | 候选版本修复现状 | 判定 |
|---|---|---|---|:---:|
| 1 | **快速开始 Target 表补齐** | [`README.md:41-42`](file:///Users/weixin.li/code/github/sopify/README.md#L41-L42)<br>[`README.zh-CN.md:41-42`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md#L41-L42) | 表格完整补入 `Antigravity`（`antigravity:zh-CN` / `antigravity:en-US`）与 `Trae（预览）` / `Trae (Preview)`。新用户首屏即可查得目标参数。 | **已通过** |
| 2 | **支持宿主表移除克隆安装说明** | [`README.md:114-117`](file:///Users/weixin.li/code/github/sopify/README.md#L114-L117)<br>[`README.zh-CN.md:114-117`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md#L114-L117) | 安装列统一为标准 `--target` 指令，彻底移除了 `从源码克隆安装：` 前缀，并删除了表格下方“Antigravity 和 Trae 需要克隆本仓库安装”的过时文本。发版时效性完全匹配。 | **已通过** |
| 3 | **产品形态图 Claude 名称统一** | [`sopify-product-form-release.svg`](file:///Users/weixin.li/code/github/sopify/assets/sopify-product-form-release.svg)<br>[`sopify-product-form-release-en.svg`](file:///Users/weixin.li/code/github/sopify/assets/sopify-product-form-release-en.svg) | 中英文两张产品形态图 HOST 栏卡片中的 `Claude` 均已更新为 `Claude Code`，与正文及架构图完全同构。 | **已通过** |
| 4 | **中文产品形态图状态词全中文** | [`sopify-product-form-release.svg`](file:///Users/weixin.li/code/github/sopify/assets/sopify-product-form-release.svg) | 状态词统一为「已验证」与「基线」，图例统一为「协议已验证」与「基线支持」，彻底消除中英状态词混排。 | **已通过** |

---

## 三、新手测试摩擦点核验矩阵（A1、A4、B1、B4–B7 等）

依据新手测试报告 [`newbie/answers.md`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/newbie/answers.md) 与修复报告 [`newbie-fix-codex.md`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/newbie-fix-codex.md)，在 commit [`2bee037`](file:///Users/weixin.li/code/github/sopify) 中完成专项闭环，核查矩阵如下：

| 编号 | 新手遇到的摩擦点 / 问题 | 修复策略与具体改动 | 代码与文档依据 | 现场复核裁决 |
|---|---|---|---|:---:|
| **A1** | **旧 Python 报错无用户可读提示**：系统 Python 3.9 下运行抛出 `ImportError: cannot import name 'StrEnum'` 原始堆栈。 | 在任何第三方/子模块导入前前置 `sys.version_info < (3, 11)` 检查，仅用标准库解析参数，向 `stderr` 打印单行双语人话提示并 `exit(1)`。同时保护 `sopify_init.py`。 | [`scripts/install_sopify.py:11-27`](file:///Users/weixin.li/code/github/sopify/scripts/install_sopify.py#L11-L27)<br>[`scripts/sopify_init.py:23-35`](file:///Users/weixin.li/code/github/sopify/scripts/sopify_init.py#L23-L35) | **已解决**<br>（见第四节实测 1） |
| **A4** | **安装后下一步提示与 README 脱节**：安装成功提示 `2. Type: ~go`，但空项目直接输入裸 `~go` 无意义，与快速开始 `~go plan <需求>` 不一致。 | `installer/distribution.py` 将普通安装与显式预热共 4 处分支的下一步提示统一改为 `~go plan <what you want to do>` 与 `~go plan <你要做的事>`。 | [`installer/distribution.py:595,606,664,675`](file:///Users/weixin.li/code/github/sopify/installer/distribution.py#L595) | **已解决** |
| **B1** | **非交互模式提问即结束本轮，新手以为出方案失败**：`-p` 模式下 Sopify 提出澄清问题后即退出，未生成 `plan.md`，新手产生严重挫败感。 | README 快速开始第 2 步与命令速查表中明确补充：“等你在对话里回答后才写 `plan.md`。非交互会话（如 `-p` / `--print`）下提问会结束本轮——把答案写进请求再发一次即可。” | [`README.md:52,109`](file:///Users/weixin.li/code/github/sopify/README.md#L52)<br>[`README.zh-CN.md:52,109`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md#L52) | **已解决** |
| **B4–B7** | **仓库文件变动与忽略规则不透明**：新手不知道运行后多出什么文件、哪些该提交；且忽略规则写在本地 exclude，clone 后无法共享。 | 1. README 新增「仓库里会多出什么」表格，清晰阐明 `sopify.json`（提交）、`plan/`与`history/`（提交）、`state/`（不提交，通过 exclude 忽略）。<br>2. 修复队友 clone 场景，见下项。 | [`README.md:63-71`](file:///Users/weixin.li/code/github/sopify/README.md#L63-L71)<br>[`README.zh-CN.md:63-71`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md#L63-L71) | **已解决** |
| **B6 (clone)** | **队友 Clone 场景忽略规则失效缺口**：队友 clone 已含 `sopify.json` 的仓库，旧入口规则因 `sopify.json` 存在而不调 helper，导致本地 `state/` 未被忽略。 | 扩展所有受管宿主 Header 模板中的入口规则：“首次受管写入前，若 `.sopify/sopify.json` 缺失，**或在 Git 仓库中 `git check-ignore -q .sopify/state/active_plan.json` 表明 state 未被忽略**，调用 helper……”利用原有 helper 的幂等修补能力自动补齐 exclude。 | [`skills/zh/header.md.template:31`](file:///Users/weixin.li/code/github/sopify/skills/zh/header.md.template#L31)<br>[`skills/en/header.md.template:31`](file:///Users/weixin.li/code/github/sopify/skills/en/header.md.template#L31)<br>[`skills/zh/cursor-plugin-rule.mdc.template:32`](file:///Users/weixin.li/code/github/sopify/skills/zh/cursor-plugin-rule.mdc.template#L32)<br>[`skills/en/cursor-plugin-rule.mdc.template:32`](file:///Users/weixin.li/code/github/sopify/skills/en/cursor-plugin-rule.mdc.template#L32) | **已解决**<br>（见第四节实测 2） |
| **Qoder Target** | **Qoder 缺少语言后缀**：表格仅标 `qoder`，未体现 `:en-US` 与 `:zh-CN`。 | 在两份 README 的快速开始表与宿主表中均补齐为 `qoder:zh-CN` / `qoder:en-US`。 | [`README.md:38,119`](file:///Users/weixin.li/code/github/sopify/README.md#L38)<br>[`README.zh-CN.md:38,119`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md#L38) | **已解决** |
| **No runtime** | **"no runtime" 术语冲突**：README 声称 "no runtime"，安装器输出却打印 `Runtime: ...`。 | README 与 Pages 全文将 "no runtime" / "没有运行时" 统一替换为更精确的 "no background process" / "没有后台进程" / "不会增加守护进程、编辑器或后台进程"。 | [`README.md:44`](file:///Users/weixin.li/code/github/sopify/README.md#L44)<br>[`README.zh-CN.md:44`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md#L44)<br>[`index.html:219`](file:///Users/weixin.li/code/github/sopify/index.html#L219)<br>[`zh-CN.html:211`](file:///Users/weixin.li/code/github/sopify/zh-CN.html#L211) | **已解决** |

---

## 四、现场独立实测记录

验收官在独立会话环境内进行了现场实测，绝不依赖前置报告的声称。

### 实测 1：真实 macOS 系统 Python 3.9.6 下执行安装脚本

**测试命令**：
```bash
/usr/bin/python3 scripts/install_sopify.py --target qoder:en-US
/usr/bin/python3 scripts/install_sopify.py --target qoder:zh-CN
```

**实测输出记录**：
```text
$ /usr/bin/python3 scripts/install_sopify.py --target qoder:en-US
Sopify needs Python 3.11 or newer; current version: 3.9.6.
[exit code: 1]

$ /usr/bin/python3 scripts/install_sopify.py --target qoder:zh-CN
Sopify 需要 Python 3.11 或更新版本，当前为 3.9.6。
[exit code: 1]
```
**核查结果**：
1. 退出码精确为 `1`；
2. 没有任何 Python `Traceback` 或内部模块导入报错；
3. 输出纯粹为人话版本要求与当前版本；
4. 未对工作区或用户目录产生任何未预期的文件修改。**完全符合预期。**

---

### 实测 2：队友 Clone 仓库场景（带提交的 `sopify.json`）与入口规则自动修复

**测试设计**：
在 `/tmp/sopify-clone-sim-XXXXXX` 创建隔离环境，配置独立临时 HOME。
1. 在源仓库中通过 helper 初始化，提交 `.sopify/sopify.json`；
2. 执行 `git clone` 得到全新的克隆仓库（此时克隆仓库中已有 `sopify.json`，但其本地 `.git/info/exclude` 为初始状态，不包含 Sopify 规则）；
3. 检查克隆仓库入口条件：
   - `marker_exists`: `True`
   - `git check-ignore -q .sopify/state/active_plan.json`: 返回码 `1`（表明 `state` 尚未被忽略）；
   - 新入口规则逻辑表达式：`若 .sopify/sopify.json 缺失，或在 Git 仓库中 state 未被忽略，调用 helper` $\to$ **触发调用**！
4. 宿主自动调用 helper：`python3 .../bootstrap_workspace.py --workspace-root <clone> --request "~go" --interaction-mode interactive`；
5. 验证 helper 执行结果与本地 Git 状态：
   - helper 返回：`{"action": "updated"}`；
   - 再次执行 `git check-ignore -q .sopify/state/active_plan.json`：返回码 `0`（已正确忽略！）；
   - 测试业务方案文件 `git check-ignore -q .sopify/plan/20261021_demo/plan.md`：返回码 `1`（确保方案文件**绝不**被忽略）；
   - 在克隆仓库创建 `.sopify/state/active_plan.json` 后运行 `git status --porcelain`：输出为空，工作区保持完全干净；
   - 再次调用 helper 测试幂等性：返回 `{"action": "skipped"}`，文件内容与 mtime 完全未变。

**实测控制台输出**：
```text
[1] Install success into fake_home
[1.1] Helper found: /var/folders/9p/ghsv0fvd1zv8rb5jldxvbcsh0000gq/T/sopify-clone-sim-w3qate_z/fake_home/.qoder/sopify/helpers/bootstrap_workspace.py
[2] Source bootstrap outcome: bootstrapped
[2.1] Committed .sopify/sopify.json to source repo
[3] Cloned to teammate repo
[4.1] Marker .sopify/sopify.json exists: True
[4.2] State ignored before helper: False (returncode 1)
[4.3] Entry rule triggers helper: True
[5] Clone helper outcome: updated
[6.1] State ignored after helper: True (returncode 0)
[6.2] plan.md ignored: False (returncode 1)
[6.3] Git status with state file created: ''
[7] Helper rerun outcome: skipped

ALL CLONE SIMULATION CHECKS PASSED PERFECTLY!
```
**核查结果**：新入口规则天衣无缝地修补了队友 clone 场景下本地忽略规则缺失的问题，且不污染已跟踪的 Git index，幂等性测试 100% 成立。

---

## 五、自动化质量网关与基线复核

在干净的工作区执行全量自动化验证，记录如下：

```text
==================================== 自动化网关记录 ====================================
1. 全量单元测试与子测试 (Python 3.11):
   $ PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider" \
     /opt/homebrew/opt/python@3.11/libexec/bin/python3 -m pytest tests -q
   --> 422 passed, 101 subtests passed in 38.27s (exit 0)

2. README 规范与双语对齐检查:
   $ /opt/homebrew/opt/python@3.11/libexec/bin/python3 scripts/check-readme-links.py
   --> README validation passed:
         - SOPIFY_VERSION: 2026-08-30.001152
         - README.md body lines: 125
         - README.zh-CN.md body lines: 125 (预算 <= 250 行，全部符合)

3. 代码格式与空白检查:
   $ git diff --check b81b93e..HEAD
   --> clean (exit 0)

4. 发版前置检查全流程 (release-preflight.sh):
   $ PATH="/opt/homebrew/opt/python@3.11/libexec/bin:$PATH" bash scripts/release-preflight.sh
   --> [release-preflight] Check version consistency: passed (2026-08-30.001152)
   --> [release-preflight] Check golden snapshots: 28 passed
   --> [release-preflight] Check builtin catalog drift: passed
   --> [release-preflight] Run full test suite: 422 passed, 101 subtests passed
   --> [release-preflight] Run protocol smoke — new-plan: PASS
   --> [release-preflight] Run protocol smoke — continuation: PASS
   --> [release-preflight] Run protocol smoke — continuation (clarification pending): PASS
   --> [release-preflight] Run protocol smoke — continuation (decision pending): PASS
   --> [release-preflight] Run protocol smoke — finalize: PASS
   --> [release-preflight] Run install/payload bootstrap smoke: passed (passed=true)
   --> [release-preflight] All checks passed. (exit 0)
=======================================================================================
```

---

## 六、统一验收标准（仅风险与不通过项审查）

按指令约定，统一验收标准仅列举不通过或潜在风险项：

- **不通过项**：**无（0 项）**。
- **潜在风险与已知边界说明**：
  1. **非交互终端提问交互边界**：在 `qodercli -p` 或 `claude -p` 等非交互（无 TTY）会话中，若需求清晰度低于 7 分，Sopify 按规范提出澄清追问并安全退出当前回合，不会强行生成方案。该行为属于设计意图，README 已在快速开始与速查表中显式告知用户解决方案（“把答案写进请求再发一次即可”），不再构成新用户的认知卡点。
  2. **旧版克隆仓库的历史文件防御**：如果用户的项目在过去的旧版本中误将 `.sopify/state/` 提交到了 Git 远程仓库，clone 后该文件由于已在 Git index 中，`git check-ignore` 仍无法阻断已跟踪文件的更改。这属于 Git 原生机制，本轮入口规则修补聚焦于“正常 clone 后新建本地 state 不被误提交”，边界界定精准合理，不越权清理用户的 Git index。
  3. **产品封面与 OG 分享卡片**：`assets/sopify-cover*.jpg` 与 `assets/sopify-og-*.jpg` 保留了原英文口号，未做重新设计。这与 T10 报告中的留存项一致，不影响 README 的核心阅读体验与技术准确性。

---

## 七、最终裁定与交付签字

**最终结论：【通过】**

从 [`b81b93e`](file:///Users/weixin.li/code/github/sopify) 到当前 HEAD [`2bee037`](file:///Users/weixin.li/code/github/sopify) 的改动范围严格受控、定位精准、验证周密。代码、文档、视觉素材与自动化测试完全一致。

**本验收官正式签字确认：代码库具备合入主分支、推向 GitHub 远程仓库并呈交最终用户本人 sign-off 的全部条件。**
