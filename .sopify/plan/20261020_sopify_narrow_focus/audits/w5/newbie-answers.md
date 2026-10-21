# Sopify 新手测试记录

信息来源：仅本目录 `README-sopify.md`（未搜索网络，未读本目录以外的文件，安装命令除外）。
测试环境：macOS (darwin arm64)，`qodercli 1.1.75`，`/usr/bin/python3` = Python 3.9.6。

---

## 第一步：只读 README 的 5 个问题

### 1. Sopify 是什么？

Sopify 是一套「规则 + Skills」，安装进你已经在用的 AI 编码工具（Codex / Claude Code / Qoder / Copilot / Cursor / Antigravity / Trae）里；当一项工作需要方案时，它把方案、决策和验证证据以普通文件的形式存进仓库的 `.sopify/` 目录。它明确说「Not a new editor, not a new CLI」，也不是守护进程或运行时。
依据：README 开头正文段（"Sopify is a set of rules and Skills that installs into the AI coding tool you already use…"）与 Quick Start 第 1 步下的说明（"It writes host instructions and Skills only — no daemon, no runtime, no new editor."）。

### 2. 它对我有什么价值、解决什么问题？

它解决的是「上下文只活在一次会话里」的问题：README 列了三个场景——长任务被打断后 `~go` 会读 `.sopify/plan/` 从下一个未完成的任务续上；换一个工具或换一个人接手时不用再粘贴上下文（README 说这次发布本身就是 Claude Code 写的方案被一个只输入 `~go` 的全新 Qoder 会话接着做完的）；多个 agent 分工时由一个 owner 持有方案、worker 领有边界的任务、证据集中在一处。
依据：README "Where It Pays Off" 三段（A long task gets interrupted / Another tool or another person takes over / Several agents split the work）以及顶部标语 "AI coding plans and proof in your repo"。

### 3. 什么时候不需要用它？

三类情况不需要：提问、读代码、要解释；小修补（改名、错别字、一行风格调整）；一次性脚本和探索性尝试。README 说这些「are handled directly and never enter the plan workflow」，方案只在三种情况下才开始：你用 `~go plan` 主动要求、你要求继续在做的工作、或 `~go` 判断这个请求需要方案。
依据：README "When Not to Use It" 一节。

### 4. 怎么开始？写出你要执行的步骤。

按 README Quick Start，我要做的是三步：
1. 安装到我用的工具。我在 macOS 上用 shell 安装脚本，README 的表格里 Qoder 对应 `--target qoder`：
   `curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/install.sh | bash -s -- --target qoder`
   （前置条件：Python 3.11 或更新；README 说安装器会在下载前检查。）
2. 在项目里往聊天框输入一行 `~go plan <请求>`，例如 README 的 `~go plan add input validation to the signup form`；它会先追问未决问题，然后写 `.sopify/plan/YYYYMMDD_signup_form_validation/plan.md`，这一步不改业务代码。
3. 用 `~go` 按任务逐条实现并记录验证证据，完成后用 `~go finalize` 把方案移到 `.sopify/history/`。
   Windows 则改用 PowerShell 安装脚本（`install.ps1 --target codex:en-US`）代替第 1 步。
依据：README "Quick Start" 第 1/2/3 步与 "Command Cheat Sheet"。

（实测偏差见第二、三步：本次按 TASK.md 要求改用候选版安装命令，且 README 的 Qoder target 只写了 `qoder`，没有 `en-US` 变体。）

### 5. 用起来之后，我的仓库里会多出什么？

按 README 的说法，会多出一个 `.sopify/` 目录：方案阶段多出 `.sopify/plan/YYYYMMDD_<名字>/plan.md`；从真实案例的链接看，方案目录里还有 `receipts/verify_001.json`、`receipts/final.json` 这类验证回执文件；`~go finalize` 之后整个方案包会移到 `.sopify/history/YYYY-MM/`。README 强调「The plan and its evidence stay in git」，也就是这些文件是要提交的。README 没有提到会多出 `.sopify/sopify.json`，也没有提到会往 `.gitignore` 写东西——这两点我留到第三步实测核对。
依据：README Quick Start 第 2/3 步、"Command Cheat Sheet"、"A Real Case" 末尾的三个归档文件链接，以及 "Further Reading" 里提到的 "the four files a new session reads first, the `.sopify/` layout"。

---

## 第二步：按 README 安装

### 2.1 第一次执行（TASK.md 给的命令，原样）

```
$ python3 /Users/weixin.li/code/github/sopify/scripts/install_sopify.py --target qoder:en-US
Traceback (most recent call last):
  File ".../scripts/install_sopify.py", line 15, in <module>
    from installer.distribution import (
  ...
  File ".../installer/models.py", line 6, in <module>
    from enum import StrEnum
ImportError: cannot import name 'StrEnum' from 'enum'
  (/Library/Developer/CommandLineTools/.../python3.9/enum.py)
```

耗时 1 秒（11:34:50 → 11:34:51）。原因：本机 `python3` 是 Python 3.9.6，`StrEnum` 需要 3.11+。README 写了「Python 3.11 or newer; the installer checks before downloading」，但我看到的不是版本检查提示，而是一段 Python traceback——没有任何一句人话告诉我「你的 Python 太旧，请装 3.11」。

### 2.2 第二次执行（自己找到 python3.11 后重试）

机器上有 `/opt/homebrew/bin/python3.11`，用它重跑同一条命令，3 秒成功（11:35:26 → 11:35:29，exit 0）。输出如下：

```
Sopify installed successfully.

Installed:
  Host: Qoder (qoder:en-US)
  Language: English
  Host prompt: updated
  Runtime: /Users/weixin.li/.qoder/sopify
  Version: 2026-08-30.001152
  Runtime action: already current

Project:
  No project directory was changed.
  Sopify sets up project files the first time you run ~go in a project.

Next:
  1. Open Qoder in your project directory.
  2. Type: ~go

Diagnostics:
  Runtime smoke check was not run.
  Run again with `--verbose` for full install details.
```

### 2.3 「下一步」提示（原文记录）

> Next:
>   1. Open Qoder in your project directory.
>   2. Type: ~go

注意这里让我输入 `~go`，而 README Quick Start 第 2 步让我输入的是 `~go plan <request>`。两者不一致（详见第四步）。

### 2.4 安装阶段与 README 不一致的地方

| # | README 原句 | 实际 |
|---|---|---|
| A1 | "Python 3.11 or newer; the installer checks before downloading." | Python 3.9.6 下没有「检查」，直接抛 `ImportError: cannot import name 'StrEnum'` traceback。而且这句把检查描述成「下载前」的保护，对本地脚本路径不适用，新手读不出「3.9 根本跑不起来」这个后果。 |
| A2 | 表格 Qoder 行只写 `qoder`，其他每个 host 都是 `xxx:en-US` / `xxx:zh-CN` | `--target qoder:en-US` 被接受，且报告 `Language: English`。表格没写 Qoder 的语言变体，我读不出这是「Qoder 只有英文」还是「表格省略了」。 |
| A3 | "It writes host instructions and Skills only — no daemon, **no runtime**, no new editor." | 安装输出里有一行 `Runtime: /Users/weixin.li/.qoder/sopify`，还有 `Runtime action: already current`。同一个词 "runtime" 在 README 里是「不存在的东西」，在安装输出里是「装好的目录」，直接冲突。 |
| A4 | "Next: 2. Type: `~go`"（安装输出） vs "`~go plan add input validation to the signup form`"（Quick Start 第 2 步） | 两处给的命令不同。在一个刚 `git init`、没有 active plan 的仓库里，按安装提示输入裸 `~go` 是没有请求内容的。 |
| A5 | "It writes host instructions and Skills only" | 实际改的是**用户级全局**文件 `~/.qoder/agents.md`（安装过程中该文件被改写），以及 `~/.qoder/sopify/`。README 没说清这是全局生效、不是按项目生效，也没说会影响该项目之外的所有 Qoder 会话。 |
| A6 | README 版本徽章 `version-2026--08--30.001152` | 安装输出 `Version: 2026-08-30.001152`，与徽章一致。TASK.md 称这次装的是「候选版」，但从版本号上我无法区分它和已发布版——这是一个信息缺口，不是矛盾。 |
| A7 | "Diagnostics: Runtime smoke check was not run." | README 完全没提安装后还有 smoke check 这回事，也没说什么情况下会跑、不跑有没有风险。 |

---

## 第三步：按 README 跑第一个方案

### 3.1 准备

在 `newbie/demo/` 下 `git init`，放一个 6 行的 `calc.py`：

```python
def add(a, b):
    return a + b


def divide(a, b):
    return a / b
```

基线：`shasum -a 256 calc.py` = `f8fe1a17a9257471dab462a3d602c34752c71b2529327d304ea397d87bd5165a`。

### 3.2 运行 1：TASK.md 给的命令，原样

```
$ cd demo && qodercli -p --dangerously-skip-permissions "~go plan add a guard against division by zero in calc.py"
```

11:36:43 → 11:40:19，3 分 36 秒，exit 0。会话输出的关键部分：

- 第一行是 `6 errors loading agent configs. Use /agents to see details.`（两次运行都有）
- `[demo-ai] Requirements Analysis ?`，`Current score: **6/10**（goal clarity 3, expected outcome 1, scope boundary 2, constraints 0）— below the configured require_score of 7`
- 它问了两件事：`divide(a, 0)` 应该做什么（给了 ValueError / ZeroDivisionError / None / inf-nan 四个选项）、要不要包含测试
- 结尾自述：`Changes: workspace bootstrap only (.sopify/sopify.json, plus managed ignore rules in .git/info/exclude); no code or plan files written.`
- `Next: tell me which failure behavior you want (and whether to add tests), and I'll run Design…`

**运行 1 的四项检查结果：**

| 检查项 | 结果 |
|---|---|
| `.sopify/plan/` 下是否生成方案文件 | **没有**。`.sopify/` 下只有 `sopify.json` 一个文件，`plan/` 目录根本不存在。 |
| 是否生成 `.sopify/sopify.json` | **有**。内容：`{"bundle_version":"2026-08-30.001152","capabilities":[],"ignore_mode":"exclude","locator_mode":"global_first","schema_version":"1","stub_version":"1","workspace_kind":"external","written_by_host":true}` |
| `.gitignore` 里是否有受管块 | **没有 `.gitignore` 这个文件**。受管块写进了 `.git/info/exclude`：`# BEGIN sopify-managed` / `.sopify-payload/` / `.sopify/state/` / `# END sopify-managed`。`sopify.json` 里的 `"ignore_mode": "exclude"` 与此一致。 |
| `calc.py` 是否保持不变 | **保持不变**。sha256 与基线逐字符相同（`f8fe1a17…`），`git status` 里仍是 `?? calc.py`，未被修改。 |

### 3.3 运行 2（我加的补充探针）：把答案写进同一句请求

因为 `-p` 是非交互模式，运行 1 问完就结束，没有人能回答，方案永远不会被写出来。为了验证 README 承诺的 `plan.md` 到底能不能产出，我用同一条命令、只在请求尾部附上答案又跑了一次：

```
$ qodercli -p --dangerously-skip-permissions "~go plan add a guard against division by zero in calc.py. Answers to your questions: divide(a, 0) must raise ValueError('division by zero'); do not add tests or any new file, keep the scope to calc.py only."
```

11:41:21 → 11:47:30，6 分 9 秒，exit 0。这次成功出方案：

| 检查项 | 结果 |
|---|---|
| 方案文件路径 | **`.sopify/plan/20261021_divide_zero_guard/plan.md`**（level `light`，只有 `plan.md`，没有 `tasks.md`）。路径形状与 README 的 `YYYYMMDD_<名字>/plan.md` 一致。 |
| 其他新增文件 | `.sopify/state/active_plan.json`、`.sopify/state/current_handoff.json` |
| `.sopify/sopify.json` | 仍在，内容未变 |
| `.gitignore` | 仍然不存在；受管块仍在 `.git/info/exclude` |
| `calc.py` | **仍然未被修改**，sha256 依旧 `f8fe1a17…`。README 的 "It changes no business code at this step" 成立。 |
| 证据/回执 | **没有任何 receipt 文件**。会话自己解释了原因：`~go plan executed and verified nothing, so an exec/verify receipt would have been unsupported evidence.` |
| git 可见性 | `plan.md` 和 `sopify.json` 可提交（未被忽略）；`state/active_plan.json`、`state/current_handoff.json` 被 exclude 块忽略，**不会进 git** |

`plan.md` 里确实有可读的内容：front matter（`plan_id` / `status: planned` / `level: light` / `archive_ready: false`）、Context/Why、Scope、Approach（含具体代码片段）、Waves/Steps（W1.1–W1.3 三个未勾选的复选框）、Key Decisions（4 条，包括 `divide(0,0)` 也抛 ValueError 这个我自己没想到的边界）、Constraints/Not-in-scope、Status/Progress、Next。这部分质量是符合 README 描述的。

### 3.4 README 说的 vs 我实际看到的（逐条）

| # | README 原句 | 实际观察 |
|---|---|---|
| B1 | "Sopify asks about anything still unresolved, **then writes** `.sopify/plan/YYYYMMDD_signup_form_validation/plan.md`." | 在非交互（`-p`）模式下，「问」和「写」不是一次调用里连续发生的：它问完就结束本轮，**一个方案文件都没写**。必须再发一次带答案的请求才会写。README 这句读起来像一次输入就能拿到 `plan.md`。 |
| B2 | README 通篇没提评分门槛 | 实际有个 `require_score`（默认 7）的门禁：我的请求被打 6/10，低于门槛就直接停在 Analysis。README 的 Quick Start 和 "When Not to Use It" 都没提「请求可能因为分数不够而被拒绝出方案」，也没提怎么提高分数。 |
| B3 | "`~go plan <request>` … Writes `.sopify/plan/<id>/plan.md` and changes no code" | 「changes no code」成立；但「Writes plan.md」在第一次调用时不成立（见 B1）。 |
| B4 | README 从没提 `.sopify/sopify.json` | 它是**最先**被创建的文件（在有任何方案之前），而且是 workspace bootstrap 的一部分。新手按 README 无法预期它的存在，也不知道该不该提交它（实测：不会被忽略，会被提交）。 |
| B5 | README 从没提 `.sopify/state/` | 运行 2 之后多出 `state/active_plan.json` 和 `state/current_handoff.json`。 |
| B6 | README 从没提忽略规则 | 实测**不创建 `.gitignore`**，受管块写进 `.git/info/exclude`。这个区别有实际后果：`.git/info/exclude` 是本地文件、不随仓库分发，而 README 的卖点是 "so another supported tool can pick the work back up" / "another person takes over"——换一台机器 clone 仓库的人拿不到这条忽略规则。 |
| B7 | "The plan and its evidence stay in git, so another supported tool can pick the work back up." | 走完 Quick Start 第 2 步后，进 git 的只有一个 `plan.md`（加一个 `sopify.json`），**没有任何 evidence**（回执要到 `~go` 阶段才可能有），而 `state/` 是刻意被排除的。README 没区分 `.sopify/` 里哪些文件是设计成要提交的、哪些是本地状态。 |
| B8 | "type one line into the chat box" | 一行输入的实际代价：第一次 3 分 36 秒（无产出），第二次 6 分 9 秒（出方案），合计约 10 分钟 agent 时间，为一个 6 行文件的 2 行改动。README 对耗时和「可能需要来回一轮」没有任何预期管理。 |
| B9 | README 没提 host 之外还会显示一个项目代号 | 两次输出都以 `[demo-ai]` 开头。这个 `-ai` 后缀和它的来源（目录名 `demo`）README 里查不到。 |
| B10 | README 没提 agent 配置加载失败 | 两次运行的第一行都是 `6 errors loading agent configs. Use /agents to see details.`。我无法在本目录范围内判断它是不是 Sopify 造成的（TASK.md 限制我不读目录外文件），但作为新手第一次看到这句话是很不安的。 |
| B11 | "It changes no business code at this step." | ✅ 成立，两次运行后 `calc.py` 的 sha256 与基线完全一致。这是本次唯一一条 README 承诺与实际完全吻合、且我做了硬校验的项。 |

### 3.5 未测试的部分

Quick Start 第 3 步（`~go` 实现 + `~go finalize` 归档）我**没有跑**，TASK.md 只要求跑方案步骤。所以 README 关于「记录验证证据」「移到 `.sopify/history/`」「另一个工具能接手」的说法，本次测试没有任何证据支持或反驳。

---

## 第四步：第一印象

### 一看就懂的部分

- **开头那一段定义**（"Sopify is a set of rules and Skills that installs into the AI coding tool you already use… Not a new editor, not a new CLI."）非常准。读完我就知道它不是编辑器、不是 CLI、不常驻，以及产出物是 `.sopify/` 下的普通文件。这一段是整个 README 里效率最高的。
- **"When Not to Use It" 三条**（提问/读代码/解释、小修补、一次性脚本）具体到能直接对号入座，而且紧跟一句说明「这些直接处理，不进入方案流程」。我读的时候没有任何犹豫。
- **"Where It Pays Off" 的 Before/After 三段**结构很好，尤其 "Another tool or another person takes over" 那段直接说「这次发布就是这么做的——Claude Code 写的方案被一个只输入 `~go` 的全新 Qoder 会话接着做完」。这是全文最有说服力的一句，因为它是可验证的事实陈述而不是形容词。
- **"Command Cheat Sheet" 三行表格**（`~go plan` / `~go` / `~go finalize`）清楚到可以当书签用。
- **"Supported Hosts" 里对 Verified / Baseline / Preview 的定义**（"Verified means the managed workflow has been run in a real session on that host, not only installed"）诚实且有用，我立刻知道 Qoder 是真跑过的、Trae 还没跑过。

### 卡住或产生误解的部分（引用 README 原句）

1. **"Python 3.11 or newer; the installer checks before downloading."**
   这是我最实的一次卡壳。我按 TASK.md 跑 `python3 …/install_sopify.py`，得到的是 `ImportError: cannot import name 'StrEnum' from 'enum'` 的原始 traceback，没有任何「你的 Python 版本太旧」的提示。README 这句话给了我一个错误的安全感——我以为版本检查会拦住我并告诉我怎么办，实际上它连一句人话都没输出就崩了。我还得自己去找机器上有没有 3.11。**建议**：README 明说「Python 3.9 会直接抛 ImportError」，或者安装器真的先做检查。

2. **"Sopify asks about anything still unresolved, then writes `.sopify/plan/YYYYMMDD_signup_form_validation/plan.md`."**
   我把 "asks … then writes" 读成同一轮里的连续动作。实际在非交互模式下它问完就收尾，`plan.md` 一个都没有；我必须再发一次带答案的请求。README 没说「提问会结束本轮」，也没说非交互模式下要怎么接。加上完全没提到的 `require_score: 7` 门禁（我的请求被打 6/10 就被拦住了），新手很容易得出「我照 README 做了，但它没生成方案」的结论。**这是本次最容易让人放弃的一步。**

3. **"It writes host instructions and Skills only — no daemon, no runtime, no new editor."**
   紧接着安装输出就打印 `Runtime: /Users/weixin.li/.qoder/sopify` 和 `Runtime action: already current`。同一个词在两处指两件事。我第一反应是「README 说不装 runtime，为什么输出里有 Runtime 目录？」**建议**：安装输出改叫 `Bundle:` 或 `Payload:`，或者 README 别用 "no runtime" 这个词。

4. **安装输出的 "Next: 2. Type: `~go`" vs Quick Start 的 "`~go plan add input validation to the signup form`"**
   装完我手边就是那句 `Type: ~go`。但一个刚 `git init` 的空仓库没有 active plan，裸 `~go` 没有请求内容。两处应该一致，或者安装输出直接给带 `plan` 的完整示例。

5. **README 从头到尾没有列出「跑完之后仓库里会多出哪些文件」**，所以第一步的问题 5 我只能靠 "A Real Case" 末尾那三个归档链接反推。实际第一次运行产出的是 `sopify.json`（未提及）、`.git/info/exclude` 里的受管块（未提及）、后来的 `.sopify/state/*.json`（未提及）。**建议**：加一张「`.sopify/` 里有什么、哪些进 git、哪些被忽略」的小表——这正好也能回答问题 5。

6. **"The plan and its evidence stay in git"**
   我据此预期第 2 步之后能看到 evidence，实际上一个 receipt 都没有（会话解释是「`~go plan` 什么都没执行、什么都没验证，写回执就是伪造证据」——这个理由我认为是对的，但 README 没告诉我 evidence 要到 `~go` 阶段才出现）。另外 `state/` 被排除在 git 之外，README 也没区分哪些文件是设计成共享的、哪些是本地状态。

7. **忽略规则写进 `.git/info/exclude` 而不是 `.gitignore`**
   README 对此零字。这个选择有实际后果：`.git/info/exclude` 不随仓库分发，所以队友 clone 之后拿不到这条规则，而 README 的核心卖点恰恰是 "another person takes over"。作为新手我看不出这是有意设计还是遗漏。

8. **Qoder 在 target 表里只有 `qoder`，没有 `:en-US` / `:zh-CN`**
   其他六个 host 都有语言变体。我读不出这是「Qoder 不支持选语言」还是「表格写漏了」。实际上 `qoder:en-US` 是能用的，而且输出 `Language: English`。

9. **`6 errors loading agent configs. Use /agents to see details.`**
   两次运行的第一行都是这句。README 没提，我也没有权限在本次测试里去查原因。第一次跑就看见「6 errors」，对一个刚被 "Verified" 标签说服的新手来说是减分项。

10. **`[demo-ai]` 这个项目代号**
    输出里每轮都带这个前缀，README 没解释 `-ai` 后缀从哪来（看起来是目录名 `demo` 加 `-ai`），也没说能不能改、在哪改（配置那节只出现在 "Further Reading" 的一个链接里）。

### 用了几步、大约多久

按命令数：**8 步**（读 README → 写答案 → 安装失败 → 找 python3.11 → 安装成功 → 建 demo/git init/写 calc.py → 运行 1 → 运行 2 → 检查结果）。其中 agent 会话跑了 **2 次**，安装跑了 **2 次**（1 次失败）。

按时间（本机墙钟）：

| 阶段 | 时间 | 耗时 |
|---|---|---|
| 读 README + 写第一步答案 | 11:31 – 11:34 | ~4 min |
| 安装第 1 次（失败） | 11:34:50 – 11:34:51 | 1 s |
| 找 python3.11 | 11:35 | ~30 s |
| 安装第 2 次（成功） | 11:35:26 – 11:35:29 | 3 s |
| 建 demo / git init / calc.py | 11:35 – 11:36 | <1 min |
| 运行 1（问完即止，无方案） | 11:36:43 – 11:40:19 | 3 min 36 s |
| 运行 2（出方案） | 11:41:21 – 11:47:30 | 6 min 9 s |
| 检查结果 + 写本报告 | 11:47 – 11:52 | ~5 min |
| **合计** | 11:31 – 11:52 | **~21 min**，其中约 10 min 是 agent 运行时间 |

从「装完」到「仓库里真的有一个 `plan.md`」，我花了 **2 次 agent 会话、约 10 分钟**，对象是一个 6 行、2 个函数的文件。如果我只按 README 的 Quick Start 跑一次就停，我手上会有 `.sopify/sopify.json` 和一个 `.git/info/exclude` 里的块，**但没有方案**——而 README 让我以为会有的。

### 一句总结

概念层（它是什么、什么时候别用、值不值）README 讲得很清楚，我 4 分钟就能复述；操作层（装完之后到底发生什么、会多出哪些文件、什么时候会被门禁拦住、提问会不会结束本轮）README 几乎没讲，我踩的每一个坑都在这一层。
