# 输入检查记录

检查日期：2026-10-21。Windows 11 / PowerShell Core。

## 来源与已读资料

- 启动包：`D:/EdgeDownload/MC3_Codex_%E5%90%AF%E5%8A%A8%E8%B5%84%E6%96%99%E5%8C%85.zip`，623,368 字节。
- 包内包含 PROJECT_SPEC.md、官方 data/raw/MC3_release.zip、7 个辅助处理文件和 tools/prepare_mc3.py。
- 原始工作目录最初仅有 work、outputs 两个目录，并无既存应用工程。
- PROJECT_SPEC.md 已完整读取并原样保存到本交付项目根目录。
- 已完整读取 MC3_schema.json、MC3_data_description.pdf 的文本、辅助 profile.json 和预处理脚本；官方 MC3_graph.json 已直接从嵌套 ZIP 解析。
- 已将原始 ZIP 与辅助文件导入 D:/MC3-Visual-Analytics，并重建处理结果；与启动包内原始 ZIP 做逐字节对比，一致。

官方 PDF 说明竞赛数据是合成数据。系统所称真实数据指实际提供的官方记录，不表示真实世界发生的事件。

## 原始图核验结果

| 指标 | 实测值 |
| --- | ---: |
| 节点 / 唯一节点 ID | 1,159 / 1,159 |
| 有向边 | 3,226 |
| Entity / Event / Relationship | 72 / 802 / 285 |
| 通信事件 | 584 |
| 推断边 / 非推断边 | 2,058 / 1,168 |
| 引用不存在节点的边 | 0 |
| 发送方或接收方数量不为 1 的通信 | 0 |
| Event 缺少 timestamp | 32 |
| 无 evidence_for 的通信 | 81 |

原始根字段为 directed、multigraph、graph、nodes、edges。

每日通信量：10-01 至 10-14 分别为 44、46、46、40、45、38、42、43、35、34、49、43、42、37，合计 584。

`Event_VesselMovement_1000` 的原始 timestamp 确为 `2023-10-14 22:00:00`，movement_type 为 rendezvous；不得改写年份。

`Event_Communication_1` 的时间为 `2040-10-01 08:09:00`，有完整英文原文。Nadia Conti、Boss、The Lookout 均为实际存在的 Person 实体。

## 语义与质量注意事项

- PDF 明确指出 Colleagues 和 Friends 使用“两实体均指向关系节点”的无向语义，其他关系按方向说明角色。
- 事件与关系源于故事人物对通信的推断，可能有错误和矛盾；界面需与原始通信记录区分。
- schema 中某些边类型说明含非通信事件边，且部分统计与实际图不一致；不能直接将这些计数当作当前数据断言。
- 不存在实际经纬度，不应绘制真实航迹或距离。
- 原脚本已检查节点 ID 唯一性、引用合法性及通信方向，适合作为复用起点；仍需补齐索引、质量报告和 API 所需格式。

## 环境与当前验证范围

- 已安装 Python 3.11 与 3.14；默认 python 指向 3.14。
- Node.js v24.13.1，npm 11.8.0；rg 可用。
- 检查时默认 Python 环境未安装 FastAPI、Pandas、NetworkX、scikit-learn。
- 官方 PDF 使用本机 pdftotext 读取；未新增 PDF 解析依赖。
- 后续开发已完成 Phase 0–3，使用独立 .venv 安装依赖；应用测试、构建、浏览器交互和后台启动/停止已运行，详见 docs/archive/VALIDATION.md。

## 后续新增发现

除 2023 年异常年份事件外，原图还包含 Event_VesselMovement_944，时间为 2040-10-15 00:00:00，超出通信观察期。质量报告分别记录 1 个异常年份与 2 个观察期外事件，原值不改写。

原始 ZIP SHA-256：`ca62ea3d0605b05b57b2a9b6c824da67d6ab47e3e714069bfd69f0963380c9d6`。

后续平台验收已覆盖 WSL2 Ubuntu 24.04.4：Python 3.12.3 后端测试、Node.js 24.18.0 原生构建和 Windows 浏览器访问 WSL 服务均通过；未修改 Windows 依赖或 Ubuntu 系统代理/系统包。
