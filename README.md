# 暗潮寻踪

基于 IEEE VAST Challenge 2025 MC3 官方记录的本地可视分析工作台，面向《可视化技术》课程展示。数据为官方合成竞赛数据；应用使用实际原始记录，不使用模拟页面数据。故事时间为 2040 年。

## 在本机使用

当前入口（2026-10-29）为“证据调查”：左侧选择 Nadia 的四个调查阶段，中央关系画布呈现八条引用的原始消息方向，点击行动标签展开原文；底部时间轨道显示全期 26 条主体参与通信。支持键盘核查、阅读状态保留与 HTML/JSON 调查档案导出。顶部可进入通信、群体和身份工具。四题完整结果见 [ANALYSIS_STORY.md](docs/ANALYSIS_STORY.md)，当前视觉与交互验收见 [FINAL_PROJECT_AUDIT.md](docs/FINAL_PROJECT_AUDIT.md)。

项目工作区：`D:\MC3-Visual-Analytics`。已创建 Python 3.11 虚拟环境、安装依赖并构建前端。

在 **Windows PowerShell 7** 中运行：

```powershell
Set-Location 'D:\MC3-Visual-Analytics'
pwsh -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -OpenBrowser
```

浏览器访问 **http://127.0.0.1:8000/**。同端口提供网页与 API，无需同时启动 Vite。服务在后台运行，不会反复弹出控制台。

停止服务：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1
```

换电脑或首次从源码部署，先运行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

需要 Python 3.11、Node.js 及 npm；已验证环境为 Python 3.11、Node.js 24.13.1、npm 11.8.0。Python 精确版本锁定在 `backend/requirements.lock.txt`，前端锁定在 `frontend/package-lock.json`。准备脚本创建项目独立环境、安装锁定依赖、重建数据、构建前端并运行后端测试。已有环境无需重复安装。

## 已实现功能

| 阶段 | 可使用的功能 |
| --- | --- |
| Phase 0 | 原始 ZIP 校验、数据字典、质量报告、真实总览、健康检查 |
| Phase 1 | 14×24 通信热力图、逐日趋势、有向通信投影、社区与中心性、日期/小时/主体/文本联动、图节点和边到原文 |
| Phase 2 | 时序异常特征与基线、原始消息 ID、主体事件链、事件类型过滤、独立日期来源、缺失时间与观察期外事件、原始异构图检查 |
| Phase 3 | 可调权重候选排名、特征贡献与样本量、支持/反证 ID、一对多探索、人工不确定标记、JSON 导出、课程发现与演示脚本 |

## 当前项目版本（2026-10-23）

- 刷新失败明确标为未同步，旧视图暂停交互；全局及当前工作区模块未就绪时禁止导出，报告使用同一范围快照。
- 网络节点按唯一通信数计数，自环可见并可回查；加权度与发送、接收、自环分别标注。
- 群体主题可切换绝对量和群内占比，8 主题颜色独立；增加边界样本和固定种子抽样，新增 24 条原文复核。
- 候选比较提供两侧特征证据、特征移除/去重/逐日留出敏感性及可调分段；默认展示前三名，结论与局限前置。
- “分析发现”提供四题论证、竞争解释、证据缺口及 Nadia 时间线，可恢复调查条件并随 JSON/HTML 导出。

- 浅色任务工作台：通信模式、群体与主题、身份与事件调查；统计缩为一行，原文证据固定在右侧。
- 保留完整 14×24 时间概览，增加单日主体通信泳道；支持撤销筛选。
- 通信网络按当前社区进行有界力布局并缓存位置，支持有向矩阵、邻域、按需标签、内部/跨群计数和消息高亮；桌面双图并排，可单图放大。
- 固定官方语料的 TF-IDF + NMF 主题模型，支持 4/6/8 主题比较、群体—主题矩阵、时间分布和原文样本；当前 v3 排除英语缩写碎片，已完成 63 组扰动评估与 18 条代表原文复核，大屏放大视图支持矩阵与样本并排。
- 人物/船舶同类候选、人员—船舶原始角色、前后时段画像；不把操作者等同船舶身份。事件概览覆盖当前筛选内全部事件，列表分页不改变时间轴。
- 原文阅读器提示自环、同文节点、可能的发送角色冲突和计划时间风险；可回查相同双方附近 24 小时的通信。群体主题的计数、样本及导出保持同一范围。
- 当前验证范围与结果以 `docs/FINAL_PROJECT_AUDIT.md` 为准；`VALIDATION.md`、`COMPLETION_AUDIT.md` 和 `REDESIGN_VALIDATION.md` 属于历史快照。

本轮范围为系统实现、分析支撑及运行交付；按用户要求，暂不制作课程 PPT、个人总结或课程提交包。当前四题分析与机器快照见 `docs/CURRENT_ANALYSIS.md/json`；主题质量见 `docs/TOPIC_QUALITY_REVIEW.md/json`。`docs/MC3_ANALYSIS_DRAFT.md` 及 `MC3_ANALYSIS_EVIDENCE.json` 保留第二阶段旧模型快照，开放身份问题仍保留不确定结论。

当前运行源码包：`releases/MC3-Visual-Analytics-20261029.zip`，校验值见同名 `.sha256` 文件。当前浏览器验证与运行文件哈希见 `docs/release-verification-20261029.json`；本轮验证环境为已有依赖的 Windows 工作区。包内排除虚拟环境与 node_modules，首次使用按上方 setup.ps1 准备依赖。

## 两分钟上手

1. 点击通信热力图色块，或“密集时段”按钮，观察总览、网络及消息同步变化。
2. 点击图中节点查看主体；点击连接检查构成消息。图支持滚轮缩放、节点拖动、画布拖动、邻域和社区过滤。
3. 重置后，点击异常提示查看基线、特征贡献和原始通信，再从消息进入其支撑事件/关系。
4. 切到“群体与主题”，在关系图和有向邻接矩阵间切换；点击主题矩阵色块或代表消息，检查原文与群体联系。
5. 切到“身份与事件调查”，点击“调查 Nadia Conti”，检查主体—事件泳道与支撑通信，不预设违法结论。
6. 在候选视图选择“人物”或“船舶”，比较 Boss / The Lookout / Mako 等对象；展开“分时段对照”和“人员—船舶角色”，回查原文。分数不是身份概率，角色不是身份相等。
7. 顶部“导出证据”保存当前筛选的完整消息及所选节点证据；“导出报告”生成自包含 HTML，内嵌当前工作区可见的 SVG 图表、完整英文消息、质量说明和来源哈希，离线可打开并打印为 PDF。消息页、事件页与候选比较另有独立导出；示例见 `docs/sample-report.html`。

点击邻域内的连接时，消息阅读器显示该连接的消息，临时独立于主体筛选；日期、小时及检索仍生效。节点证据详情始终返回完整原始连接，可能包含筛选窗口外的支撑消息。

化名比较继承日期、小时和检索范围，为保证比较两方，独立于上方主体过滤。默认候选集按称呼形式区分，仅是探索入口。船舶默认只比较船舶；跨类型请求使用角色关系查询。分时段画像默认比较观察范围前后两半，也可指定分界日，不自动识别共享操作者。人工标记仅保存在当前浏览器，可导出 JSON；不写回原始数据。

## 测试与复现

Windows PowerShell 7：

```powershell
Set-Location 'D:\MC3-Visual-Analytics'
& '.\.venv\Scripts\python.exe' scripts/prepare_data.py
Set-Location frontend
npm run build
Set-Location ..
& '.\.venv\Scripts\python.exe' -m pytest backend/tests -q
pwsh -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
Set-Location frontend
$env:MC3_BASE_URL = 'http://127.0.0.1:8000'
npm run test:e2e
node tests/redesign.mjs
node tests/topic-scope.mjs
node tests/investigation.mjs
node tests/workbench.mjs
node tests/analysis-tasks.mjs
node tests/reliability.mjs
node tests/investigation-quality.mjs
node tests/findings.mjs
node tests/topic-sampling.mjs
node tests/user-feedback.mjs
node tests/case-study.mjs
node tests/visual-design.mjs
Set-Location ..
& '.\.venv\Scripts\python.exe' scripts/export_analysis.py
& '.\.venv\Scripts\python.exe' scripts/review_topics.py
& '.\.venv\Scripts\python.exe' scripts/sample_topic_evidence.py
& '.\.venv\Scripts\python.exe' scripts/benchmark.py
```

浏览器测试通过 Playwright 调用本机 Microsoft Edge，无需下载浏览器。测试结果、性能测量及截图存于 `docs/`。若没有 Edge，可安装 Edge 或调整测试中的 Playwright channel；后端与构建检查不依赖浏览器。

开发模式使用两个终端，分别执行项目根目录下的 `.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend` 和 frontend 下的 `npm run dev`，前端地址为 http://127.0.0.1:5173/。请先停止生产服务，避免端口冲突。

WSL2 Ubuntu 的 Bash 环境可在已安装 Python 3.11/3.12、对应 venv 包及兼容 Node.js 的前提下运行。Ubuntu 缺少 ensurepip 时先由用户安装 `python3-venv`，或使用已有的独立 Python 环境：

```bash
cd /mnt/d/MC3-Visual-Analytics
python3 -m venv .venv-linux
source .venv-linux/bin/activate
python -m pip install -r backend/requirements.lock.txt
python scripts/prepare_data.py
cd frontend
npm ci
npm run build
cd ..
python -m pytest backend/tests -q
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

前版历史验收：已实测 WSL2 Ubuntu 24.04、Python 3.12.3、Node.js 24.18.0：Linux 后端 16 项测试、原生前端构建和 Windows Edge 访问 WSL 服务的 20 组交互均通过。2026-10-22 历史版本已复验 Linux 后端和原生前端构建；2026-10-23 当前版本的复验范围见 FINAL_PROJECT_AUDIT。浏览器完整交互本轮在 Windows Edge 中执行。前版验收环境使用 Linux 临时虚拟环境及独立前端副本，未替换 Windows 依赖；不要在 Windows PowerShell 直接粘贴 Bash 代码。

## 工程结构与说明

- `backend/app/`：原始数据索引、API、投影图、事件/异常及化名算法。
- `backend/tests/`：数据、API、图、事件、化名测试。
- `frontend/src/`：Vue 工作台、统一筛选、ECharts 时间视图、D3 网络和证据组件。
- `data/raw/`：原始官方 ZIP，保留不变；`data/processed/`：可重建表和质量报告。
- `scripts/`：准备、数据发现、性能测量；`start.ps1/stop.ps1`：本地生产服务。
- `docs/API.md`、`DATA_DICTIONARY.md`、`DESIGN_RATIONALE.md`、`FINDINGS.md`、`DEMO_SCRIPT.md`、`REPRODUCTION.md`：课程及复现资料。

原始图为 1,159 个节点、3,226 条边；通信投影有 41 个参与实体和 217 个有向连接，承载 584 条消息。两者不是同一种网络。推断、异常和候选结果均可回到原始 ID；不得把相关性解释为因果或违法事实。
