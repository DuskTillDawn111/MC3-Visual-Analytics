# 可复核的分析发现

本文是早期统计发现记录。更完整的四题调查、竞争解释与敏感性检查见 [MC3_ANALYSIS_DRAFT.md](MC3_ANALYSIS_DRAFT.md)，当前系统范围与局限见 [FINAL_PROJECT_AUDIT.md](FINAL_PROJECT_AUDIT.md)。

所有数字来自 `scripts/export_analysis.py` 重算的 `FINDINGS_DATA.json`，不依赖故事预设答案。默认全观察期和默认权重；改变筛选、社区或权重后，结果可能变化。

## 1. 最密集小时与最偏离基线的小时不是同一个时段

全期 584 条通信中，2040-10-05 10 时共有 24 条，是最高计数小时；2040-10-11 当日有 49 条，是最高日计数。按“其他 13 日同小时中位数”比较，2040-10-04 13 时的 9 条通信更突出：同小时基线中位数为 0、MAD 为 0，安全降级尺度为 1，正向 z 为 9，综合提示分约 9.028。

该时段消息 ID：`Event_Communication_301`、`302`、`304`、`305`、`309`、`311`、`312`、`313`、`316`（后八项均使用相同 `Event_Communication_` 前缀）。可在热力图或异常提示点击进入原文。

解释：绝对密度和相对基线回答不同问题。9 条消息并不能证明可疑行为；14 日短窗口且 MAD 为 0，使该提示对基线定义敏感。截图：`screenshots/02-hour-evidence.png`，异常细节可在工作台重新选择。

## 2. 原始 72 个实体中，41 个实际参与了通信

通信投影由真实 sent/received 路径恢复，共 41 个参与实体、217 个有向通信对，权重合计 584。其余 31 个实体并非不存在，它们仍可出现在事件或关系证据中；不能将它们全部塞入通信图并解释成孤立的通信主体。

默认 Louvain（seed=42，双向权重在无向社区图中求和）得到 4 个群体，规模为 18、12、9、2。最后一组只有 Clepper Jensen 和 Miranda Jordan，在通信投影中形成独立连通分量；两者相关通信共 38 条。社区不是身份或组织的事实标签。

证据：`FINDINGS_DATA.json` 的 communities/components；在消息搜索中输入 `Clepper Jensen` 或 `Miranda Jordan`，可逐条查阅组成消息。全图截图：`screenshots/01-overview-1920.png`。

## 3. Boss 的前两名候选非常接近，默认排名不足以确认身份

默认权重（邻居 .30、时间 .20、文本 .30、上下文 .20；反证惩罚 .20）下，Boss 与 Nadia Conti 的得分约为 **35.16/100**，与 Elise 约为 **34.63/100**，差距约 0.52 分。该差距很小，也没有校准概率意义。

Boss 与 Nadia 的共享邻居包括 Davis、Liam Thorne、Rodriguez、V. Miesel Shipping；共享上下文包括 `Event_Monitoring_266`、`Event_Monitoring_722`、`Relationship_AccessPermission_243`、`Relationship_Jurisdiction_446`。这些是共享环境的线索，不是同一身份的证明。算法先移除实体名称，并排除双方直接互发通信后再计算相似性。

对照可查 `Event_Communication_199`、`Event_Communication_248`、`Event_Communication_312`、`Event_Communication_313`，以及上述上下文节点的完整原始证据。支持列表是特征示例，不能把每一条示例称作身份确认。

结论：保留多个候选和“不确定”更符合现有证据。The Lookout 的默认首名 Kelly 也仅有 3 条候选消息，样本量提示不可忽略。截图：`screenshots/04-candidates-and-events.png`（截图中调整过权重，分数以该图当前权重为准；本节默认数值由 JSON 重算）。

## 4. Nadia 的候选事件链可以追溯，但不构成违法结论

Nadia Conti 直接参与 26 条通信；按直接事件参与或通信证据连接恢复，可检索到主观察期内 15 个非通信事件。例：`Event_Assessment_329` 由 `Event_Communication_330` 支撑；`Event_Assessment_583` 由 `Event_Communication_584` 支撑。`Event_Monitoring_266` 有多个支撑通信，包括 `Event_Communication_297`、`Event_Communication_677` 等。

事件本身由故事人物从通信中推断，事件时间可能与其支撑消息时间不同。时间排序与共同主体只能形成待核查的关联链，不能直接解释为传播、因果或违法活动。完整节点字段、参与实体及消息保存在 `FINDINGS_DATA.json` 的 nadia 字段，可在工作台点击对应 ID 复查。

## 5. 时间质量问题需要区别处理

32 个 Event 没有 timestamp，其中部分有独立 date/time，可另行解释为日期来源；不能等同“未发生”。除了任务书指出的 `Event_VesselMovement_1000`（2023-10-14 22:00:00），还存在 `Event_VesselMovement_944`（2040-10-15 00:00:00），后者只是超出通信观察期，而非年份错误。

质量报告将 1 个异常年份和 2 个观察期外事件分别列出，原值保持不变。81 条通信没有 evidence_for，也仍可阅读原文。复核来源：`data/processed/data_validation_report.json` 与工作台质量检查。
