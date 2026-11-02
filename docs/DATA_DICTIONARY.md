# 数据字典与来源

唯一原始输入是 `data/raw/MC3_release.zip` 中的 `MC3_release/MC3_graph.json`。这是官方合成竞赛数据，所有应用记录均来自该输入。

| 对象 | 字段与含义 |
| --- | --- |
| Entity | `id` 原始标识；`name/label` 原始名称；`sub_type` 为 Person、Vessel、Location、Organization、Group |
| Event | `id/sub_type`；`timestamp` 原始故事时间，可缺失；其余类型相关字段完整保留 |
| Relationship | `id/sub_type`；`start_date/end_date/submission_date` 等不同来源日期不能混称 timestamp |
| 原始边 | `source/target` 为原始节点 ID；`type` 可缺失；`is_inferred` 表示文本推断；原始 `id` 可缺失或不唯一 |
| 内部边键 | `edge-00000` 等，来自 ZIP 固定边序号；仅用于本数据版本，不当作原始业务 ID |
| 通信 | `Entity --sent--> Communication --received--> Entity`；保留 id、timestamp、sender、receiver、content、evidence_ids |
| 证据 | `Communication --evidence_for--> Event/Relationship`；描述支撑，不能解释为已证实的因果关系 |

`Colleagues/Friends` 的两名实体均指向关系节点，表示对称关系；其他实体—事件/关系—实体路径按方向说明角色。通信投影只由真实通信构成，权重是消息条数，不能把异构关系压成社交联系。

2040-10-01 至 2040-10-14 为主观察期。原始数据未指定时区，系统不做现实世界 UTC 转换。日期过滤包含首尾日期；小时格表示该日 `[HH:00, HH+1:00)`。

缺失 timestamp 的 32 个事件保留并单列；若使用 date/time 字段会明确标注来源。2023 年 VesselMovement 事件保持原值，主时间分析排除，质量检查可访问。81 条通信没有 evidence_for，仍可阅读原文。

运行 `python scripts/prepare_data.py` 重新生成辅助 CSV、profile 及 `data_validation_report.json`。质量报告记录源 ZIP SHA-256、全部缺失时间 ID、时间异常及逐日计数。schema 中的描述性计数与实际图不完全一致，以实际图校验结果为准。
