from collections import Counter
from datetime import datetime
from statistics import median
from math import sqrt
from .data import dataset as d


def resolved_time(node: dict) -> tuple[str | None, str]:
    if node.get('timestamp'):
        return node['timestamp'], 'timestamp'
    if node.get('date'):
        date = str(node['date']).split(' ')[0]
        time = str(node.get('time') or '00:00:00')
        try:
            parsed = datetime.fromisoformat(f'{date} {time}')
            return parsed.isoformat(sep=' '), 'date + time' if node.get('time') else 'date (day precision)'
        except ValueError:
            return None, 'unparseable date/time'
    return None, 'missing timestamp'


def timeline(filters: dict, event_type: str | None = None, include_outliers: bool = False,
             missing_only: bool = False, page: int = 1, page_size: int = 30) -> dict:
    selected_messages = {m['id'] for m in d.filter_messages(**filters)}
    items, excluded = [], 0
    for node in d.events:
        if node['sub_type'] == 'Communication' or event_type and node['sub_type'] != event_type:
            continue
        if missing_only and node.get('timestamp'):
            continue
        participants = d.related_entities(node['id'])
        supports = sorted({e['source'] for e in d.incoming[node['id']] if e.get('type') == 'evidence_for'})
        supported_in_scope = bool(set(supports) & selected_messages)
        entity = filters.get('entity_id')
        if entity and entity not in participants and not supported_in_scope:
            continue
        query = str(filters.get('q') or '').casefold()
        if query and query not in str(node).casefold() and not supported_in_scope:
            continue
        timestamp, source = resolved_time(node)
        outside = bool(timestamp and not d.days[0] <= timestamp[:10] <= d.days[-1])
        if outside and not include_outliers:
            excluded += 1
            continue
        if not outside or not include_outliers:
            if timestamp and filters.get('start') and timestamp[:10] < filters['start']:
                continue
            if timestamp and filters.get('end') and timestamp[:10] > filters['end']:
                continue
            if timestamp and filters.get('hour') is not None and int(timestamp[11:13]) != filters['hour']:
                continue
        if not timestamp and (filters.get('hour') is not None or filters.get('start') or filters.get('end')) and not supported_in_scope:
            # Undated events with no in-scope support are retained in a separate explicit inspection mode.
            if not missing_only:
                continue
        items.append(dict(id=node['id'], sub_type=node['sub_type'], timestamp=timestamp, time_source=source,
                          time_status='out_of_window' if outside else 'undated' if not timestamp else 'alternate_date' if source != 'timestamp' else 'in_window',
                          participants=participants, evidence_ids=supports, status='text_inferred', node=node))
    items.sort(key=lambda e: (e['timestamp'] is None, e['timestamp'] or '', e['id']))
    offset = (page - 1) * page_size
    return dict(items=items[offset:offset + page_size], total=len(items), source_sha256=d.source_hash,
                undated=sum(e['time_status'] == 'undated' for e in items), excluded_outliers=excluded,
                types=sorted({n['sub_type'] for n in d.events if n['sub_type'] != 'Communication'}))


def anomalies(filters: dict) -> dict:
    scoped = d.filter_messages(**filters)
    baseline_filters = {k: v for k, v in filters.items() if k not in ('start', 'end', 'hour')}
    history = d.filter_messages(**baseline_filters)
    counts = Counter((m['date'], m['hour']) for m in history)
    groups: dict[tuple[str, int], list[dict]] = {}
    for m in scoped:
        groups.setdefault((m['date'], m['hour']), []).append(m)
    rows = []
    for (day, hour), messages in sorted(groups.items()):
        other = [counts[date, hour] for date in d.days if date != day]
        center = float(median(other))
        mad = float(median([abs(v - center) for v in other]))
        scale = 1.4826 * mad if mad else max(1.0, sqrt(center + 1))
        burst = max(0.0, (len(messages) - center) / scale)
        previous = {m[k] for m in history if m['date'] < day for k in ('sender', 'receiver')}
        contacts = {m[k] for m in messages for k in ('sender', 'receiver')}
        # Day one has no prior observation; it is not evidence of newly acquired contacts.
        new = sorted(contacts - previous) if day != d.days[0] else []
        pairs = Counter((m['sender'], m['receiver']) for m in messages)
        concentration = max(pairs.values()) / len(messages)
        novelty = len(new) / max(1, len(contacts))
        features = [dict(name='volume_burst', value=round(burst, 4), contribution=round(burst, 4)),
                    dict(name='new_contact_ratio', value=round(novelty, 4), contribution=round(.5 * novelty, 4)),
                    dict(name='repeated_pair_ratio', value=round(concentration, 4), contribution=round(.25 * concentration, 4))]
        score = sum(f['contribution'] for f in features)
        rows.append(dict(date=day, hour=hour, count=len(messages), baseline=center, mad=mad,
                         scale=round(scale, 4), score=round(score, 4), flagged=burst >= 2.5,
                         message_ids=[m['id'] for m in messages], new_contacts=new, features=features,
                         explanation=f'{len(messages)} messages; other-day same-hour median={center:g}, MAD={mad:g}; scale={scale:.3f}; volume z={burst:.3f}. First observation is not contact novelty.'))
    rows.sort(key=lambda r: (-r['score'], r['date'], r['hour']))
    return dict(items=rows[:40], method='Positive robust z (other 13 same-hour days), score=z+0.5*contact novelty+0.25*pair concentration; flag iff z>=2.5',
                limitation='Only 14 observed days; exploratory signal, not statistical significance, wrongdoing or causality.')
