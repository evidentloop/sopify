# README（中英文）与 Pages 逐句措辞审计报告（只读）

**审计者**：独立验收官（Antigravity / Gemini 3.8 Flash，Orca worker `task_325c3e72221c` / `ctx_f97836f6389d`）  
**基准版本**：[`cc3e391`](file:///Users/weixin.li/code/github/sopify)（分支 `feat/sopify-narrow-focus`）  
**审计对象**：
- [`README.zh-CN.md`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md)
- [`README.md`](file:///Users/weixin.li/code/github/sopify/README.md)
- [`zh-CN.html`](file:///Users/weixin.li/code/github/sopify/zh-CN.html)
- [`index.html`](file:///Users/weixin.li/code/github/sopify/index.html)

**审计原则与边界**：
依据中文技术写作规范（`zh-tech-writing`），逐句排查：① 先否定再说明句式及重复说明；② 空话与防守性营销腔；③ 中文非必要英文夹杂与翻译腔；④ 中英文语义不一致。
**说明**：用户已决策的改动（徽章去 HOST 标签、Trae 去预览及基线定义调整、正文与首屏删除「不是新编辑器，也不是新 CLI」及「No new editor. No new CLI.」）已按要求排除在下表之外。本报告**宁少勿多，只列确实需要改动的条目**，不改写事实，不新增未定义内容。

---

## 一、`README.zh-CN.md` 措辞审计与建议清单

| 行号 | 类别 | 原句 | 建议改法 | 理由 |
|---|---|---|---|---|
| **L44** | 否定堆叠与同义冗余 | `需要 Python 3.11 或更高版本，安装器会在下载前检查。它只写入宿主指令和 Skill——没有守护进程、没有后台进程、不是新编辑器。` | `需要 Python 3.11 或更高版本，安装器会在下载前检查。它只写入宿主指令和 Skill。` | 破折号后连用三个否定式（「没有……、没有……、不是……」），其中「守护进程」与「后台进程」同义重复，「不是新编辑器」属于用户已要求清理的否定赘述。前半句「只写入宿主指令和 Skill」已有明确限定，删去后半句后表达更自信利落。 |
| **L61** | 专有名词大小写 | `方案和证据都留在 git 里，换到其他受支持的工具时可以接着做下去。` | `方案和证据都留在 Git 里，换到其他受支持的工具时可以接着做下去。` | 专有名词 Git 作为版本控制系统时应首字母大写，与技术写作规范统一（区别于文件路径中的 `.git/`）。 |
| **L84** | 口语化书面化 | `以前：把上下文重新粘一遍，还得担心漏掉关键约束。` | `以前：把上下文重新粘贴一遍，还得担心漏掉关键约束。` | 「粘」过于口头化，技术文档推荐使用规范规范的书面动词「粘贴」。 |
| **L103** | 高频词重复与句式冗余 | `这些请求直接处理，不进入方案流程。只有你用 ~go plan 明确要方案、明确要求接着做未完成的工作，或 ~go 判断这个请求需要方案时，才会开始一个方案。` | `这些请求直接处理，不进入方案流程。只有在你输入 ~go plan、明确要求接续未完成工作，或 ~go 判定需要时，才会建立方案。` | 短短一句话中连续出现 3 次「方案」（「要方案」「需要方案」「开始一个方案」）和 2 次「明确」，显得拖沓；精简后语义完全不变，更加凝练。 |
| **L122** | 中文夹杂英文行话俚语 | `\| [Antigravity](./docs/antigravity-host.md) \| 基线；已在真实会话中 dogfood \| --target antigravity:zh-CN / antigravity:en-US \|` | `\| [Antigravity](./docs/antigravity-host.md) \| 基线；已在真实会话中深度验证 \| --target antigravity:zh-CN / antigravity:en-US \|` | 中文正文应避免直接使用未翻译的英文行业口语俚语（dogfood）；改用「深度验证」更符合中文技术写作规范。 |
| **L129** | 防守性否定句 | `下面是 Sopify 在一次真实 Codex 任务中的运行过程，不是编排好的终端演示。` | `下面是 Sopify 在一次真实 Codex 任务中的运行过程。` | 前半句已正面明确「一次真实 Codex 任务中的运行过程」，后半句「不是编排好的终端演示」属于无需多言的防守性否定，删去后语气更从容客观。 |
| **L139** | 机械直译（翻译腔） | `真实任务是一次可选验证器接入。动效解释 Sopify 如何管理这项工作，归档文件记录实际过程：` | `真实任务是一次可选验证器接入。上方动图展示了 Sopify 如何管理这项工作，归档文件记录实际过程：` | 「动效解释」系英文「The animation explains」的生硬直译，动效本身无法「解释」；改用「上方动图展示了」符合中文自然表达习惯。 |
| **L144** | 英文标题未汉化 | `- [Getting Started](./docs/getting-started.md) — 安装细节、先审查脚本再安装、各宿主安装、更新与卸载、可选的 EvidentLoop 配套` | `- [入门指引](./docs/getting-started.md) — 安装细节、先审查脚本再安装、各宿主安装、更新与卸载、可选的 EvidentLoop 配套` | 该节其他所有链接标题均为纯中文（「Sopify 如何工作」「宿主接入指南」等），唯独此项保留未翻译的英文标题，建议统一为中文。 |
| **L147** | 中英文夹杂与不通顺 | `- [外部仓库 Quickstart](./examples/external-repo-quickstart/README.md) — 在非 Sopify 自身仓库上的分步 demo` | `- [外部仓库快速上手](./examples/external-repo-quickstart/README.md) — 在独立外部仓库上的分步实操演示` | 一行内夹杂「Quickstart」与「demo」两个借词，且「非 Sopify 自身仓库」略显别扭；改为纯中文表达更规范。 |

---

## 二、`README.md` 措辞审计与建议清单

| 行号 | 类别 | 原句 | 建议改法 | 理由 |
|---|---|---|---|---|
| **L44** | 否定堆叠与同义冗余 | `Python 3.11 or newer; the installer checks before downloading. It writes host instructions and Skills only — no daemon, no background process, no new editor.` | `Python 3.11 or newer; the installer checks before downloading. It writes host instructions and Skills only.` | The em-dash clause stacks three negations ("no daemon, no background process, no new editor"). "daemon" and "background process" are synonymous redundancies, and "no new editor" is unnecessary defensive negation. The affirmative statement "It writes host instructions and Skills only" sets the boundary with precision. |
| **L61** | 专有名词大小写 | `The plan and its evidence stay in git, so another supported tool can pick the work back up.` | `The plan and its evidence stay in Git, so another supported tool can pick the work back up.` | Capitalize the proper noun "Git" when referring to the version control system. |
| **L129** | 防守性否定句 | `This archived workflow ran inside Codex; it is not a scripted terminal demo. A complex request became a tracked plan, an audit concern stopped the work for a user decision, and after the user approved a minimal fix the verification evidence was recorded and the plan was archived.` | `This archived workflow ran inside Codex. A complex request became a tracked plan, an audit concern stopped the work for a user decision, and after the user approved a minimal fix the verification evidence was recorded and the plan was archived.` | Deleting "; it is not a scripted terminal demo" removes defensive, argumentative negation. Stating that the workflow ran inside Codex is confident and professional. |

---

## 三、`zh-CN.html` 措辞审计与建议清单

| 行号 | 类别 | 原句 | 建议改法 | 理由 |
|---|---|---|---|---|
| **L207** | 宿主清单缺漏与名称不全 | `<li>支持 Codex、Claude、Qoder、Copilot 与 Cursor</li>` | `<li>支持 Codex、Claude Code、Qoder、Copilot、Cursor、Antigravity 与 Trae</li>` | 1. 遗漏了 Antigravity 与 Trae 两个已支持的宿主，与全站及 README 7 宿主不一致；<br>2. 将 Claude 统一为正式全称 Claude Code。 |
| **L211** | 防守性否定句堆叠 | `<p class="install-trust">安装宿主指令与配套资产；不会增加守护进程、编辑器或后台进程。</p>` | `<p class="install-trust">仅写入宿主指令与配套资产。</p>` | 分号后是典型的防御性否定排比，且「守护进程」与「后台进程」同义重复；正面阐明「仅写入宿主指令与配套资产」干脆有力。 |
| **L237-239** | 防御性否定设问重构 | `<summary>Sopify 是另一个编辑器或 Agent CLI 吗？</summary>`<br>`<p>不是。Sopify 把工作流指令和项目约定安装到你已有的 AI 编程宿主中。</p>` | `<summary>Sopify 如何与我现有的 AI 编程工具协同？</summary>`<br>`<p>Sopify 是一套规则和 Skill，直接安装到你已有的 AI 编程宿主中，无需更换工具或改变习惯。</p>` | 原设问以否定句开头（「是另一个 X 吗？不是。」），属于自我辩解式的防守提问。重构为正面阐述协同方式，传达清晰产品边界的同时转为积极的价值解答。 |
| **L250** | 中文问答夹杂英文行话俚语 | `其中 Antigravity 还已在真实会话中 dogfood，但并非每个场景都已在真实会话中证实。` | `其中 Antigravity 还已在真实开发中深度验证，但并非每个场景都已在真实会话中证实。` | 中文技术问答中混用英文行业俚语「dogfood」不符合规范，替换为「深度验证」更严谨。 |
| **L261** | 页脚翻译腔词组 | `<span>Sopify · 能停车、能恢复、能追溯的 AI 工作。</span>` | `<span>Sopify · 能停车、能恢复、能追溯的 AI 编程工作流。</span>` | 「AI 工作」系「AI work」的生硬直译，含义模糊且不顺畅；改为「AI 编程工作流」更加严谨贴切。 |

---

## 四、`index.html` 措辞审计与建议清单

| 行号 | 类别 | 原句 | 建议改法 | 理由 |
|---|---|---|---|---|
| **L215** | 宿主清单缺漏与名称不全 | `<li>Codex, Claude, Qoder, Copilot, and Cursor targets</li>` | `<li>Codex, Claude Code, Qoder, Copilot, Cursor, Antigravity, and Trae targets</li>` | 补齐 Antigravity 与 Trae 两个已支持的宿主，并将 Claude 统一为 Claude Code，与中英文全站保持一致。 |
| **L219** | 否定从句堆叠 | `<p class="install-trust">Installs host instructions and supporting assets. It adds no daemon, editor, or background process.</p>` | `<p class="install-trust">Installs host instructions and supporting assets directly into your tools.</p>` | 删去冗余的否定句（"adds no daemon, editor, or background process"），以肯定句式呈现更具信心。 |
| **L245-247** | 防御性设问重构 | `<summary>Is Sopify another editor or agent CLI?</summary>`<br>`<p>No. Sopify installs workflow instructions and project conventions into supported AI coding hosts.</p>` | `<summary>How does Sopify work with existing AI coding tools?</summary>`<br>`<p>Sopify installs workflow instructions and project conventions directly into your existing AI coding hosts without changing your setup.</p>` | 将自我辩解式的否定设问（"Is it another...? No."）转为正面的架构协同说明。 |
| **L269** | 页脚名词精准度 | `<span>Sopify · AI work that can stop, resume, and be inspected.</span>` | `<span>Sopify · AI coding workflows that can stop, resume, and be inspected.</span>` | 与中文版对齐，用更精准的 "AI coding workflows" 代替宽泛模糊的 "AI work"。 |

---

## 五、中英文对齐与审计总结

1. **结构与信息镜像完全一致**：四个文件在各章节结构、命令示例、价值场景及配置链接上严格同构，无事实性分歧。
2. **共性改进总结**：
   - **全面剔除防守性否定句式**：包括安装处的后台进程排比、Codex 案例中的「不是演示」否定、FAQ 的「不是编辑器」否定设问；
   - **消除中文夹杂与未汉化遗留**：包括英文行话 `dogfood` 改为「深度验证」、深入阅读中的 `Getting Started` 与 `Quickstart` 汉化；
   - **补齐网页宿主卡片一致性**：网页安装面板的小点完整同步 7 个宿主全称。
