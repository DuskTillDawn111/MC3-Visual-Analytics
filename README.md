# 暗潮寻踪 · MC3 Visual Analytics

暗潮寻踪是基于 IEEE VAST Challenge 2025 Mini-Challenge 3 官方数据的可视分析工作台，用于探索通信模式、群体联系、化名线索与人物活动。系统将关系图、时间视图和原文证据联动，支持从分析发现回到具体通信、事件及关系记录。

项目采用 Vue 前端与 FastAPI 后端，支持本地运行及 HTML / JSON 分析档案导出。首页以 Nadia Conti 的四阶段调查为入口，完整分析见 [四题分析](docs/ANALYSIS_STORY.md)，实现与验收记录见 [项目验收](docs/FINAL_PROJECT_AUDIT.md)。

## 功能概括

- **证据调查**：按四个阶段梳理 Nadia 的活动，通过关系画布、时间轨道和原文阅读器核查八条引用，保存阅读状态并导出调查档案。
- **通信模式**：通过每日趋势、14 × 24 小时热力图和有向关系图探索通信分布，按日期、小时、主体及关键词筛选，查看异常时段与对应消息。
- **群体与主题**：结合社区划分、有向邻接矩阵和 TF-IDF + NMF 主题模型，比较群体的通信联系、主题分布及代表原文。
- **身份与事件**：比较人物或船舶的化名候选，查看特征贡献、分时段画像、人员与船舶角色，以及事件时间线和支撑通信。
- **分析导出**：导出筛选范围内的消息、证据及图表，生成可离线阅读的 HTML 报告和 JSON 数据。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、D3、ECharts |
| 后端 | Python、FastAPI、Uvicorn、Pydantic |
| 数据分析 | NetworkX、scikit-learn、pandas |
| 验证 | pytest、Playwright、vue-tsc |
| 本地运行 | PowerShell 7 启停脚本、FastAPI 托管前端静态资源 |

## 项目结构

```text
MC3-Visual-Analytics/
├── backend/
│   ├── app/                  数据索引、API 与分析算法
│   ├── tests/                后端测试
│   └── requirements.lock.txt Python 依赖锁定文件
├── frontend/
│   ├── src/                  Vue 工作台、图表、筛选状态与报告导出
│   ├── tests/                浏览器交互与界面回归脚本
│   └── package-lock.json     前端依赖锁定文件
├── data/
│   ├── raw/                  官方原始数据 ZIP
│   └── processed/            可重建的数据表与质量报告
├── scripts/                  环境准备、数据核验与分析导出脚本
├── tools/                    原始图数据预处理程序
├── docs/                     分析、设计、接口、验收与截图
├── releases/                 历史源码包与校验值
├── PROJECT_SPEC.md           项目任务说明
├── start.ps1                 启动本地服务
└── stop.ps1                  停止本地服务
```

运行时的虚拟环境、前端依赖、构建目录及 `work/` 日志目录由本机生成，已在 `.gitignore` 中配置。

## 本地运行

准备 **Python 3.11、Node.js 24、npm 和 PowerShell 7**。在 Windows PowerShell 7 中执行：

```powershell
git clone https://github.com/DuskTillDawn111/MC3-Visual-Analytics.git
Set-Location MC3-Visual-Analytics
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -OpenBrowser
```

`setup.ps1` 创建 Python 虚拟环境、安装锁定依赖、重建数据表、构建前端并运行后端测试。首次准备完成后，日常使用直接运行 `start.ps1`。

浏览器访问 **<http://127.0.0.1:8000/>**。FastAPI 在同一端口提供网页与 API，启动脚本会在后台运行服务。健康检查地址为 <http://127.0.0.1:8000/api/health>。

停止服务：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1
```

## 本地开发

完成环境准备后，在项目根目录停止已有服务，再分别打开两个 PowerShell 7 终端。

后端：

```powershell
& '.\.venv\Scripts\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

前端：

```powershell
Set-Location frontend
npm run dev
```

开发页面为 **<http://127.0.0.1:5173/>**，Vite 将 `/api` 请求代理到本地后端。

## 测试与数据复现

在项目根目录运行后端测试：

```powershell
& '.\.venv\Scripts\python.exe' -m pytest backend/tests -q
```

前端类型检查与生产构建：

```powershell
Push-Location frontend
npm run build
Pop-Location
```

浏览器回归使用本机 Microsoft Edge。启动服务后，在项目根目录执行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
Push-Location frontend
$env:MC3_BASE_URL = 'http://127.0.0.1:8000'
npm run test:e2e
node tests/case-study.mjs
Pop-Location
```

更多专项检查位于 `frontend/tests/`，已有验证结果及检查范围见 [项目验收](docs/FINAL_PROJECT_AUDIT.md)。

项目保留官方提供的合成竞赛数据，故事主要时间范围为 2040 年 10 月 1—14 日。原始图包含 **1,159 个节点、3,226 条边及 584 条通信**；通信投影覆盖 **41 个参与实体和 217 个有向连接**。系统直接读取 `data/raw/MC3_release.zip`，按原始 ID 建立证据索引，并保留数据质量检查结果。

重建处理表与质量报告：

```powershell
& '.\.venv\Scripts\python.exe' scripts/prepare_data.py
```

数据字段与检查结果分别见 [数据字典](docs/DATA_DICTIONARY.md) 和 [输入检查](INPUT_AUDIT.md)，复现说明见 [REPRODUCTION.md](docs/REPRODUCTION.md)。

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [项目任务](PROJECT_SPEC.md) | 数据背景与分析问题 |
| [四题分析](docs/ANALYSIS_STORY.md) | 通信、群体、化名和 Nadia 活动的分析结果与依据 |
| [当前分析快照](docs/CURRENT_ANALYSIS.md) | 可复核的统计与证据记录 |
| [可视化设计](docs/DESIGN_RATIONALE.md) | 任务组织、图形编码与交互设计 |
| [API 说明](docs/API.md) | 接口参数、返回结构与筛选约定 |
| [主题质量评审](docs/TOPIC_QUALITY_REVIEW.md) | 主题模型评估与代表原文核查 |
| [项目验收](docs/FINAL_PROJECT_AUDIT.md) | 实现记录、实际验证范围与待复核事项 |
