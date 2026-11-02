"""Authored interpretations with computed statistics and explicit source records.

These are investigation starting points, never inferred identity or legal truth.
"""
from functools import lru_cache
from statistics import median

from .data import dataset as d
from .graph import graph
from .aliases import aliases, DEFAULT_WEIGHTS


def sources(ids):
    return [d.message_index[f'Event_Communication_{number}'] for number in ids]


def clock_median(rows):
    seconds = [sum(int(value) * factor for value, factor in zip(m['timestamp'][11:19].split(':'), (3600, 60, 1))) for m in rows]
    value = int(median(seconds))
    return f'{value // 3600:02}:{value % 3600 // 60:02}'


@lru_cache(maxsize=1)
def findings():
    graph_data = graph({})
    morning = sum(8 <= message['hour'] < 12 for message in d.messages)
    internal = sum(group['internal_communications'] for group in graph_data['communities'])
    candidates = aliases('Boss', {})['items']
    ablated = aliases('Boss', {}, dict(DEFAULT_WEIGHTS, text=0))['items']
    scope = dict(start=d.days[0], end=d.days[-1], hour=None, q='', entity='')

    def card(key, title, workspace, claim, counter, limitation, evidence, stats, stages=None):
        return dict(id=key, title=title, level='author_analysis', claim=claim,
                    competing_explanation=counter, limitation=limitation, statistics=stats,
                    evidence=sources(evidence), stages=stages or [],
                    state=dict(workspace=workspace, filters=dict(scope, entity='Nadia Conti' if key == 'nadia' else ''),
                               message_ids=[m['id'] for m in sources(evidence)],
                               alias='Boss' if key == 'identity' else None))

    cards = [
        card('rhythm', '上午通信集中，Nadia 后期参与增加', 'patterns',
             f'{morning}/{len(d.messages)} 条消息出现在 08:00–11:59。两周的通信时间中位数接近；161/162 通过情报要求与一分钟后的回应，呈现一次具体的任务传递。',
             '161 中 Mrs. Money 要求收集情报，162 中 The Intern 以“as requested”回应，任务要求与回复内容相互对应。',
             '节奏统计使用通信发送时间；主体参与量同时计入发送与接收，每条通信对同一主体计一次。', [161, 162],
             dict(morning_messages=morning, total_messages=len(d.messages),
                  first_week_median=clock_median([m for m in d.messages if m['date'] <= d.days[6]]),
                  second_week_median=clock_median([m for m in d.messages if m['date'] > d.days[6]]))),
        card('groups', '四个通信群体的内部协作与跨群联系', 'groups',
             f'全期分为 {len(graph_data["communities"])} 个通信社区：内部消息 {internal} 条，跨群消息 {len(d.messages)-internal} 条。群内往来构成主要联系，跨群消息连接不同活动圈。主题占比进一步呈现各群体的内容侧重。',
             '751 同时谈及部署、设备调整与 ROV 许可延迟，展示同一通信中交织的任务内容。',
             '通信社区按当前范围计算；主题沿用全量模型。主题占比以群体关联消息为分母，跨群通信分别计入双方群体。', [460, 733, 161, 126],
             dict(communities=len(graph_data['communities']), internal=internal, cross_group=len(d.messages)-internal)),
        card('identity', '文本特征改变 Boss 的候选排序', 'investigation',
             f'默认首名为 {candidates[0]["candidate"]}，移除文本特征后为 {ablated[0]["candidate"]}。文本特征使 Nadia 排到首位；其余特征组合将 Elise 排到首位，两种配置提供了两条具体的身份比较路径。',
             '21/22 呈现 Boss 的机会与资金讨论，529/535 呈现 Nadia 的报酬与巡逻安排；866/724 则提供 Boss 与 Elise 的接收语境。',
             '候选排序综合联系人、时间、文本与上下文特征，并单独计入直接互发反证；移除文本特征用于观察排序变化。', [529, 535, 21, 22],
             dict(default_top=candidates[0]['candidate'], without_text_top=ablated[0]['candidate'],
                  default_candidates=[dict(candidate=r['candidate'], score=r['score']) for r in candidates[:3]])),
        card('nadia', 'Nadia 串联文件处置、报酬安排与作业协调', 'investigation',
             '10 月 5 日，Nadia 要求取消特殊通道并销毁相关文件；8 日提出加倍报酬，收到 Liam 关于巡逻调整的回复；12 日建议加速并转移作业；14 日收到 Remora 的最终批准请求。这条通信链呈现她在文件、人员和作业安排之间的协调角色。',
             '334 中 Nadia 向 Council 解释旅游项目的时间冲突；536 中她向 Neptune 提出工程范围异议；575 中 Mako 向 Sentinel 引用许可 CR-7844，解释科研设备运输安排。不同对象的陈述补充了许可与工程背景。',
             '分析选取 8 条通信，覆盖 10 月 5、8、12、14 日四个阶段；其中 7 条由 Nadia 直接参与，575 为 Mako 与 Sentinel 的交叉引用。',
             [331, 334, 529, 535, 536, 575, 847, 943],
             dict(direct_messages=len(d.filter_messages(entity_id='Nadia Conti'))), [
                 dict(date='2040-10-05', claim='取消通道并要求销毁文件', support_ids=['Event_Communication_331'],
                      counter_ids=['Event_Communication_334'], gap='331 将取消通道、销毁文件与另选地点写在同一指令中；334 向 Council 解释旅游项目时间冲突。'),
                 dict(date='2040-10-08', claim='提出加倍报酬；对方自述调整巡逻', support_ids=['Event_Communication_529', 'Event_Communication_535'],
                      counter_ids=['Event_Communication_536', 'Event_Communication_575'], gap='529 提出加倍报酬，535 回复会面与巡逻安排；536 和 575 分别补充工程范围及许可编号。'),
                 dict(date='2040-10-12', claim='自述文件完成并建议加速、转移作业', support_ids=['Event_Communication_847'],
                      counter_ids=[], gap='847 记录 Nadia 自述许可文件完成、计划会见 The Middleman，并建议加速和转移作业。'),
                 dict(date='2040-10-14', claim='收到水下照明的最终批准请求', support_ids=['Event_Communication_943'],
                      counter_ids=[], gap='943 记录 Remora 向 Nadia 汇报准备进度，并请求水下照明的最终批准。'),
             ]),
    ]
    changes = []
    for entity in ['Boss', 'Nadia Conti', 'The Intern', 'The Lookout', 'Mako', 'Mrs. Money']:
        rows = d.filter_messages(entity_id=entity)
        first = [m for m in rows if m['date'] <= d.days[6]]
        second = [m for m in rows if m['date'] > d.days[6]]
        changes.append(dict(entity=entity, first_count=len(first), second_count=len(second),
                            first_median=clock_median(first), second_median=clock_median(second),
                            message_ids=[m['id'] for m in rows]))
    cards[0]['statistics']['entity_changes'] = changes
    cards[0]['claim'] = ('整体通信集中在上午，但主体变化方向不同：Nadia 两周参与消息由 6 条增至 20 条，'
                         'Boss 由 25 条降至 5 条。对具体影响关系，161/162 展示 Mrs. Money 的情报要求和 The Intern 一分钟后的回应。')
    notes = [
        (331, '销毁文件指令', 'Destroy all related documentation.', 'Nadia 将取消特殊通道、销毁相关文件和另选地点安排写在同一指令中。'),
        (334, '时间冲突解释', 'My cancellation was due to scheduling conflicts', '四分钟后，对 Council 的解释转为旅游项目时间冲突，同时自述此前不知道许可获批。'),
        (529, '提出加倍报酬', 'Double your usual fee', 'Nadia 以双倍报酬要求 Liam 维持 Harbor Master 的配合，并约定次日 22 时见面。'),
        (535, '巡逻调整自述', "implemented new patrol schedules that work in our favor", 'Liam 确认次日 22 时会面，自述已转移 Harbor Master 的注意力、调整巡逻，并要求 Nadia 携带约定报酬。'),
        (536, '工程范围异议', 'This extends beyond our agreed scope.', 'Nadia 指出水下基础工程超出原约定范围，要求次日 6 时会面讨论影响和额外资源。'),
        (575, '合法运输自述', "We're operating under permit #CR-7844, not NR-1045.", 'Mako 向 Sentinel 引用许可 CR-7844，说明科研设备运输，并将转发器异常解释为技术问题。'),
        (847, '加速与转移安排', 'Recommend accelerating timeline due to EcoVigil', '自述许可文件完成，并把加速、转移安排与 EcoVigil 的 ROV 审批联系起来。'),
        (943, '最终批准请求', 'Need final approval for underwater lighting placement', 'Remora 向 Nadia 汇报南码头准备工作，并请求 Nemo Reef 水下照明的最终批准。'),
    ]
    cards[3]['source_notes'] = [dict(id=f'Event_Communication_{n}', label=label, excerpt=excerpt, reading=reading)
                               for n, label, excerpt, reading in notes]
    def step(observation, interpretation, ids):
        return dict(observation=observation, interpretation=interpretation,
                    message_ids=[f'Event_Communication_{n}' for n in ids])
    cards[0]['reasoning_steps'] = [
        step('全期 468/584 条通信在 08:00–11:59；两周中位时间为 10:23 / 10:27。',
             '总体通信稳定集中于上午；分主体统计进一步显示参与量在不同角色之间发生变化。', []),
        step('Nadia 由 6 条增至 20 条，Boss 由 25 条降至 5 条。',
             'Nadia 的参与量增至首周的 3.3 倍；她后一周的通信涉及报酬、巡逻安排、作业转移和批准请求。', [529, 535, 847, 943]),
        step('161 的情报要求在 162 得到“as requested”的回应，相隔一分钟。',
             '要求与回应在时间和措辞上直接衔接，呈现 Mrs. Money 向 The Intern 传递情报任务的过程。', [161, 162])]
    cards[1]['reasoning_steps'] = [
        step('四个通信社区内部 464 条，跨群 120 条。', '群内通信占 79.5%，跨群通信占 20.5%；网络同时呈现内部往来密集的群体和连接群体的通信。', [460, 733]),
        step('六主题模型中，社区 2 的主题 5 为 92/255，社区 4 为 23/38。',
             '前者数量更多，后者占比更高（36.1% / 60.5%）；群体规模与内容集中度分别比较。', [751]),
        step('751 同时涉及部署、设备调整与 ROV 许可延迟。',
             '部署、设备和许可事项出现在同一条原文中，解释了该通信同时接近多个主题的原因。', [751])]
    cards[2]['reasoning_steps'] = [
        step('Boss 默认首名为 Nadia，移除文本特征后首名为 Elise。',
             '文本相似性将 Nadia 推到首位；移除该特征后，联系人、时间与上下文的组合将 Elise 推到首位。', [21, 22, 529, 535]),
        step('21/22 涉及 Boss、Mrs. Money、The Middleman 的机会与资金讨论；529/535 涉及 Nadia 与 Liam 的报酬及巡逻安排。',
             'Boss—Nadia 假设将机会与资金讨论、报酬与巡逻安排串联到同一操作者；将两人分别建模时，这些通信形成两条活动链。', [21, 22, 529, 535]),
        step('866 是发给 Boss 的消息，724 是发给 Elise 的消息。',
             '这两条相似语境来自发给候选人的消息，揭示接收内容对文本画像的贡献。', [866, 724])]
    cards[3]['reasoning_steps'] = [
        step('331 要求销毁文件，334 给出时间冲突解释。', 'Nadia 在四分钟内向 Harbor 发出文件处置指令，又向 Council 提出旅游项目的时间冲突解释，呈现面对不同对象的两种表述。', [331, 334]),
        step('529/535 串联报酬、会面与巡逻调整自述；536/575 补充工程范围和许可说法。',
             'Nadia 提出报酬条件，Liam 回复会面、巡逻与付款安排，构成连续的协调往来；同日另两条记录补充工程范围和许可背景。', [529, 535, 536, 575]),
        step('847 涉及加速和转移，943 仍向 Nadia 请求最终批准。',
             '12 日 Nadia 向航运公司建议调整进度与地点，14 日 Remora 向她请求最终批准，协调往来延续至观察期末。', [847, 943])]
    return dict(source_sha256=d.source_hash, analysis_version='review-2026-10-30', items=cards,
                scope='Full official 14-day corpus and default model parameters; interpretations do not automatically change with UI filters.')
