# PROJECT_SPEC 逐项完成审计

> 历史记录（2026-10-21）。其中“通过”与“无遗留”不代表当前质量结论；随后批判性评审发现并修复了范围与布局问题。当前验收见 [FINAL_PROJECT_AUDIT.md](FINAL_PROJECT_AUDIT.md)。

审计日期：2026-10-21（Asia/Shanghai）。检查实际 D 盘源码、官方原始 ZIP、运行中的 HTTP 服务、构建输出及浏览器操作；文档中的状态声明不单独作为完成证据。

## 目标、输入和真实性（任务书 1–3）

| 要求 | 当前实现及权威证据 | 结果 |
| --- | --- | --- |
| T1 通信节奏、T2 群体、T4 事件回溯、T3 候选比较，按阶段形成完整系统 | temporal/network/event/alias/evidence Vue 组件与对应 API；双平台实际端到端记录 | 通过 |
| 实际官方输入，先读任务书、PDF、schema、原图 | PROJECT_SPEC.md 原样保留；INPUT_AUDIT.md 记录已读来源；原 ZIP 与启动包逐字节一致 | 通过 |
| 全部节点、边、通信、节点类型与实体子类型符合事实表 | data.py 读取嵌套 graph JSON；后端计数测试；额外实测确认 Person/Vessel/Location=18/15/29，Organization/Group=5/5 | 通过 |
| 有效通信 584，时间范围 2040-10-01 08:09 至 10-14 13:35，逐日之和 584 | 数据处理报告、data 测试及原始时间区间断言 | 通过 |
| 32 个缺失 timestamp、81 条无证据连接不丢弃 | 质量报告含完整 ID；事件 missing_only=32；浏览器打开无证据消息并比对完整原文 | 通过 |
| 2023 年事件不改写、默认排除并解释 | events 默认排除；quality 显示原值；浏览器检查 Event_VesselMovement_1000 | 通过 |
| 额外观察期外事件不伪装成年份错误 | Event_VesselMovement_944 保留 2040-10-15；异常年份 1 条与观察期外 2 条分列 | 通过 |
| 1,168 条直接记录与 2,058 条推断可区分 | 原图 is_inferred 原值，实线/虚线及图例；浏览器实际切换原图推断过滤并检查线型 | 通过 |
| 有向原图 roots 为 nodes/edges，实体间通信只从 sent/received 恢复 | data.py、graph.py；方向唯一性及边权合计 584 测试 | 通过 |
| Colleagues/Friends 对称编码正确 | related_entities 同时读取两端入/出边；所有该类关系恢复恰好 2 实体，symmetric=true | 通过 |
| 保留原始内容/时间/ID，不依赖非唯一边 id | lossless nodes/edges，内部边键为固定序号，证据含源 ZIP SHA-256；原 ZIP 完全未改 | 通过 |
| 不生成经纬度、真实航线、虚构消息或身份/违法答案 | 原始坐标字段检查为 false；前端只有时间/网络/列表，无地图；候选和异常均运行时计算并标注局限 | 通过 |

## 视图和交互（任务书 4）

| 要求 | 实现与实际验证 | 结果 |
| --- | --- | --- |
| 专业单页工作台，适配 1366×768、1920×1080 | 深色五模块工作台；两个尺寸截图；1366 无横向溢出断言 | 通过 |
| 日期/实体统一过滤、搜索、重置与加载/空/错误反馈 | store.ts、App.vue、api.ts；真实数据量变化、Nadia/Boss/The Lookout 搜索及空时间段检查 | 通过 |
| 实体/化名与详情、通信、其他视图联动 | 图节点实际点击 Boss 后主体与原始详情更新；选择 Nadia 同步热力图/图/消息/事件；化名比较保留独立双主体范围说明 | 通过 |
| 14×24 热力图、精确 tooltip、逐日趋势及实体模式 | TemporalView.vue；默认 336 格、总量 584；实际 SVG 色块点击得到 24 条通信；tooltip 使用 API 精确值/基线 | 通过 |
| 图形、颜色、大小、箭头与图例有数据定义 | NetworkView.vue，Person/Vessel/Location/Organization/Group 形状，社区颜色，加权通信次数大小，方向/线型说明 | 通过 |
| 缩放、节点/画布拖动、1–2 跳、时间、社区和边类型过滤 | D3 zoom/drag；API hops 校验及邻域计算；前端各选择控件；实际节点拖动变换断言、原图推断过滤 | 通过 |
| 局部通信投影与完整原图分开，避免毛线球 | 通信图 41 实体/217 有向对；原图模式最多 180 节点并提示截断；evidence 可查询完整原始连接 | 通过 |
| 图边可回溯消息及源/目标/类型/推断属性 | 连线选择→详情/消息；邻居之间的连接临时独立主体约束，已验证列出全部构成消息 | 通过 |
| 社区不仅有颜色，还能查成员/代表/主题/通信量及桥梁 | graph.communities 提供 members/size/representatives/topics/communications；图例原生 tooltip 显示成员，详情展开主题和代表，跨群桥梁控件 | 通过 |
| 异常有特征、基线、贡献和原文 | AnomalyView 与 events.anomalies；浏览器实际点击，展示中位数/MAD/降级及 ID，回查消息 | 通过 |
| 化名多候选、权重、样本量、不确定、支持/反证 | AliasView 与 aliases.py；默认/自选候选，5 项特征，权重滑块，原文/反证 ID，人工不确定标记；浏览器实际操作通过 | 通过 |
| 时间事件链、类型过滤、原文、复制 ID、往返主体/消息 | EventView、EvidencePanel；时间来源/未定时/观察期外分开，参与者与证据可点击，原始边端点可继续探索；复制与导出控件已实现 | 通过 |
| 已观测通信、文本推断、算法异常、人工判断区别呈现 | 分别采用绿色直接通信、紫色推断、橙色提示、单列人工状态；来源和局限明确 | 通过 |
| 导出选中证据与截图/报告 | JSON 完整筛选记录；自包含 HTML 含当前 3 个 SVG、完整原文和所选节点证据；离线打开/打印；浏览器断言内容/数量/来源及图框布局通过 | 通过 |

## 算法、工程与 API（任务书 5–7、11）

| 要求 | 当前证据 | 结果 |
| --- | --- | --- |
| Python 预处理、合法性检查、质量报告，复用现有脚本 | prepare_data.py 调用原 prepare_mc3.py，产出全部 CSV/profile/data_validation_report.json；加载时检查唯一 ID、引用及方向 | 通过 |
| 度/加权度、中介中心性、连通分量和稳定社区 | NetworkX directed weighted degree、1/权重距离的 betweenness、connected_components、Louvain seed=42；不在异构图混算 | 通过 |
| 解释性稳健异常，稀疏/MAD=0 安全，不按名字评分 | positive robust z + 新出现主体比例 + 重复方向对集中度；测试有限值与贡献总和、空/稀疏范围 | 通过 |
| TF-IDF/cosine、邻居/时间/上下文、反证与可调权重 | aliases.py；名字移除、互发从相似性剔除、归一化权重及独立反证惩罚；无身份概率或强制唯一匹配 | 通过 |
| CPU、前后端分离、TypeScript/Python 类型、模块化 | FastAPI/Pydantic/NetworkX/scikit-learn，Vue/Vite/TS/ECharts/D3；组件与算法模块；无 GPU/LLM/付费服务依赖 | 通过 |
| Windows 与 WSL2 Ubuntu 可运行 | Windows Python 3.11、Node 24.13.1；WSL Ubuntu 24.04 Python 3.12.3、Node 24.18.0：各 16 后端测试、各原生构建、各 20 组 Edge 操作通过 | 通过 |
| 所有规定 API、输入校验、分页、稳定排序、空格 ID、统一错误 | main.py 的完整路由及 /openapi.json；API 测试覆盖 health/overview/entities/messages/evidence/timeline/aliases/anomalies 和 404/422；graph/heatmap 另有测试 | 通过 |
| 原始英文保留、无外部事实补全、版本/启动方式说明 | 数据字典、源哈希、README、Python/npm 锁文件与实际 lifecycle 检查 | 通过 |
| 性能保护，避免每次扫描重载或大图卡顿 | 启动时索引、分页、128 图查询缓存/64 文本矩阵缓存、原图 180 节点、有界力布局、SVG 图表；实际本地接口测量已保存 | 通过 |

## 阶段、自动化与课程交付（任务书 8–10、12）

四阶段的运行顺序、阶段功能与测试已经实施，具体记录见 IMPLEMENTATION_PLAN.md 和 VALIDATION.md。

任务书的 14 项自动化验收条件均有对应证据：官方计数、逐日总量、通信方向、前端统计/节点/边交互、三名称检索、第一条通信、异常年份、缺失时间、推断线型、无证据/无候选/空时段、无虚构地理与原文、后端测试与构建、README 运行命令、性能保护。数据为空时不强行产生候选，原始通信没有证据连接时仍可阅读；均有算法或实际 UI 检查。

必需文档已存在并核对内容：

- PROJECT_SPEC.md、IMPLEMENTATION_PLAN.md、INPUT_AUDIT.md、README.md。
- DATA_DICTIONARY.md：字段、方向、对称关系、时间及来源。
- DESIGN_RATIONALE.md：每个视图的问题、数据属性、编码理由、交互、实际发现与局限。
- FINDINGS.md、FINDINGS_DATA.json：5 条由原始数据重算的发现，带消息/事件 ID、截图或图表证据；不预设身份与违法答案。
- API.md：全部接口、实际请求/响应字段、编码与分页/错误说明。
- REPRODUCTION.md、VALIDATION.md：命令、平台、测试与性能范围。
- DEMO_SCRIPT.md：3–5 分钟连续“模式→群体→候选→事件证据”操作。
- sample-report.html、screenshots/、双平台浏览器结果：可离线使用的报告和展示素材。

Windows start/stop 与重复启动、不可见后台进程、数据加载及生产页面的生命周期测试通过。无需创建云部署、Docker、微服务、Isolation Forest、embedding、地图或官方赛事答案；任务书将这些列为可选扩展或明确排除，不属于未完成项。

结论：Phase 0–3 的必需要求均有当前源码及实际执行证据。未遗留必须开发或验证的工作；化名与因果保持不确定是系统应有的分析边界。

追加组合验收：原图 evidence_for → 通信投影的隐藏过滤条件残留已通过失败用例复现并修复。滚轮缩放、真实剪贴板、邻域/社区组合切换、24 条小时报告与原始消息逐条比对均通过，双平台浏览器覆盖扩大至各 20 组。
