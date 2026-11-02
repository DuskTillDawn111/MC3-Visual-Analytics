from collections import Counter
from statistics import mean
from .data import dataset as d


def overview(filters: dict) -> dict:
    messages = d.filter_messages(**filters)
    participants = {m[k] for m in messages for k in ('sender', 'receiver')}
    return dict(entities=len(participants), communications=len(messages),
                projection_edges=len({(m['sender'], m['receiver']) for m in messages}),
                evidence_targets=len({i for m in messages for i in m['evidence_ids']}),
                total_entities=len(d.entities), total_nodes=len(d.nodes), total_edges=len(d.edges),
                total_communications=len(d.messages), period=d.quality['period'],
                quality=d.quality, filters=filters)


def heatmap(filters: dict) -> dict:
    messages = d.filter_messages(**filters)
    counts = Counter((m['date'], m['hour']) for m in messages)
    days = [day for day in d.days if (not filters.get('start') or day >= filters['start'])
            and (not filters.get('end') or day <= filters['end'])]
    # Baseline always uses the other observed days for this entity/query at the same hour.
    baseline_filters = {k: v for k, v in filters.items() if k not in ('start', 'end', 'hour')}
    all_counts = Counter((m['date'], m['hour']) for m in d.filter_messages(**baseline_filters))
    cells = [dict(date=day, hour=hour, count=counts[day, hour],
                  baseline=round(mean([all_counts[other, hour] for other in d.days if other != day]), 3))
             for day in days for hour in range(24)]
    return dict(days=days, cells=cells,
                daily=[dict(date=day, count=sum(counts[day, h] for h in range(24))) for day in days],
                total=len(messages), baseline_definition='Mean of other 13 observed days at the same story-time hour')
