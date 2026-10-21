# 新手安装问题修复报告

已完成版本提示、安装下一步和 clone 后本地忽略规则三项最小修复。全量测试 **422 passed, 101 subtests passed**；release preflight 全通过，`git diff --check` 通过。

基线：`feat/sopify-narrow-focus`，`a49ac5107e64edb5e1e9a47683160c2cbec1d0a2`。任务依据为 `task-codex-newbie-fix.md` 和 `newbie/answers.md` 的 2.1、2.4、3.4 B6。本轮未 commit、未 push，未改 README/Pages、方案/state/history 或真实用户 home；工作区中的 README/Pages 改动由并行任务持有，已保留。

## 1. Python 版本提示

- `scripts/install_sopify.py:11` 在任何 `installer` 导入前拦住 Python < 3.11，仅使用标准库，输出当前版本和要求后以 1 退出。语言按显式 target 的语言、`--language` 和 `LANG` 选择。
- 同时保护 `scripts/sopify_init.py:23`。实测旧脚本在系统 Python 3.9.6 下并非同样 traceback，而是捕获 `ImportError`、跳过 Copilot 指令生成，仍输出成功；因此也前置版本检查，避免产生部分初始化后报成功的情况，没有改初始化业务逻辑。
- 两个入口分别用真实 `/usr/bin/python3` 验证中英文，共 4 次：均 exit 1、stdout 为空、无 traceback、临时 home/项目为空。示例输出：

```text
Sopify needs Python 3.11 or newer; current version: 3.9.6.
Sopify 需要 Python 3.11 或更新版本，当前为 3.9.6。
```

证据：[修改前](./newbie-fix-evidence/python-before.json)、[真实 Python 3.9 修改后](./newbie-fix-evidence/python39-after.json)。自动测试另在独立子进程模拟 3.9.6，覆盖两脚本及两语言；正常 Python 3.11 安装/初始化继续由原有测试验证。

## 2. 安装完成的下一步

`installer/distribution.py` 的中英文普通安装及显式预热两个分支，共 4 处，改为：

```text
2. Type: ~go plan <what you want to do>
2. 输入：~go plan <你要做的事>
```

用户说明仍保留“首次 ~go 时自动设置项目文件”的原有通俗表达，未加入 helper、非交互等内部术语。Cursor 的重启/Plugin 检查、Copilot 的自动加载指引维持原状，因为这些分支原本没有 `Type: ~go`。同步的输出断言覆盖双语、普通安装/预热及实际 CLI 输出。

## 3. 队友 clone：确认存在缺口，只改入口条件

使用临时 Qoder 安装、临时 Git 源仓库和临时 clone，模拟已提交 `.sopify/sopify.json` 的接手场景。fixture 提交仅存在于一次性临时仓库，主仓库未提交。

| 步骤 | 结果 |
|---|---|
| 原仓库首次 helper | `bootstrapped`，忽略块写入本地 `.git/info/exclude` |
| clone | marker 存在，但本机 exclude 没有受管块 |
| 创建临时 state 探针 | `git check-ignore -q .sopify/state/active_plan.json` 返回 1；`git status --porcelain --untracked-files=all` 出现 `?? .sopify/state/active_plan.json` |
| 调用原样 helper（请求 `~go`） | `READY` / `updated`，补齐本机 exclude；check-ignore 返回 0，Git 待提交列表为空 |
| 再调同一 helper | `skipped`；exclude 字节和 mtime 不变，marker 字节不变 |

因此旧入口“marker 缺失才调用 helper”会漏掉新 clone。现有 helper 已具备补齐和幂等能力，无须修改 `installer/bootstrap_workspace.py`。

最小修改为中英文 header 和 Cursor rule 中同一条入口条件：首次受管写入前，若 marker 缺失，**或在 Git 仓库中上述 check-ignore 表明 state 未被忽略**，调用原有 helper。保持完整请求、实际交互模式、失败停车和 writer 导入方式不变；consult/quick_fix 不进入此流程，非 Git 目录不执行 Git 忽略检查。

测试还确认保留用户自有 exclude 规则、不重复插入块、方案文件不被忽略。双语路径测试覆盖 Codex、Claude Code、Qoder、Antigravity、Trae、Cursor 的已安装入口；Copilot 继续不生成全局 helper 路径。证据：[clone 与 helper 探针](./newbie-fix-evidence/clone-helper-probe.json)，回归用例为 `tests/test_payload_entry_paths.py:57`。

这证明 Git/安装产物及 helper 的行为；本轮没有跑新的真实宿主会话，不把入口文字断言视为模型必然遵循的黑盒证明，也未更新真实宿主安装。已跟踪进 index 的旧 state 不属于本次“clone 后新建本地 state”的修复范围，未扩大为清理历史文件或新机制。

## 4. 验证

验证环境：`PYTHONDONTWRITEBYTECODE=1`、`PYTEST_ADDOPTS="-p no:cacheprovider"`；全量和 preflight 的 HOME 为一次性临时目录，PATH 首位为 `/opt/homebrew/opt/python@3.11/libexec/bin`，保证嵌套的 `python3` 也为 3.11。Python 3.9 探针显式使用 `/usr/bin/python3`。

| 检查 | 最终结果 | 日志 |
|---|---|---|
| 版本/输出/入口路径/初始化定向测试 | 52 passed, 8 subtests passed | [targeted.log](./newbie-fix-evidence/targeted.log) |
| Python 3.11 `-m pytest tests -q` | 422 passed, 101 subtests passed | [full-tests.log](./newbie-fix-evidence/full-tests.log) |
| `bash scripts/release-preflight.sh` | exit 0；版本、golden、catalog、全量、5 项协议 smoke、安装/payload smoke 全通过 | [preflight.log](./newbie-fix-evidence/preflight.log) |
| `git diff --check` | exit 0 | 完成前再次执行 |

首轮全量有两项失败：新增入口条件导致 header 体积基线过期；以及未给嵌套子进程固定 PATH，使 release fixture 的 `python3` 误用系统 3.9 并跳过 golden 再生。前者仅更新两种语言的 `header_after` 数值，后者仅修正本次验证环境，最终完整重跑通过；首轮日志保留在 [full-tests-first.log](./newbie-fix-evidence/full-tests-first.log)。

已审核后显式更新 golden：仅 Codex/Claude header 与 Antigravity/Trae prompt tree 的 8 项摘要变化；Copilot payload 和阶段 Skill tree 的 4 项摘要不变。header 体积：中文 6008 → 6110 bytes，英文 6970 → 7082 bytes，均保持 62 行。没有引入新依赖、新开关或新的用户操作步骤。

## 5. 实际写集

共 12 个仓库文件；逐文件 SHA-256 与基线记录见 [changed-files.json](./newbie-fix-evidence/changed-files.json)。

- `installer/distribution.py`
- `scripts/install_sopify.py`
- `scripts/sopify_init.py`
- `skills/en/header.md.template`
- `skills/zh/header.md.template`
- `skills/en/cursor-plugin-rule.mdc.template`
- `skills/zh/cursor-plugin-rule.mdc.template`
- `tests/test_distribution.py`
- `tests/test_install_user_summary.py`
- `tests/test_payload_entry_paths.py`
- `tests/golden-snapshots.json`
- `tests/behavior-scenarios/plain-language-output-v1.json`

报告和取证日志仅写在外部 scratchpad。主仓库 Git index 无变更；后续独立验收和提交由协调者处理。
