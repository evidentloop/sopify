# T10 配图交付报告（待 Qoder 验收）

已按原路径覆盖指定 5 个图片文件：2 张中英文跨宿主 JPG、1 张架构 SVG、2 张中英文产品形态 SVG。没有 commit、push、改封面或改仓库文本文件；README、Pages、how-sopify-works 和检查器的并行文本改动保持原状。本轮基线为 `feat/sopify-narrow-focus@1ae94c291e6da9ddcea31b07c0fd865957dde315`。

本报告及预览/原图备份/校验日志均在 scratchpad，未加入仓库。作者自查已完成，**独立 Qoder 图文验收尚未进行，五图均待其验收**。

## 图片与预览路径

| 图片原路径（已覆盖） | 尺寸 | 大小：原 → 新 | 预览 |
|---|---|---|---|
| [中文跨宿主场景](/Users/weixin.li/code/github/sopify/assets/readme-visuals/sopify-scene-cross-host.jpg)<br>`assets/readme-visuals/sopify-scene-cross-host.jpg` | 1440 × 810 | 294420 → 206819 bytes | [预览](/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/visuals-evidence/final/sopify-scene-cross-host.jpg) |
| [English cross-host](/Users/weixin.li/code/github/sopify/assets/readme-visuals/sopify-scene-cross-host-en.jpg)<br>`assets/readme-visuals/sopify-scene-cross-host-en.jpg` | 1440 × 810 | 281544 → 212812 bytes | [预览](/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/visuals-evidence/final/sopify-scene-cross-host-en.jpg) |
| [架构图](/Users/weixin.li/code/github/sopify/assets/sopify-architecture.svg)<br>`assets/sopify-architecture.svg` | 960 × 600 | 11516 → 11924 bytes | [预览](/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/visuals-evidence/final/sopify-architecture.png) |
| [中文产品形态](/Users/weixin.li/code/github/sopify/assets/sopify-product-form-release.svg)<br>`assets/sopify-product-form-release.svg` | 1400 × 640 | 20164 → 21717 bytes | [预览](/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/visuals-evidence/final/sopify-product-form-release.png) |
| [English product form](/Users/weixin.li/code/github/sopify/assets/sopify-product-form-release-en.svg)<br>`assets/sopify-product-form-release-en.svg` | 1500 × 640 | 20075 → 21629 bytes | [预览](/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/visuals-evidence/final/sopify-product-form-release-en.png) |

中英文场景对照：[contact sheet](./visuals-evidence/cross-host-contact-sheet.jpg)。SVG 预览为 1920px 宽 PNG，源 SVG 的 viewBox 与 width/height 保持原值。完整文件大小、预览路径及 SHA-256 见 [final-manifest.json](./visuals-evidence/final-manifest.json)。

## 跨宿主场景：doc-to-sketch

采用 **Path A：原生 image_gen 图像生成**，使用现有 cross-host 图、未修改的 Sopify cover 及 skill 的 style anchor 作参考。沿用暖白纸面、细钢笔/铅笔线稿、淡蓝/鼠尾草绿/浅紫、角落细构图标记；不重画封面。

依据 `.sopify/plan/20261020_sopify_narrow_focus/audits/w4/t9-qoder-transcript-summary.md` 与 `t9-accept-gemini.md`：Claude Code 是方案作者，Qoder 是新会话执行者，唯一用户输入是裸 `~go`，之后从项目文件接续 T6b。画面不再使用旧 Codex/JWT 示例、钟表和昼夜隐喻，也不声称共享云端聊天或自动完成全部受管协议。

- 左：`Claude Code`，屏幕 `~go plan ...`。
- 中：`.sopify/` 文件夹与“同一仓库 / Same repository”，两段细箭头表示文件记录的保存与消费。
- 右：`Qoder`，屏幕仅 `~go`，标注“接着完成 / Continue the work”。
- 中文标题：**换个工具，接着做**。
- 英文标题：**Pick up where any tool left off**，采用任务给定建议。
- 未使用 `Seamless`、`无缝`。删除了可能误指旧 Codex 示例的立方体图标，避免品牌标识混淆。

最终两张图的全部 8 项可见文字分别核对，拼写与中文准确；没有额外伪代码、乱码或多余副标题。本次不需要文字后处理覆盖。精确文本清单在 [required-text.json](./visuals-evidence/required-text.json)，共用风格锁在 [style-lock.txt](./visuals-evidence/style-lock.txt)。

原生尺寸为 1672×941；按本任务明确要求的 JPG 原路径，做高质量裁切/缩放及 JPEG 编码，最终两张均 **1440×810，精确 16:9**。原图为 1440×816，新文件约 202KB / 208KB，原文件约 288KB / 275KB，保持同一量级并低于 web 500KB 门槛。原生 PNG 保留在 `visuals-evidence/*-native.png`，没有删除生成器原始输出；没有用脚本代替主视觉生成。

## 技术图：fireworks-tech-graph

先读取三张现有 SVG 的根属性：它们均没有 `data-style-id`、`data-visual-theme`。依现有白底、灰边、蓝色主流程与绿色资产的 CSS 选择对应 **Style 1 / Flat Icon**；不伪造原本不存在的 style 元数据，不切换主题。三张 SVG 根尺寸与原有 `<style>` 样式表逐字保持一致；HOST 小卡片局部调整字号与高度以容纳新增宿主，色板和图形语言不变。

仅更新：

1. 宿主清单增加 Antigravity 和 Trae；Trae 在中文图标“预览”、英文图标“preview”，架构图为 `Trae · preview`；既有认证/基线颜色含义保持原样。
2. 产品形态中的“五宿主”改为七宿主并明确包含预览；在原 HOST 栏内重新排布宿主小卡，不改变五个主阶段和箭头。
3. 架构副标题和两张产品形态图的主标语与当前 README 标语一致，强调方案与验收证据在仓库、跨工具/人/agent 接续。

架构的 Host / Protocol / Workflow / Knowledge 层、产品形态的 Host → Skill → Assets → Handoff → Archive 主体结构、主要组件与业务箭头都保留。SVG 使用 skill 要求的 Python list 方法逐行生成，不改源码、schema 或仓库文档。

原架构图在更新前即有三条工作流内箭头被误判为穿过“大背景组件”，因为工作流区域是实色 rect。给该既有区域补了一个 `data-graph-role="container"`，使其正确表示区域容器，未移动或伪装业务箭头；该元数据不改变视觉。此前失败日志保存在 `before-sopify-architecture-validation.log`。

## 校验与视觉检查

三图均使用 skill 原有入口：

```text
/Users/weixin.li/.codex/skills/fireworks-tech-graph/scripts/generate-diagram.sh \
  -t architecture -s 1 -o <scratchpad 中的实际 SVG> -w 1920
```

自动检查均通过：XML、marker 引用、箭头碰撞、semantic geometry、composition quality、渲染；具体日志：

- [架构校验](./visuals-evidence/sopify-architecture-validation.log)
- [中文产品形态校验](./visuals-evidence/sopify-product-form-release-validation.log)
- [英文产品形态校验](./visuals-evidence/sopify-product-form-release-en-validation.log)

CairoSVG 自动渲染能完成，但本机 PNG 会丢部分 CJK/箭头字形；按 skill 的 PNG export 指引，用现有 `rsvg-convert` 重新输出预览，已逐张打开检查：中文不再缺字，宿主卡片、Trae 预览、标题、流程箭头及标语无新增重叠或裁切。SVG 本身仍保留可读文本，不转轮廓、不嵌入外部资源。作者 `visual_review: passed`，这只表示内部自查，不能代替 Qoder 验收。

自查还确认：

- 两张 JPG 精确 16:9，三张 SVG 尺寸完全不变；五个文件大小均为原值的 0.5–2 倍以内。
- 双语手绘构图、纸色和线条一致，contact sheet 已检查。
- 五个目标文件与已校验的 staged 文件逐字节相同；同一份摘要记录可供验收者核对。
- `git diff --check -- assets` 通过；两张现有 cover 无 diff。
- 仓库只覆盖任务列出的五个图片路径；其他文本 dirty 来自并行工作，没有复制、回退或覆盖。

## 交给 Qoder 的验收要点

请逐张打开上述预览并核对：T9 的 Claude Code → `.sopify/` → 新 Qoder 会话含义、右侧只有 `~go`、标题没有 Seamless/无缝、所有中英文文字、Trae 预览标签、与当前 README/Pages 的事实与样式是否一致。若需反馈，请按原图片路径指出具体位置；当前没有将这些图自行标记为最终 accepted。

## 本轮变化

依据 Qoder 的图片验收意见，仅覆盖两张产品形态 SVG：

- 中英文宿主卡均将 `Claude` 改为 `Claude Code`，与架构图名称一致。
- 中文宿主状态统一为“已验证 / 基线 / 预览”，对应图例改为“协议已验证 / 基线支持”。
- 原根属性、尺寸、样式表与所有 `style` 属性逐项比对均不变；中文 Claude Code 标签仅增加水平适配 transform，使长名称留在原卡片内，未改卡片布局。

两图均通过 fireworks `validate-svg.sh` 的 XML、marker、碰撞、语义几何、构图与渲染检查，并用 `rsvg-convert` 导出 1920px 预览逐张打开确认，文字完整、无新增裁切或重叠。`git diff --check` 通过；未 commit、未 push、未修改 README，工作区并行出现的 README 改动未触碰。

| 文件 | SHA-256 | 体积 | 校验与预览 |
|---|---|---:|---|
| `assets/sopify-product-form-release.svg` | `9dda9e127f43a5d07a95944d3a9dce0c7110e3e6b7e3e9091728b5504d4a6d9f` | 21717 → 21748 bytes | [校验](./visuals-rework-evidence/sopify-product-form-release-validation.log) · [预览](./visuals-rework-evidence/sopify-product-form-release.png) |
| `assets/sopify-product-form-release-en.svg` | `f9faa3cbc049529d3b94958057e665a13e710827ad2b095f363c8296b8991e5a` | 21629 → 21634 bytes | [校验](./visuals-rework-evidence/sopify-product-form-release-en-validation.log) · [预览](./visuals-rework-evidence/sopify-product-form-release-en.png) |

修改前快照、当前文件副本及摘要见 [manifest.json](./visuals-rework-evidence/manifest.json)；本轮为执行者校验与视觉自查，后续独立验收由协调者安排。
