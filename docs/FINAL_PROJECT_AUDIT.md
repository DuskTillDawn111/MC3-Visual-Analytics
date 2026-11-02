# 当前项目实现验收

## 2026-11-01 Attio 参考方向落地

用户确认采用 Attio 参考方向后，分批完成全站界面精修：中性导航与面板、蓝色关系画布、深色正文、轻边框和明确的选中态。顶部将筛选与统计压为两层，统计行整合同步状态；视图入口保持常驻，原文栏与主图标题对齐。调查画布和通信网络共用图形色，主题矩阵与时间热图采用一致的蓝色数量编码。关系图保留大幅展示，类型图例进入可展开详情，悬停数据在画布上浮现。

修改源码：`frontend/src/App.vue`、`style.css`、`theme.ts`、`components/CaseStudyView.vue`、`CaseStudyView.css`、`NetworkView.vue`、`TopicView.vue`。新增回归测试：`frontend/tests/control-sizing.mjs`。生产资源已重新构建到 `frontend/dist`。

本轮采用 [make-interfaces-feel-better](https://github.com/jakubkrehel/make-interfaces-feel-better/blob/main/skills/make-interfaces-feel-better/SKILL.md) 的实现原则，沿用 Vue 与原生 CSS。技能作为本次实现依据读取，用户级技能目录保持原状。

| 检查项 | 实际检查与结果 |
|---|---|
| 排版 | 实看四个工作区、调查原文栏和手机页面；通过浏览器字体接口核对原有中文字形来源。统一深色标题、正文层级和等宽数字，字体栈加入本机可用的 Noto Sans SC 并保留系统回退。 |
| 表面与控件 | 主图、证据栏标题对齐；导航、视图切换和图内切换各有明确选中态；主操作为深色按钮。复选框继承输入框高度的问题已先测试复现，再修复为 14×14px 并验证标签点击。 |
| 动效 | 保留短时颜色过渡，避免添加高频入场动效。现有 reduced-motion 检查通过。未进行浏览器 10% 速度的动画录制。 |
| 图标 | 搜索图标改为 currentColor 的单个 SVG，品牌图标与现有结构沿用；未引入图标库。 |
| 性能 | 类型检查与生产构建通过，浏览器走查未出现页面脚本错误。未开展独立帧率与性能基准测量。 |

验证命令：`npm run build`、`node tests/network-prominence.mjs`、`node tests/visual-design.mjs`、`node tests/case-study.mjs`、`node tests/reliability.mjs`、`node tests/control-sizing.mjs`。五个测试脚本共 16 组检查通过，覆盖大图位置、具名视图入口、原文和键盘访问、调查阶段、离线报告、请求失败重试、快速筛选同步、主题口径和复选框交互。

额外检查 390、768、1024、1366、1920px 五种宽度 × 四个工作区，共 20 个组合，均无页面横向溢出。结果见 `work/attio-implementation-20261101/layout-checks.json`。已实看 `case-reader.png`、`network.png`、`network-1920.png`、`topics.png`、`temporal.png`、`investigation.png`、`patterns-390.png`；截图位于同一目录。

保留大幅蓝色画布和各工作区的现有分析功能；全深色石板蓝、装饰性渐变、重复解释尾注均未采用。后续体验重点：在用户实际浏览器中核对字体回退，并查看长英文实体名称及更多筛选组合下的标签排布。

## 2026-11-01 全站雾蓝配色与视图入口

四个工作区统一为浅蓝灰导航与表面、雾蓝调查画布、墨灰正文和海蓝操作色。style.css 集中定义界面色，theme.ts 集中定义群体、主题、特征及数量图配色；网络、时间、主题、候选、事件、异常、证据阅读与分析抽屉同步应用。数量图采用统一蓝色深浅，群体与主题保持各自的分类编码。主题矩阵使用深色数字以提高数值对比度，导出报告沿用相同配色。

App.vue 在分析区加入常驻“全部视图”及具名视图切换，覆盖通信关系、时间与异常、群体关系、主题比较、化名候选、事件溯源；切换后分析区回到顶部，工作区切换恢复总览。关系图默认保留全宽展示，原有时间与主题视图仍可滚动访问。

修改文件：frontend/src/style.css、theme.ts、store.ts、App.vue、report.ts；components/CaseStudyView.vue、CaseStudyView.css、NetworkView.vue、TemporalView.vue、TopicView.vue、AliasView.vue、EventView.vue、AnomalyView.vue、EvidencePanel.vue、FindingsPanel.vue；tests/network-prominence.mjs 与 e2e.mjs；AGENTS.md。docs/case-study-report.html 由调查报告验证重新导出。

验证：类型检查与生产构建通过；network-prominence、case-study、visual-design 共九组浏览器检查通过，覆盖大图尺寸、键盘操作、具名视图切换、四阶段与八条原文、报告内容、窄屏及减少动画偏好。额外验证 390、768、1024、1366、1920 像素宽度下四工作区的页面溢出，以及时间筛选、证据列表、关系图查证和筛选报告记录数一致。浏览器运行过程未记录脚本异常。

实看四工作区及时间、主题详情截图，并检查 1920 像素邻域大图和 390 像素页面。截图与筛选报告位于 work/theme-20261101；本机 8000 服务已使用最新生产构建。此次视觉检查覆盖布局、文字对比和配色一致性，真实用户对新配色的体验反馈留待后续收集。

## 2026-10-30 分析正文与报告文案

重写 backend/app/findings.py 中四题标题、结论、分析依据与八条原文解读，围绕数量变化、任务回应、候选排序及 Nadia 的协调通信组织叙述。请求、建议和自述沿用原文语气。CaseStudyView.vue、App.vue、FindingsPanel.vue 删除重复核查提醒与来源页脚；report.ts 同步正文并删除自动免责声明，离线示例 case-study-report.html 已重新导出。AGENTS.md 记录源头文案检查规则。

验证：构建通过；test_findings.py 两项核对统计、引用和原文一致性；findings.mjs 与 case-study.mjs 共五组浏览器检查通过，覆盖四题恢复、八条原文及报告正文一致性。额外检查四题分析与原文解读中的残留防御性措辞，并实看页面，截图位于 work/narrative-20261030。运行服务已加载 review-2026-10-30 分析版本。

## 2026-10-30 雾蓝画布与通信关系主视图

调查画布采用低饱和雾蓝 #DDE9F3，时间轨道采用协调浅蓝；节点、文字、实线与虚线同步适配，HTML 导出的 SVG 使用相同配色。通信模式与群体探索将关系图置于首位，占满分析区域宽度，时间和主题分析顺序排列在后。1920×1080 下关系画布为 1472×680；1366×768 下为 988×400。

主体筛选后的子图保留节点相对位置，视图自动居中缩放。先以 network-prominence.mjs 复现子图偏右的问题，再修复并通过检查。新增检查覆盖两种桌面宽度的主图位置、宽高、子图居中、空间利用及键盘查证。

修改实现：frontend/src/components/CaseStudyView.vue、CaseStudyView.css、NetworkView.vue、frontend/src/App.vue、style.css；新增 frontend/tests/network-prominence.mjs；AGENTS.md 记录用户的配色与大图优先要求。

验证：类型检查与生产构建通过；case-study 4 组、visual-design 4 组、redesign 9 组、network-prominence 1 组，共 18 组浏览器检查通过。实际检查雾蓝调查页、全局与邻域关系图及窄屏页面，最终截图位于 work/mist-blue-20261030。本次更新为本机源码与生产构建。

## 2026-10-30 标题区与辅助说明整理

标题区删除阶段副标题、装饰性标签、重复操作提示和解释性小字。原文时间、参与者与来源收纳到“通信信息与来源”；时间图、事件图及网络图的解释集中到可展开详情。主题图以直接标题呈现，候选特征值与加权贡献改为三列表格。项目规则同步记录标题下方的排版要求。

修改实现：frontend/src/App.vue；components 下的 CaseStudyView.vue、CaseStudyView.css、TopicView.vue、AliasView.vue、TemporalView.vue、EventView.vue、FindingsPanel.vue、AnomalyView.vue、NetworkView.vue、EvidencePanel.vue。case-study、visual-design、user-feedback 的测试步骤同步采用实际展开操作。

验证：类型检查与生产构建通过；case-study 4 组、visual-design 4 组、user-feedback 3 组、analysis-tasks 5 组、topic-scope 7 组、investigation 4 组，共 27 组浏览器检查通过。实看主调查、通信模式、主题、身份、事件和 390px 窄屏原文阅读；截图位于 work/title-cleanup-20261030。本次更新为本机源码与生产构建。

## 2026-10-30 页面叙述清理

按 anti-defensive-writing 原则精简卡片叙述：移除重复的防御性提醒和正文尾注；原文来源归入标题信息，图形编码及主题计算口径集中到可展开的详情，身份比较正文直接呈现样本、特征和反证。主题模型、原始证据与导出数据沿用现有实现。

修改文件：frontend/src/App.vue；components 下的 CaseStudyView.vue、CaseStudyView.css、NetworkView.vue、TopicView.vue、EventView.vue、AliasView.vue、FindingsPanel.vue；frontend/tests/analysis-tasks.mjs 更新为先展开模型详情再检查其内容。

验证：vue-tsc 与 Vite 构建通过；case-study 4 组、visual-design 4 组、analysis-tasks 5 组、topic-scope 7 组、investigation 4 组、findings 1 组，共 25 组浏览器检查通过。实际查看原文阅读、主题与身份比较页面，截图位于 work/copy-cleanup-20261030。本次成果为本机源码与生产构建，2026-10-29 ZIP 对应下方历史版本。

## 2026-10-29 关系画布与视觉改进

首页采用深海蓝关系画布、日期阶段侧栏、全期通信轨道及按需原文阅读器。八条引用按原始消息方向连接，交叉引用 Mako—Sentinel 单独呈现；主体位置保持稳定，阶段切换突出对应材料。探索工作区共享导航、控件、间距与阅读背景。四题结论、原始资料及算法口径保留。

修改实现：frontend/src/components/CaseStudyView.vue、CaseStudyView.css、frontend/src/App.vue、style.css、report.ts；新增 frontend/tests/visual-design.mjs。当前主图在 1366×768 下约 400px 高。图形标签与原文展开后的布局、小屏四条引用可见性及导出图例均先复现问题，再修正并复验。

验证：vue-tsc 和 Vite 生产构建通过；13 个浏览器脚本共 70 组通过，其中既有 66 组、新增视觉交互 4 组。新增检查覆盖原始发送方向、标签分离、阅读器焦点与 Esc 返回、26 条通信统计、八条离线引用、图例语义、390px 窄屏及减少动效。后端应用与模型本轮未修改，既有后端 38 项结果保留在上一版本记录。

视觉复查：1366×768 与 1920×1080 的首页、原文展开、阶段切换、四题分析，以及三个探索工作区；另检查 390×844 窄屏。实际截图见 screenshots/visual-design，离线报告为 case-study-report.html，日志位于 work/visual-redesign-20261029。当前运行包为 releases/MC3-Visual-Analytics-20261029.zip，文件与构建校验见 release-verification-20261029.json。

后续重点：真人复测对箭头、证据角色、26/8 两种范围与原文展开的理解；窄屏关系图采用局部横向浏览。视觉质量由实际页面和用户反馈继续评审。前一版本记录的单次报告下载超时在本轮完整回归中未出现。

## 2026-10-28 证据调查版本

当前首页为 Nadia 核心调查，采用四阶段、双侧证据、固定原文阅读器与调查结论的布局。八条引用可由阶段、节点、卡片及键盘进入；支持/竞争解释视角、待补证据状态、原始关系检查与返回后的阅读状态均已实现。调查档案可导出 HTML/JSON，四题分析过程已写入页面及独立文档 ANALYSIS_STORY.md。

当前验证：后端 38 项通过；前端类型检查与生产构建通过；12 个浏览器脚本共 66 组通过，其中 case-study 新增 4 组。实际复查 1366×768 与 1920×1080 的首页、双侧比较及四题分析。修复了一项返回调查页后阶段与所选原文重置的问题，新增失败复现后验证通过。既有工具测试先显式进入通信工作区，继续验证原交互行为。

交付核验完成于 2026-10-29：独立解包服务同样通过后端 38 项与浏览器 66 组检查；79 个运行、源码、测试、配置及数据文件逐项核对哈希。复用本机依赖，浏览器脚本指向独立服务执行。连续脚本中曾出现一次 HTML 下载超时，手动复查、单独运行及随后三次重复检查均通过；原因尚未复现，列入后续观察。

修改文件：backend/app/findings.py、backend/tests/test_findings.py；frontend/src/components/CaseStudyView.vue、FindingsPanel.vue、App.vue、report.ts、style.css；新增 case-study.mjs 并调整六个既有测试的首页入口。原始数据、算法权重、依赖锁文件保持原版本。源码、构建及项目文档打包为 releases/MC3-Visual-Analytics-20261028.zip，独立目录验证结果见 release-verification-20261028.json。

可能的使用风险与复测重点：阶段等距排列的理解、证据角色与事件类型的区别、跨主体引用的解释、从原始关系返回后的上下文、改变阅读视角后档案仍保留全部八条引用。自动检查已覆盖来源、状态与导出；新版核心场景待真人实际复测。课程 PPT 与个人总结仍按既有范围安排。

## 2026-10-26 真人反馈改进验收

三项反馈已落实：单日计数标明“全天背景”与当前小时高亮条数；候选表头改为“相似分”，摘要说明加权得分与原分 × 100；恢复状态及 HTML 区分图表范围与引用附录，报告列出直接通信和跨主体引用数量，JSON 增加 chart_filters。

当前验证：vue-tsc 与 Vite 构建通过；user-feedback 3、findings 1、investigation-quality 3、reliability 6、e2e 20，共 33 组浏览器回归通过。1366×768、1920×1080 布局及实际导出报告完成视觉核对，页面无横向溢出。测试日志和截图位于 work/feedback-review-20261026。Nadia 报告显示图表 26 条、附录 8 条（7 条直接通信、1 条跨主体引用 575）。

修改实现：frontend/src/components/TemporalView.vue、AliasView.vue、frontend/src/App.vue、report.ts；针对性测试为 frontend/tests/user-feedback.mjs，生产 dist 已更新。后端、依赖及数据保持原版本。潜在交互风险集中于切换小时后说明同步、小屏文字换行、无主体/空范围导出及跨主体引用计数，当前相关回归通过。真人复测待反馈，重点任务见 USER_WALKTHROUGH.md。

本机 http://127.0.0.1:8000/ 已提供当前版本。下述 2026-10-23 运行包与机器验收记录保留为历史交付快照；本次更新交付在工作区源码与生产构建中。

## 2026-10-23 验收快照

日期：2026-10-23。范围为系统实现、分析支撑、项目文档与运行交付；课程 PPT、个人总结和课程提交包不在本次范围。本文替代旧文档中的当前状态声明。

## 本轮完成内容

| 原问题 | 当前实现与验证依据 |
|---|---|
| 刷新失败仍显示同步、报告混用范围 | 失败显示未同步，暂停旧图交互；全局与可见子模块加载完成才能导出；快速切换、延迟及部分失败有回归 |
| 唯一通信数和加权度混用、自环不可见 | 列表、详情和图统一唯一通信数；发送/接收/自环分列；自环弧线支持鼠标或键盘回查 |
| 主题比较受规模影响，8 色重复，仅检查典型样本 | 增加群内占比及分母、8 种独立颜色、边界与固定种子抽样；复核 24 条原文并导出抽样方式与因子权重 |
| 候选证据与特征联系不清、敏感性不在界面 | 联系人/小时/上下文/共享词均附两侧来源；可查看特征移除、同文去重和逐日留出排序；自定义分段可导出 |
| 小屏重点不突出、事件图横向溢出 | 候选摘要前置、默认前三名、提高关键文字对比度、事件泳道适配面板并优先选中主体；人工记录刷新后保持展开 |
| 四题分析仅在文档 | 新增四题分析卡片、竞争解释、证据缺口及 Nadia 四阶段时间线；点击恢复调查条件，JSON/HTML 保留论证与原始消息 |

默认权重和 NMF v3 未为追求预设身份答案而调整。官方原文、端点、异常年份、自环和相同正文记录保留。

## 已执行验证

| 检查 | 结果及范围 |
|---|---|
| Windows / Python 3.11 后端 | 37 passed；1 条 Starlette/httpx 上游弃用提示，无失败 |
| WSL2 / Python 3.12 后端 | 当前源码 37 passed；复用 /tmp/mc3-audit-20261021/venv。最初 work/wsl-venv 缺少 pytest，改用已有依赖环境后通过 |
| Windows 前端 | vue-tsc 与 Vite 生产构建通过；依赖锁文件未修改。当前版本未重跑 WSL 原生前端构建 |
| Edge 生产页面 | 十个脚本共 59 组通过：e2e 20、redesign 9、topic-scope 7、investigation 4、workbench 3、analysis-tasks 5、reliability 6、investigation-quality 3、findings 1、topic-sampling 1 |
| 视觉复查 | 三工作区在 1366×768、1920×1080 加载完成后截图复查，无页面横向溢出；截图见 screenshots/improvements |
| 主题复核 | 原 v3 的 63 组扰动仍适用；新增六主题各 2 条边界、2 条固定种子样本，共 24 条 AI 辅助原文复核，不是独立人工标注准确率 |
| 独立目录运行包 | work/release-check-20261023 的 ROOT、584 条通信及源哈希已核验；后端 37 项及同一批 59 组浏览器检查全部通过；记录见 release-verification.json |
| Windows 后台启停 | 无可见窗口、重复启动幂等、停止、重启、生产页面与官方数据均通过 |
| 真实用户走查 | 已收到一份覆盖五项任务的答卷，用户明确确认真人填写，Codex 署名不作为排除依据；原文及处理表见 USER_WALKTHROUGH.md。用时、帮助次数与独立完成条件未记录，不计算总体成功率或效率；反馈改进及复测待完成 |

浏览器曾发现两项问题：旧缩放测试在同步保护期间发送滚轮，已改为等待可交互状态；候选刷新收起人工记录区，先新增失败测试，再保存展开状态并复验通过。

## 结论与边界

- 四题论证见 CURRENT_ANALYSIS.md，界面卡片由 backend/app/findings.py 提供，保留来源和竞争解释。468/584 条通信集中于 08:00–11:59；四群体内部 464 条、跨群 120 条，不证明组织身份或因果。
- 默认六主题移除四条重复正文后，236/584 条最大因子归属变化，主题编号不是稳定类别。抽样让不确定性可检查，不会消除它。
- Boss 默认 Nadia 与 Elise 接近，移除文本首名改变。接收语境、转述及共同任务影响相似性；得分不是概率，分时变化不确认共享操作者。
- Nadia 原文支持隐瞒、协调、设备及许可活动的调查线索；指令与执行、许可自述与独立核验仍有缺口，不确认具体违法或持续非法捕鱼。
- 密集网络仍需邻域/矩阵/放大；已收真人答卷指出范围层级、/100 得分及附录组成的理解负担。应改进后复测，不能把自动测试或一份答卷当作全部用户的易用性证明。
- 无经纬度、身份真值或独立现场观察；推断关系与来源原文不是独立的两份证据。
- 本机循环测量中候选接口约 1.6 秒，敏感性按需执行；不是并发负载测试或生产 SLA。

## 数据与运行包

唯一事实输入 data/raw/MC3_release.zip，SHA-256：`ca62ea3d0605b05b57b2a9b6c824da67d6ab47e3e714069bfd69f0963380c9d6`。原图 1,159 节点、3,226 边、584 条通信；投影 41 主体、217 个有向联系。保留 32 个缺失事件时间、81 条无 evidence_for 通信、31 条自环及 4 对相同正文。

运行源码包：releases/MC3-Visual-Analytics-20261023.zip，附同名 .zip.sha256。包括源码、测试、锁文件、官方数据、处理表、生产前端、脚本和文档；排除虚拟环境、node_modules、缓存、work、releases 自身。入口为 start.ps1/stop.ps1。

独立验证复用本机 Python 依赖和 Edge/Playwright，浏览器测试从开发目录请求解包后的 8002 服务，不代表全新电脑联网安装验证。最后仅同步文档并重新封装；运行源码、测试、配置、数据与构建产物须逐文件哈希匹配已验证副本。机器记录见 [release-verification.json](release-verification.json)。

问卷接收后的更新仅涉及项目规则与评审文档，未改应用代码、测试结果或已交付 ZIP；现有 ZIP 保留封装时的走查状态，当前反馈状态以工作区本页及 USER_WALKTHROUGH.md 为准。

## 修改文件与后续复测

后端：app/graph.py、main.py、aliases.py、findings.py，及 tests/test_graph.py、test_aliases.py、test_findings.py。前端：App.vue、api.ts、store.ts、report.ts、style.css，NetworkView、TopicView、AliasView、EventView、TemporalView、FindingsPanel；测试 e2e、investigation、reliability、investigation-quality、findings、topic-sampling。抽样：scripts/sample_topic_evidence.py。README、API、设计依据、当前分析、抽样复核、走查表、机器快照与 dist 同步更新。

后续真实反馈优先复测：不同群体的数量/占比理解、身份分数误解、两侧原文追踪、指令与完成区分、分析卡片与消息附录范围。记录匿名卡点、处理和复测，不能把待执行项目记为通过。
