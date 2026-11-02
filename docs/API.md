# API 合约与实际样例

## 2026-10-28 调查档案

`/api/findings` 的分析版本更新为 `review-2026-10-28`。每题增加 `reasoning_steps`（observation、interpretation、message_ids）；节奏题 statistics 增加 `entity_changes`，按两周分组计算参与通信数、中位时刻与完整源 ID；Nadia 增加 `source_notes`，含原文 ID、短标题、逐字 excerpt 和作者 reading。后台测试核对摘句与原始正文、时段计数和来源引用。

核心调查首页使用固定全期语料，独立于自由探索工作区的筛选。导出 JSON 保存 analysis、chart_filters、filters、messages、reading_state 与 source_sha256，reading_state 包含阶段索引、阅读视角和当前消息 ID。HTML 保存四阶段论证、时间线及八条完整原文；跨主体引用按既有报告规则标注。进入自由探索时恢复相应分析卡片的范围。

## 2026-10-26 前端导出范围

顶部证据 JSON 增加 `chart_filters`，保存导出起始时的图表日期、小时、主体与检索条件。原 `filters` 字段继续描述附录消息请求，选择消息 ID 时可覆盖主体条件。两个字段取自同一时点的快照。HTML 分别展示图表范围与引用组成，按发送方/接收方计算直接参与主体的引用数，并标注跨主体引用；单日背景图附带日期、全天计数与当前小时高亮说明。

## 2026-10-23 增补

- `/api/graph` 节点的 `communications` 为当前日期/小时/检索范围内唯一通信数，自环只计一次；`weighted_degree` 保留自环计两次的加权度。`sent`、`received` 不含自环，二者与 `self_loops` 之和等于 `communications`。邻域和边类型控制显示范围，不重新定义上述通信统计。实体列表与详情采用同一唯一计数。
- `/api/aliases` 新增 `feature_evidence`：共同联系人、共同小时、共同目标以及共享词均附比较双方的源消息；文本项附实际原文片段和余弦贡献。`support_ids` 来自这些实际特征，不再用任意早期消息兜底。
- `diagnostics=true` 按需返回四种特征移除、相同正文去重及逐日留出排名；附排除 ID、样本数和完整排序。样本扰动固定原 TF-IDF 词表与 IDF，不代表重训模型稳定性或身份概率。默认不计算，以减少交互等待。
- `/api/aliases/segments?alias=Boss&split_date=2040-10-05` 的分界日是第二段首日；未传时保持等分默认。分界必须晚于观察首日且不晚于末日，否则 422。返回 `split_date` 和 `split_mode`。
- `/api/findings` 返回四题人工分析卡片、竞争解释、证据缺口、来源 ID、复核日期及可恢复的工作区/筛选/消息状态；Nadia 卡片另含四阶段时间线。该分析基于全期官方语料，不随当前筛选自动重算，不能作为身份真值。
- 前端主题导出记录绝对量或群内占比及其分母；群内占比按该行全部关联消息计算，跨群消息可以属于两行。边界样本按前两因子相对权重差排序，固定抽样使用种子 42 和消息 ID 的确定性散列；这些权重不是概率。
- 顶部报告仅在全局及当前可见分析模块均已加载成功时导出；来源、筛选、所选证据和分析卡片均使用导出起始时的快照。

生产地址 `http://127.0.0.1:8000`；OpenAPI 文档 `/docs`，JSON 合约 `/openapi.json`。本地只读 API，不依赖外部服务。

## 统一筛选与错误

大部分分析接口接受 `start/end`（ISO 日期，首尾包含）、`entity_id`、`hour`（0–23）、`q`（最多 200 字符，按 ID/消息原文/发送接收方检索）。未传日期表示全量通信；输入 start>end 返回 422。故事时间未指定时区，不换算现实 UTC。

实体 ID 带空格必须 URL 编码，例如 `Nadia%20Conti`。未知实体返回 404。所有 404/422 使用以下格式：

```json
{"error":{"code":422,"message":"start must not be after end"}}
```

Pydantic 参数校验还包含 `fields` 数组。列表按时间和原始 ID 稳定排序；分页从 1 开始，page_size 最大 100。

## 接口列表

| GET 路径 | 附加参数 | 响应 |
| --- | --- | --- |
| `/api/health` | 无 | status、data_loaded、messages、source_sha256 |
| `/api/overview` | 统一筛选 | 当前参与主体/通信/投影连接/证据目标，原始总数、period、quality |
| `/api/temporal/heatmap` | 统一筛选 | days、cells(date/hour/count/baseline)、daily、total |
| `/api/temporal/anomalies` | 统一筛选 | 最多 40 个时段；基线/MAD/score/features/message_ids、方法与局限 |
| `/api/graph` | hops=1或2、mode=communication或original、inferred=all/recorded/inferred、edge_type、community | nodes、edges、communities、components、图定义、截断信息 |
| `/api/entities` | q、type | 按 ID 排序的主体列表及全期通信次数 |
| `/api/entities/{id}` | URL 编码 ID | 原始节点、全期通信次数、原始连接 |
| `/api/messages` | 统一筛选、sender、receiver、ids（逗号分隔）、page、page_size | items、total、page、page_size |
| `/api/evidence/{id}` | 原始节点 ID | node、participants、symmetric、edges、messages、targets、status、source |
| `/api/events/timeline` | 统一筛选、event_type、missing_only、include_outliers、page、page_size | items、total、undated、excluded_outliers、types |
| `/api/topics` | 统一筛选、topic_count=2–10（前端 4/6/8） | topics、groups、daily、assignments、total、unassigned、model、method、limitation |
| `/api/aliases/roles` | 统一筛选，必需 entity_id（Person/Vessel） | 原始 Operates、人员/船舶、角色、推断属性、当前与完整支撑 ID；无身份分数 |
| `/api/aliases/segments` | 统一筛选、alias（Person/Vessel） | 前后两段消息、发送/接收/自环、24 小时分布、联系人与源 ID |
| `/api/aliases` | 统一筛选、alias、candidates、neighbors、temporal、text、context、conflict | 每个候选的特征、贡献、样本量、支持/反证 ID、权重、方法及不确定状态 |

## 实际请求/响应

以下为实际数据中的字段摘录，不是完整响应的替代 JSON。

`GET /api/overview?start=2040-10-01&end=2040-10-01`：communications=44，total_communications=584，total_nodes=1159，total_edges=3226。

`GET /api/messages?page_size=1` 的第一条：

```json
{
  "id":"Event_Communication_1",
  "timestamp":"2040-10-01 08:09:00",
  "sender":"The Lookout",
  "receiver":"The Intern",
  "evidence_ids":["Event_Monitoring_0"]
}
```

响应同时包含完整英文 content，开头为 `Hey The Intern, it's The Lookout!`。`GET /api/evidence/Event_Communication_1` 返回该原文、sent/received/evidence_for 原始边及目标 `Event_Monitoring_0`。

`GET /api/overview?entity_id=Nadia%20Conti` 返回 communications=26。`GET /api/events/timeline?entity_id=Nadia%20Conti` 默认 total=15。

`GET /api/events/timeline?missing_only=true&page_size=100` 默认无日期限制，total=32。其中独立 date/time 可解析的记录有 time_source，原始 timestamp 仍保持缺失。

`GET /api/events/timeline?include_outliers=true` 包含 `Event_VesselMovement_1000`，timestamp 保持 `2023-10-14 22:00:00`，time_status 为 out_of_window。include_outliers 会额外列出原始观察窗外记录，即使当前日期筛选位于主观察期；不会改写时间以适应筛选。

`GET /api/aliases?alias=Boss` 的默认前两名为 Nadia Conti（score 约 .351567）和 Elise（约 .346349），score 仅为加权启发式，不能换算成身份概率。支持/反证 ID 均可通过 evidence 接口查询。

Windows PowerShell 请求示例：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/overview'
Invoke-RestMethod 'http://127.0.0.1:8000/api/entities/Nadia%20Conti'
Invoke-RestMethod 'http://127.0.0.1:8000/api/evidence/Event_Communication_1'
```

## 投影、证据与分页边界

通信投影的边权为当前时间/小时/检索范围内的消息数；选主体后显示其 1–2 跳诱导邻域，其中可以包含邻居之间的通信。前端点中此类连线时，按其 message_ids 展示消息，并临时取消阅读器的主体约束。它们不是所选主体发出的消息。

证据接口总是返回完整原始上下文，不受当前筛选约束；证据原文可能跨时间范围。`is_inferred` 原值保留，内部 `key` 为该 ZIP 边序号，不使用不稳定的原始边 id 作主键。Colleagues/Friends 的 symmetric=true，两实体都指向关系节点。

原图模式最多返回 180 个节点，truncated=true 时说明被截断，推荐选择主体缩小范围；完整原始节点和连接始终可用 evidence 检索。缓存上限：图查询 128 项、文本矩阵 64 项；输入数据视为启动后只读。

化名比较忽略 entity_id，仍使用日期/小时/文本范围。前四项权重和必须大于 0，反证权重独立扣分；所有权重限制在 0–1。没有通信、没有可比较候选、未知 ID 或非法权重都提供明确空结果或错误。API 不保证任何唯一身份匹配。

## 主题分析契约（本轮新增）

`GET /api/topics?topic_count=6&entity_id=Nadia%20Conti`。

- 固定官方全量语料拟合 TF-IDF + NMF，筛选只改变聚合；相同 topic_count 的 model.version 不随日期/主体变化。
- `topics[].message_ids` 为当前范围的唯一消息分组，`representatives` 为实际原始消息对象；没有数据时返回空样本，不生成示例。
- `assignments[]` 保留 message_id、topic_id 与相对因子 weights。weights 不是校准概率。
- `groups[]` 的 counts 和 message_ids 按当前窗口通信社区逐主题提供，跨社区消息可能出现在多行；不能把群体行相加当作唯一总数。
- `daily[]` 为官方 14 日逐主题计数；当前范围之外为 0。
- `model` 提供处理版本、源 ZIP SHA-256、topic_count、seed=42、全量拟合范围和重构误差。名称清理仅用于建模，原文不改变。
- `topic_count` 超出 2–10 返回 422。空检索结果仍保留固定模型信息，total=0、空 assignments 和空代表消息。

浏览器消息/主题选择只高亮并限制阅读器消息，不自动改写全局通信统计；日期、主体、关键词筛选才改变全局范围。导出当前连接或主题时，消息集合可以小于总览范围。

## 同类候选、角色与时段画像（2026-10-22）

- `/api/aliases?alias=Mako` 返回 Vessel 同类候选；Person 起点保留原默认人物集。`alias_type`、`comparison=same_type_similarity` 和 `source_sha256` 随结果返回；候选含 candidate_type。同类相似不证明同一身份，船舶无线电操作者可能变化。
- 显式候选与起点类型不同返回 422，提示改查角色关系；组织/地点不进入身份候选。
- `/api/aliases/roles?entity_id=Mako` 返回原图四条人员角色（Davis、Rodriguez、Mrs. Money、Samantha Blake）。每条保留 relationship、edges、is_inferred、evidence_ids 与 all_evidence_ids；没有 score。角色和事实层级由原图决定，不自动确认行为执行。
- 角色筛选按支撑通信的日期/小时/q，而非推断雇佣起止日期；entity_id 用于选择关系主体，不把间接支撑消息删掉。例如 q=Event_Communication_142 可找到 Rodriguez—Mako 的船长关系，虽然原通信节点在图中是 Rodriguez 自环。
- `/api/aliases/segments?alias=Boss` 将筛选内实际观察日期等分前后两半。各段消息互斥；sent/received 不含自环，自环另计，所以三者和为 count。没有两段非空观察时相似值为 null；没有日期范围时 segments 为空。不输出共享化名真值。

## 证据核查字段与全范围事件

`/api/evidence/{id}` 新增 checks、message_checks 和 nearby_exchange。检查项包含 code/text，重复正文项有 related_ids；原始 node、messages 和 edges 均保留。

自环及同文提示描述图和正文的实际状态。speaker_mismatch 只识别有限的开头自称形式，并对唯一姓名提示作对照，可能漏检或误检；不会改边或合并身份。event_after_support 只提示事件时间晚于部分支撑消息，不能判断是计划还是行动已执行。nearby_exchange 返回同双方前后 24 小时内最多 6 条邻近原文，按时间排列，可能超出当前筛选，不能解释为因果链。

事件 API 仍分页（最大 100），返回 source_sha256；前端逐页合并当前筛选内的全部事件构建概览和泳道，列表再按 15 条分页。事件范围导出包含全部当前筛选事件，filters 保存全局日期/主体/小时/q 及局部 event_type、missing_only、include_outliers。导出使用已加载范围的快照；加载中或条件与快照不一致时禁止导出。图 API 的 communities 新增 internal_communications、sent_external、received_external；三者和为该群体的 communications，跨群消息会在双方关联统计中出现。

主题当前处理版本为 nmf-v3：额外排除英语缩写碎片。topic_count 固定时筛选不重训，v2/v3 或不同主题数的编号不可直接对照。limitation 明确提示训练样本与初始化敏感；63 组扰动及原文复核见 TOPIC_QUALITY_REVIEW.md/json，分数、重构误差及种子一致性均不代表语义准确率。
