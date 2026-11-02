#!/usr/bin/env python3
"""Preprocess the official VAST Challenge 2025 MC3 ZIP into analysis-friendly tables.

Run: python prepare_mc3.py /path/to/MC3_release.zip ./mc3_processed
No third-party dependencies are required.
"""
import collections
import csv
import datetime as dt
import json
import pathlib
import sys
import zipfile


def main(zip_path, out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        path = next((p for p in z.namelist() if p.endswith('/MC3_graph.json')), None)
        if path is None:
            raise FileNotFoundError('MC3_graph.json was not found in the ZIP archive')
        data = json.loads(z.read(path))

    nodes, edges = data['nodes'], data['edges']
    ids = {n['id'] for n in nodes}
    if len(ids) != len(nodes):
        raise ValueError('Node IDs are not unique')
    if any(e['source'] not in ids or e['target'] not in ids for e in edges):
        raise ValueError('Edge source/target refers to missing node')

    senders = collections.defaultdict(list)
    receivers = collections.defaultdict(list)
    evidence = collections.defaultdict(list)
    for e in edges:
        kind = e.get('type')
        if kind == 'sent':
            senders[e['target']].append(e['source'])
        elif kind == 'received':
            receivers[e['source']].append(e['target'])
        elif kind == 'evidence_for':
            evidence[e['source']].append(e['target'])

    def write_csv(name, fields, rows):
        with (out / name).open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k) for k in fields})

    entities = [n for n in nodes if n.get('type') == 'Entity']
    events = [n for n in nodes if n.get('type') == 'Event']
    relationships = [n for n in nodes if n.get('type') == 'Relationship']
    messages = []
    for n in events:
        if n.get('sub_type') != 'Communication':
            continue
        mid = n['id']
        if len(senders[mid]) != 1 or len(receivers[mid]) != 1:
            raise ValueError(f'Unexpected sender/receiver counts for {mid}')
        tm = n['timestamp']
        t = dt.datetime.fromisoformat(tm)
        messages.append({
            'message_id': mid,
            'timestamp': tm,
            'date': t.date().isoformat(),
            'hour': t.hour,
            'sender': senders[mid][0],
            'receiver': receivers[mid][0],
            'content': n['content'],
            'evidence_count': len(evidence[mid]),
            'evidence_targets_json': json.dumps(evidence[mid], ensure_ascii=False),
        })
    messages.sort(key=lambda r: (r['timestamp'], r['message_id']))
    write_csv('messages.csv',
        ['message_id','timestamp','date','hour','sender','receiver','content','evidence_count','evidence_targets_json'], messages)

    write_csv('entities.csv', ['id','sub_type','label','name'], entities)
    event_fields = ['id','sub_type','label','timestamp','date','time','content',
        'movement_type','destination','monitoring_type','findings','assessment_type','results',
        'enforcement_type','outcome','activity_type','participants','thing_collected','reference']
    write_csv('events.csv',event_fields,events)
    rel_fields = ['id','sub_type','label','start_date','end_date','coordination_type',
        'permission_type','operational_role','report_type','submission_date',
        'jurisdiction_type','authority_level','friendship_type']
    write_csv('relationships.csv',rel_fields,relationships)
    write_csv('edges.csv', ['source','target','type','is_inferred','id'], edges)

    daily = collections.Counter(m['date'] for m in messages)
    write_csv('daily_communication_counts.csv', ['date','count'],
        [{'date':d, 'count':c} for d,c in sorted(daily.items())])
    parsed_ts = [dt.datetime.fromisoformat(m['timestamp']) for m in messages]
    outlier_times = [
        {'id': n['id'], 'sub_type': n.get('sub_type'), 'timestamp': n.get('timestamp')}
        for n in events if n.get('timestamp') and not str(n['timestamp']).startswith('2040-10-')
    ]
    report = {
        'source': pathlib.Path(zip_path).name,
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'node_type_counts': dict(collections.Counter(n['type'] for n in nodes)),
        'entity_subtype_counts': dict(collections.Counter(n['sub_type'] for n in entities)),
        'event_subtype_counts': dict(collections.Counter(n['sub_type'] for n in events)),
        'relationship_subtype_counts': dict(collections.Counter(n['sub_type'] for n in relationships)),
        'edge_type_counts': dict(collections.Counter(e.get('type','none') for e in edges)),
        'edge_inferred_counts': dict(collections.Counter(str(e.get('is_inferred')) for e in edges)),
        'communication_count': len(messages),
        'communication_first': min(parsed_ts).isoformat(sep=' '),
        'communication_last': max(parsed_ts).isoformat(sep=' '),
        'daily_communication_counts': dict(sorted(daily.items())),
        'outlier_event_timestamps': outlier_times,
        'events_with_missing_timestamp': sum(not e.get('timestamp') for e in events),
        'communications_with_missing_timestamp': sum(not m.get('timestamp') for m in messages),
        'communications_without_evidence_links': sum(m['evidence_count']==0 for m in messages),
        'coordinates_present': any(any(k in n for k in ('latitude','longitude','lat','lon')) for n in nodes)
    }
    (out / 'profile.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    if len(sys.argv) not in (2,3):
        print('Usage: python prepare_mc3.py MC3_release.zip [output_directory]')
        sys.exit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv)==3 else 'mc3_processed')
