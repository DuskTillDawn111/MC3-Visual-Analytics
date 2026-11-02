# 暗潮寻踪前端设计研究

## 已确认并实施的方向

用户回复“不错 就这个了”，确认采用本轮推荐的 Attio 排版与控件精度、大幅关系画布、协调蓝色背景。实现与验证已完成，详见 [当前验收记录](FINAL_PROJECT_AUDIT.md)。以下研究条目按各轮发生时的状态保留；石板蓝预览已作废。

## 2026-11-01 再次筛选：以实际产品界面校准方向

用户已否决上一轮石板蓝临时预览。下文的石板蓝提案仅保留为研究记录，后续实现应以新的视觉确认结果为准。本轮只研究参考与技能，应用源码及生产构建保持原样。

上一轮预览保留了密集的顶部控件和相近的区域权重；整体加深之后，布局、中文排版和控件精度的问题仍然明显。后续方案需要同时处理这些问题。

### 新筛选的技能

- [make-interfaces-feel-better](https://github.com/jakubkrehel/make-interfaces-feel-better/blob/main/skills/make-interfaces-feel-better/SKILL.md)：已读取源文件。关注光学对齐、字体与图标重量、数字排版、圆角关系、边框和阴影用途，适合精修现有分析应用。推荐作为具体实现细节的检查依据。
- [better-web-ui / add-ui](https://github.com/aladicf/better-web-ui/blob/main/skills/add-ui/SKILL.md)：已读取源文件。强调候选方案在信息层级、布局密度和交互组织上的实际差异，可借鉴其方案比较方法。当前仅评估，尚未启动该技能要求的完整多方案流程。
- [redesign-existing-projects](https://github.com/elayadesign/redesign-skill/blob/main/skills/redesign-existing-projects/SKILL.md)：已读取源文件。诊断现有界面的思路有价值，其固定字体、配色及装饰预设与本项目的中文数据分析场景匹配度较低。

### 实际查看的产品

| 参考 | 观察与操作 | 本项目可借鉴的细节 |
|---|---|---|
| [Attio Reporting](https://attio.com/platform/reporting) | 浏览报表展示区，关闭 Cookie 提示，点击 “Down to the record” 切换产品演示。 | 深色正文、较轻的边界、紧凑控件和局部蓝色数据焦点。统一组件细节后，再协调蓝色主画布与周边表面。 |
| [Hex Explore 文档](https://learn.hex.tech/docs/share-insights/explore) | 查看官方产品截图，包括数据浏览器、图表类型选择器。 | 将图表类型与字段配置组织为紧凑操作区；切换时提供图形预览。截图为官方文档展示，本轮操作范围为文档页面。 |
| [Cosmograph Country Borders](https://run.cosmograph.app/public/d82da4c7-486b-42c2-b3bb-d9bf45ba02eb) | 实际加载公开网络：249 个节点、642 条边；查看画布、侧栏、图例并滚轮缩放。 | 窄工具栏、大幅关系画布、局部图例。其彩色标签较杂，项目应继续使用统一的节点文字与既有群体语义色。 |

本轮倾向以 Attio 的控件与排版精度组织全站，以 Cosmograph 的空间分配组织主图。蓝色画布、中文标题和真实通信数据共同决定最终效果。先选定用户认可的原站参考，再提交本项目的具体结构方案。

截图保存在 `work/design-references-20261101`：`attio-reporting-clean.png`、`attio-drilldown.png`、`hex-chart-interface.png`、`cosmograph-borders.png`、`cosmograph-zoom.png`。Observable 示例地址返回 404，Cosmograph 官网首屏截图加载效果欠佳，均已排除出设计依据。

---

## 2026-11-01 补充研究：加强视觉层次

用户反馈：全站雾蓝方案整体偏浅，希望提升质感。当前判断是各表面的明度接近、正文和数据焦点的视觉重量不足；下一版应同时调整表面层级、图形对比和文字层级。

本轮通过原作者仓库核对四套技能：

- [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)：已读取源文件。本轮采用其真实内容、明确视觉方向、渲染后评审流程，制作方向预览。
- [Impeccable](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md)：已读取源文件及官网。现行版本区分 Operate、Read 等使用场景，提供 critique、bolder、typeset、polish 等命令，适合作为后续改进工具。仓库现行路径已改变，旧 source/skills/frontend-design 路径返回 404。当前仅完成评估，尚未安装或运行其二进制引擎。
- [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md)：核对其检索流程与适用范围，作为配色、字体与 Vue 实现参考候选。本轮未运行其数据库检索。
- [Taste Skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md)：核对源文件；当前主分支已包含 app-screen 分流，部分搜索索引仍保留较早的页面限定描述。本轮未运行其抽样或检查脚本。

实际打开 Linear 官网并操作 Product 菜单；打开 Impeccable 官网并操作前后对照滑块，保存并查看浏览器截图。参考站点：https://linear.app/、https://impeccable.style/。Linear 的深灰背景与明亮文字形成明显层级；Impeccable 的对照强调删除装饰性重复并重排主次。本项目继续让真实通信网络承担主视觉。

提议方向：石板蓝分析工作台。底色 #1D2C35，侧栏 #243843，面板 #293F4B，主画布 #304C5B，文字 #EDF1F2，选中操作 #8FC3D2，少量重点 #D0AC74。导航、侧栏、画布连续过渡；主图保留大幅展示，压缩重复控件行，让节点和原文获得清晰对比。铜金用于选中重点与既有证据语义，群体继续使用分类色。

基于本机真实页面与数据，通过临时浏览器样式制作并检查两张方向预览：

- [通信关系预览](../work/premium-research-20261101/slate-network-preview.png)
- [证据调查预览](../work/premium-research-20261101/slate-case-preview.png)

预览用于选择视觉方向，应用源码与生产构建保持本轮研究前的版本。当前尚未安装新技能。原站截图与方向预览均保存在 work/premium-research-20261101。

---

研究日期：2026-10-29。目标是明确下一轮前端的视觉方向与交互结构。本文中的布局、字体和颜色为设计提案，当前应用尚未实施。本次使用 Edge 在 1440×1000 下实看网站，保存截图并操作关系节点、键盘推进、信息提示及地图模式切换。

## 当前界面的具体问题

1. **主图过小。** 实测首页时间图为 968×178，顶部介绍高 171，原文栏为 340×947。首屏的大量面积用于标题、阶段按钮、说明和边界，数据图的表达空间不足。
2. **图形传达的信息偏少。** 八个点主要展示消息编号与支持/竞争角色；人物、通信方向、行动变化需要在其他位置寻找。编号适合溯源，人物与行动更适合承担第一层识别。
3. **层级重复。** 大标题、英文眉题、章节编号、阶段序号、卡片标题和消息编号交替出现，阅读路径被切成多个相似的小块。
4. **中文排版缺少统一。** Georgia 英文标题与微软雅黑中文采用不同尺寸和基线，正文与图内文字偏小；英文姓名在视觉上压过调查问题。
5. **原文占比过高。** 初次进入就显示完整侧栏，调查主张、图形关系和证据细读之间缺少逐步展开的节奏。
6. **页面风格断裂。** 调查首页的浅绿编辑排版与原探索工具的蓝灰面板拥有各自的视觉体系，跨页体验需要统一。

当前截图：[current-project.png](../work/design-research-20261029/current-project.png)。以上是视觉与信息结构评审。

## 实看参考

| 参考 | 实际观察与操作 | 本项目可采用的原则 |
|---|---|---|
| [The Pudding：The Real Kevin Bacon](https://pudding.cool/2026/10/kevin-bacon/) | 全幅关系网络与左侧短说明共同构成页面。点击 Zendaya 后路径变亮，中间人物逐步显现；支持键盘推进。 | 以关键主体和原文支撑的通信路径组织主图；选中后仅突出相关节点、边和说明；逐步回答一个问题。 |
| [Blue Corridors：Explore](https://bluecorridors.org/explore/species) | 左侧约四分之一为图层和对象目录，右侧为主画布。实际打开 Info 并切换 Flat (Static)；地图完成加载后可见轨迹和颜色编码。 | 将筛选集中于侧栏，把视觉空间交给数据；对象详情按需出现。MC3 对应主体关系与时间画布，空间布局依据关系或时间。 |
| [Linear](https://linear.app/) | 查看首页和产品演示区。标题实测 64px/64px；导航、正文、展示图具有明确尺寸差。深色界面以少量灰阶、细分隔和稳定对齐组织内容。 | 统一控件、选中态、间距和标题尺度；收起低优先级操作；让调查页与探索工具共享基础视觉规范。 |
| [Stripe](https://stripe.com/) | 本次浏览器显示中文香港版本。大幅文字与彩色图形形成首屏焦点，分区采用连续网格，主操作突出。 | 学习首屏主次及分区节奏。项目的代表图形直接取自通信数据，颜色对应可说明的业务含义。 |
| [The Pudding 首页](https://pudding.cool/) | 每篇作品以自身主图作为入口，标题与摘要围绕图排列。 | 四道分析问题的入口使用各自真实分析图缩略图，让读者先看到差异。 |
| [Awwwards 获奖网站目录](https://www.awwwards.com/websites/) | 实际查看作品缩略图、分类与布局。网页阅读工具超时，Edge 页面成功加载。 | 作为广泛的构图样本库；具体设计判断以打开后的原站及本项目任务为依据。 |

参考截图位于 [work/design-research-20261029](../work/design-research-20261029)。第三方页面截图保留为本地研究记录；生产资源采用自行实现或明确授权素材。

![The Pudding：选中人物后突出关系路径](../work/design-research-20261029/pudding-selected.png)

![Blue Corridors：图层目录、主画布与按需信息](../work/design-research-20261029/blue-info.png)

### 图形与分析逻辑的适配

The Pudding 将共同参演关系组织为网络，并用最短联系距离展开故事；其“中心”有具体的计算定义。本项目需要区分唯一通信数、消息方向、原始关系和推断关系。路径上的每条边应能打开对应通信，界面直接写出正在使用的指标。

Blue Corridors 将不同数据层和物种映射为可独立控制的图层。本项目可将主体、通信、事件和证据角色分层；时间筛选先明确控制对象，再同步统计。已有算法保留原始含义，布局变化服务于证据核查。

## 前端技能筛选

本轮核对了可安装技能目录，并直接读取以下技能源文件。当前完成的是查找和评估；用户级技能目录尚未安装新技能。

| 技能 | 来源与用途 | 本项目选择 |
|---|---|---|
| frontend-design | [Anthropic 源文件](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md)。先形成具体视觉方案和简明设计变量，再以真实内容构建、截图批评。技能目录有 Apache-2.0 [许可证](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/LICENSE.txt)。 | 优先，用来指导主视觉、字体、布局和独特性审查。 |
| web-design-guidelines | [Vercel 源文件](https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/web-design-guidelines/SKILL.md)，要求读取最新[界面规范](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)，覆盖焦点、语义、字体、状态、动效及内容溢出。 | 配合前者进行实现审查。已读规则；本轮未完成全站逐条审计。尝试的许可证路径返回 404，复制分发前继续核实授权。 |
| ui-ux-pro-max | [项目仓库](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)与[技能源文件](https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/.claude/skills/ui-ux-pro-max/SKILL.md)。提供可检索的风格、配色、排版、图表和 Vue 实现建议；仓库为 [MIT](https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/LICENSE)。 | 作为定向查询工具。本项目以图表表达为核心，应提高图形编码的优先级；配色结果需对照中文页面实际审查。 |

推荐工作组合：frontend-design 制定视觉方案，web-design-guidelines 检查落地质量，ui-ux-pro-max 按具体问题补充建议。

## 推荐设计：以通信关系为中心的调查画布

首屏直接呈现 Nadia 与关键联系人、选中阶段中的通信，以及一条可核查的调查问题。读者先观察关系，再选择消息查看行动与原文。

```text
┌ 暗潮寻踪   调查 / 通信 / 群体 / 身份        搜索   导出 ┐
│ 调查问题与阶段   │                                     │
│                 │      人物—通信关系主画布             │
│ 10.05 文件      │      标签优先显示姓名和行动           │
│ 10.08 报酬      │      选中通信时突出相关路径           │
│ 10.12 转移      │                                     │
│ 10.14 批准      │                         原文按需展开 │
├─────────────────┴─────────────────────────────────────┤
│                 14 日时间轨道与当前阶段                 │
└───────────────────────────────────────────────────────┘
```

- **布局**：1366 宽度下侧栏约 248px，主画布占其余空间；原文在选中后展开约 360px，并保持选中对象可见。主图目标高度 460–560px，按视口可用高度调整。四题长分析进入下层阅读区。
- **首屏内容**：以“取消通道后，Nadia 如何继续协调？”等可由原文回答的问题开场。主图呈现真实联系人和通信；选中的消息同时给出日期、行动短语与来源入口。
- **配色提案**：海军蓝 `#082C4A` 用于画布，浅雾白 `#F2F6F8` 用于阅读，深墨 `#162B3B` 用于正文，亮蓝 `#46B7E8` 用于当前选择，琥珀 `#E6A04B` 用于待核查，灰蓝 `#8EA6B7` 用于上下文。具体前景背景组合在样稿中逐项验对比度。
- **字体提案**：以 Source Han Sans SC / Noto Sans SC 作为中文候选，与系统微软雅黑作实屏比较；英文姓名沿用同一无衬线体系，数字使用等宽数字特性。标题 32–40px，正文 15–16px，图标签 13–14px。部署字体先核对许可与体积。
- **图形编码**：人物位置尽量稳定；节点标签为姓名，边表示当前范围通信。消息用实际日期定位。证据角色同时提供文字与形状提示，颜色含义在同一页面保持一致。
- **交互节奏**：切换阶段时突出当期关系；选边出现通信列表；选消息显示原文。180–240ms 过渡只用于说明焦点变化，并提供减少动效模式。原文关闭后保持阶段及对象。
- **内容减法**：统计移入紧凑状态栏；逐条删除重复编号、装饰眉题和同义标题；原文编号保留在溯源位置。界面按钮采用“查看原文”“定位通信”等明确动作。

另一个可行方向是明亮的图文专题：主图铺满内容宽度，短段落逐步展开证据。考虑课程演示还要执行筛选、定位和比较，本轮优先推荐调查画布。

## 实施与视觉验收

先以当前 26 条主体参与通信和八条引用制作可审阅的首屏设计，再接入既有完整交互。按每批最多三个文件拆分：页面结构与样式；图形联动与原文；其他工作区的视觉统一；对应验证与项目文档。

视觉验收分别查看 1366×768 和 1920×1080 的默认、选中、原文展开、空结果与加载失败状态，另检查窄屏的顺序和操作入口。重点判断：第一眼能否找到调查问题与主图，标签是否清晰，关系是否容易追踪，原文展开是否遮挡焦点，工作区之间是否一致。

功能回归覆盖来源消息、日期范围、返回状态及导出内容。视觉评审记录具体截图与发现，真人走查重点询问“你先看到了什么、下一步准备点击哪里、这条线表达什么”。
