# 复现与验收说明

当前版本验收以 [FINAL_PROJECT_AUDIT.md](FINAL_PROJECT_AUDIT.md) 为准。下列 16 项后端及 WSL 浏览器结果为 2026-10-21 的历史记录；2026-10-22 当前版已复验 Windows/WSL 后端各 32 项、两平台构建和 Windows Edge 48 组交互。不要把历史 Linux 浏览器结果算作新版本通过。

## 输入不变与重新计算

原始输入为项目内 `data/raw/MC3_release.zip`，不是下载的其他参赛项目。运行 `scripts/prepare_data.py` 会复用原 tools/prepare_mc3.py 重建辅助 CSV，再输出更完整的 `data_validation_report.json`。原 ZIP 的 SHA-256 存入质量报告、健康接口和证据详情。

运行 `scripts/export_analysis.py` 重新计算 `FINDINGS_DATA.json`；文档中的发现以默认全期和默认权重为准。Louvain 和布局使用固定随机源，筛选后的社区可变化。Python 与 npm 锁文件固定本次依赖版本。

## 实际验证范围

本机为 Windows 11 / PowerShell Core，Python 3.11、Node.js 24.13.1、npm 11.8.0。

- 后端覆盖原始计数、每日总量、方向与引用、缺失时间/异常时间、无证据消息、搜索、分页/错误、投影/原图、事件链、稀疏异常、候选权重及支持/反证 ID。
- 前端 `npm run build` 同时执行 vue-tsc 和生产构建。
- 浏览器测试使用本机 Edge，经实际 HTTP 页面操作日期、实体、搜索、图边、节点拖动、原图虚线、异常、缺失时间、年份及候选解释，检查 1920 和 1366 宽度与 JavaScript 异常。
- `browser-test-results.json` 记录浏览器检查结果，`screenshots/` 保存页面截图。
- `performance-results.json` 记录实际本地测量；每个接口 1 次初始加 5 次重复请求。服务可能已有缓存，数字不能称作冷启动或生产性能承诺。
- WSL2 Ubuntu 24.04 已实测：Python 3.12.3 后端 16 项测试、Node.js 24.18.0 原生前端构建均通过；Windows Edge 实际访问 WSL 的临时 8011 服务，20 组交互通过。结果分别保存为 browser-test-results.windows.json 与 browser-test-results.wsl.json。WSL 临时环境位于 /tmp/mc3-audit-20261021，Python 锁定依赖从项目 work 中离线轮子安装，未修改系统代理或系统包；Windows 环境保持不变。

完整命令见 README。生产服务将构建后的前端和 API 一起提供在 8000 端口，减少展示时启动步骤；开发模式由 Vite 5173 代理到 8000。

## 防卡顿与工程限制

- 原始图及索引启动时读取一次；数据版本由源哈希标识，修改原 ZIP 后需重启及重建处理结果。
- 通信投影最多 72 个可能实体；实际全期 41 个参与者。原图最多返回 180 节点，显示截断原因，可通过 evidence 完整检索。
- 消息和事件分页，支持按主体/日期/类型缩小范围。图缓存上限 128，文本特征缓存上限 64。
- 浏览器布局迭代有界，停算后支持拖动；ECharts 使用 SVG，监听容器大小；图引擎、渲染器及网络独立分包。
- 顶部导出逐页获取当前筛选的完整消息，单页导出则明确只含当前页。
- HTML 报告包含导出开始时当前工作区可见的 SVG 视图、当前筛选、选中消息完整附录及节点证据。图表数量随工作区和放大状态变化；图表与所选连线的消息范围可能不同，报告明确区分。图表清除运行时绝对定位样式，已验证不会覆盖报告文字；离线无需 API、外部资源或脚本。
- 人工分析备注保存在浏览器 localStorage，刷新可读；清除浏览器数据会丢失，因此需要时导出 JSON。

## 解释边界

官方数据全部合成，事件与关系源于故事人物文本推断。没有经纬度，没有物理位置互斥判据，没有校准身份标签。候选模型为工程启发式，不训练大型模型，也不承诺识别真实身份。异常规则仅作短窗口探索，因果、违法与身份确认都需要额外证据，系统不自动输出这些结论。

## 当前分析与主题质量

`python scripts/export_analysis.py` 同时输出 CURRENT_ANALYSIS.json；`python scripts/review_topics.py` 输出 TOPIC_QUALITY_REVIEW.json，执行 63 组固定词表的 NMF 扰动。当前人工解释见 CURRENT_ANALYSIS.md 与 TOPIC_QUALITY_REVIEW.md。旧 MC3_ANALYSIS_EVIDENCE.json 和 topic-model-review.json 保留为历史快照，不以新模型覆盖。

`node tests/analysis-tasks.mjs` 是四题及事件导出范围的 5 项脚本化任务检查；它不测量人类完成时间或学习成本。独立包测试的实际依赖、请求地址和文件哈希见 release-verification.json。
