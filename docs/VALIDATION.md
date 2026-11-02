# 阶段验收记录

> 历史记录（2026-10-21），不是当前版本验收。本文测试数量、界面说明和完成判断仅适用于当时快照；当前状态见 [FINAL_PROJECT_AUDIT.md](FINAL_PROJECT_AUDIT.md)。

验收日期：2026-10-21（Asia/Shanghai）。工作区：D:/MC3-Visual-Analytics。

## 阶段结果

| 阶段 | 完成项 | 实际验证 | 剩余工作 |
| --- | --- | --- | --- |
| Phase 0 | 原始输入、数据质量、数据字典、API、真实总览及前后端工程 | 原始 ZIP 与启动包逐字节一致；1,159 节点、3,226 边、584 消息；方向与引用合法；HTTP 页面/健康接口成功 | 无必需项遗留 |
| Phase 1 | 热力图、逐日趋势、投影图、社区/中心性、统一筛选、搜索与原文联动 | Edge 实际点击 SVG 热力格显示 24 条原文；连接操作、Nadia/Boss/The Lookout 搜索、空时间段与重置通过 | 无必需项遗留 |
| Phase 2 | 事件链、解释性异常、缺失时间、独立日期、推断样式与证据查询 | 异常贡献到原消息、32 个缺失 timestamp、2023 年原值及原图虚线通过；事件/异常算法测试通过 | 不提供未经证据确认的因果或违法判断 |
| Phase 3 | 候选排名、可调特征、支持/反证、人工标记、JSON/HTML 报告、性能保护、5 条数据发现与课程文档 | 权重、原文回查、人工标记、完整 584 消息及 3 个 SVG 报告通过；Windows/WSL2 构建与交互通过 | 无必需项遗留；开放身份问题按设计保持不确定 |

## 后端

命令：`.venv/Scripts/python.exe -m pytest backend/tests -q`。

结果：**Windows 16 passed，WSL2 Ubuntu 16 passed**。上游 Starlette 对 TestClient 使用 httpx 给出 1 条弃用提示，不影响测试结果或运行时 API；无失败或跳过。

覆盖基础计数、引用和方向、每日总量、筛选、缺失/异常时间、关系无向语义、消息证据、分页与统一错误、原图/投影、事件链、稀疏异常安全、候选权重和支持/反证、生产页面。

## 前端构建

命令：frontend 下 `npm run build`（vue-tsc --noEmit + vite build）。

结果：**Windows 与 Linux 原生构建均通过，无大分包警告**。JS 分包约 76.65 / 120.48 / 183.63 / 366.48 KB，分别为网络、界面与报告、渲染器和图表。采用 SVG 图表与有界布局。

## 生产页面实际浏览器测试

使用本机 Microsoft Edge，经 Playwright 实际访问 **http://127.0.0.1:8000/**，非静态文件截图。MC3_BASE_URL 指向生产单端口；开发预览已关闭。

结果：**Windows 服务与 WSL 服务各 20 组检查通过，JavaScript pageerror 均为 0**。分别见 `browser-test-results.windows.json` 与 `browser-test-results.wsl.json`；通用结果文件保存最近一次运行。

1. 官方总览、真实图表。
2. 密集时段按钮同步图与消息。
3. 实际 SVG 热力格点击，24 条原始消息。
4. Nadia 主体及带空格 ID。
5. 邻居之间的连接，显示该连接完整消息。
6. Boss 与 The Lookout 搜索。
7. Event_Communication_1 原文及支撑目标。
8. 图节点实际拖动、原图及推断虚线。
9. 异常特征与原始 ID 回查。
10. 缺失时间及异常年份。
11. 候选、权重、人工不确定及证据。
12. 空时间范围。
13. 导出包含全量筛选消息与来源哈希。
14. 1366 桌面布局无横向溢出及运行时错误；另保留 1920 截图。
15. 图节点实际鼠标点击联动主体/详情，无证据连接通信仍完整显示原文。
16. 离线 HTML 报告含 584 条消息、3 个 SVG、来源哈希，无脚本；每个 SVG 都位于对应图框内，不覆盖文字。示例为 sample-report.html。
17. 精确小时报告：选中 10-05 10 时后，报告 24 条消息的 ID 和完整英文内容逐条等于同筛选 API，筛选日期/小时一致。示例为 sample-filtered-report.html。
18. 1/2 跳、社区与边类型组合过滤；原图 evidence_for 切回通信投影后恢复正常网络。
19. 实际点击复制按钮后，浏览器剪贴板内容等于 Event_Communication_1。
20. 实际鼠标滚轮缩放，网络 SVG 可见变换随之改变。

WSL 运行环境为 Ubuntu 24.04.4 LTS、Python 3.12.3、Node.js 24.18.0。临时服务 8011 与 Windows 主服务 8000 使用同一份 D 盘源码/原始数据；通过 Windows 浏览器实际 HTTP 操作验证。Linux 依赖放在临时隔离环境，未覆盖 Windows .venv 或 node_modules。

## 启动、停止与后台窗口

命令：`pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test_lifecycle.ps1`。

结果：**通过**。重复 start 不新增服务，后台进程 MainWindowHandle=0；stop 正确停止并删除状态记录；随后 restart 后健康接口加载 584 条通信，生产页面 HTTP 200。服务最终保持运行，便于用户直接查看。

曾复现并修复：PowerShell ConvertFrom-Json 将 ISO 时间转为 DateTime，导致字符串进程身份校验不匹配；现使用 UTC ticks，兼容旧状态记录。另修复节点拖动、标签遮挡、邻域边消息受主体过滤、未知路由错误格式，均有先失败后通过的检查。

补充回归修复：原图专属 edge_type 在切回通信投影后仍发送到 API，造成网络为空；现在进入通信投影时清空该隐藏条件。新增组合操作用例先复现失败，再验证修复；未改变原始数据或后端分析算法。

## 性能与数据不变性

本地各接口 1 次初始 + 5 次重复请求的后续中位数约 **1.80–10.94 ms**，原图响应约 82 KB；测量环境可能已缓存，不是冷启动或并发负载承诺。原图限制 180 节点、消息/事件分页、图缓存与文本矩阵缓存均生效。详情见 `performance-results.json`。

输入 ZIP 与启动资料包内容逐字节一致，SHA-256 为 `ca62ea3d0605b05b57b2a9b6c824da67d6ab47e3e714069bfd69f0963380c9d6`。没有修改年份、生成经纬度或伪造原文。
