"""Official input, lossless indexes and a single definition of message filters."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]


class Dataset:
    def __init__(self, path: Path = ROOT / 'data/raw/MC3_release.zip') -> None:
        self.source_hash = sha256(path.read_bytes()).hexdigest()
        with zipfile.ZipFile(path) as archive:
            graph_path = next(p for p in archive.namelist() if p.endswith('/MC3_graph.json'))
            self.raw = json.loads(archive.read(graph_path))
        self.nodes = {n['id']: n for n in self.raw['nodes']}
        if len(self.nodes) != len(self.raw['nodes']):
            raise ValueError('Duplicate node IDs')
        self.edges = [dict(e, key=f'edge-{i:05d}') for i, e in enumerate(self.raw['edges'])]
        self.incoming: dict[str, list[dict]] = defaultdict(list)
        self.outgoing: dict[str, list[dict]] = defaultdict(list)
        for e in self.edges:
            if e['source'] not in self.nodes or e['target'] not in self.nodes:
                raise ValueError(f"Invalid node reference: {e['key']}")
            self.outgoing[e['source']].append(e)
            self.incoming[e['target']].append(e)
        self.entities = [n for n in self.nodes.values() if n['type'] == 'Entity']
        self.events = [n for n in self.nodes.values() if n['type'] == 'Event']
        self.messages: list[dict[str, Any]] = []
        for n in self.events:
            if n['sub_type'] != 'Communication':
                continue
            senders = [e['source'] for e in self.incoming[n['id']] if e.get('type') == 'sent']
            receivers = [e['target'] for e in self.outgoing[n['id']] if e.get('type') == 'received']
            if len(senders) != 1 or len(receivers) != 1:
                raise ValueError(f"Invalid sender/receiver count: {n['id']}")
            time = datetime.fromisoformat(n['timestamp'])
            self.messages.append(dict(
                id=n['id'], timestamp=n['timestamp'], date=time.date().isoformat(), hour=time.hour,
                sender=senders[0], receiver=receivers[0], content=n['content'],
                evidence_ids=[e['target'] for e in self.outgoing[n['id']] if e.get('type') == 'evidence_for'],
            ))
        self.messages.sort(key=lambda m: (m['timestamp'], m['id']))
        self.message_index = {m['id']: m for m in self.messages}
        self.content_message_ids: dict[str, list[str]] = defaultdict(list)
        self.speaker_names: dict[str, set[str]] = defaultdict(set)
        for m in self.messages:
            self.content_message_ids[m['content']].append(m['id'])
        for entity in self.entities:
            self.speaker_names[entity['id'].casefold()].add(entity['id'])
            parts = entity['id'].split()
            if entity['sub_type'] == 'Person' and len(parts) > 1 and parts[0] not in ('The', 'Mrs.', 'Mr.'):
                self.speaker_names[parts[0].casefold()].add(entity['id'])
        self.days = sorted({m['date'] for m in self.messages})
        self.first, self.last = self.messages[0]['timestamp'], self.messages[-1]['timestamp']
        self.quality = self.validation_report()

    def validation_report(self) -> dict:
        missing = [n['id'] for n in self.events if not n.get('timestamp')]
        outliers = [dict(id=n['id'], timestamp=n['timestamp'], reason='outside_main_observation_window')
                    for n in self.events if n.get('timestamp') and not self.first[:10] <= n['timestamp'][:10] <= self.last[:10]]
        return dict(
            source='data/raw/MC3_release.zip', source_sha256=self.source_hash,
            nodes=len(self.nodes), edges=len(self.edges), communications=len(self.messages),
            node_types=dict(Counter(n['type'] for n in self.nodes.values())),
            entity_types=dict(Counter(n['sub_type'] for n in self.entities)),
            inferred_edges=sum(e['is_inferred'] for e in self.edges),
            recorded_edges=sum(not e['is_inferred'] for e in self.edges),
            invalid_references=0, invalid_communication_directions=0,
            missing_timestamp_count=len(missing), missing_timestamp_ids=missing,
            timestamp_outliers=[o for o in outliers if o['timestamp'][:4] != self.first[:4]],
            outside_observation_events=outliers,
            communications_without_evidence=[m['id'] for m in self.messages if not m['evidence_ids']],
            daily_counts=dict(sorted(Counter(m['date'] for m in self.messages).items())),
            period=dict(start=self.first, end=self.last),
            coordinates_present=any(set(n) & {'latitude', 'longitude', 'lat', 'lon'} for n in self.nodes.values()),
            notes=[
                'Official synthetic competition records; story time has no specified timezone.',
                'Original graph JSON counts take precedence over descriptive schema counts.',
                'Colleagues/Friends are symmetric: both entities point to the relationship node.',
                'Missing and out-of-window timestamps remain searchable; never rewritten.',
            ],
        )

    def filter_messages(self, start: str | None = None, end: str | None = None,
                        entity_id: str | None = None, hour: int | None = None,
                        q: str = '', sender: str | None = None, receiver: str | None = None) -> list[dict]:
        # Dates are inclusive calendar days in the supplied story time, without UTC conversion.
        text = q.strip().casefold()
        return [m for m in self.messages
                if (not start or m['date'] >= start)
                and (not end or m['date'] <= end)
                and (not entity_id or entity_id in (m['sender'], m['receiver']))
                and (hour is None or m['hour'] == hour)
                and (not sender or m['sender'] == sender)
                and (not receiver or m['receiver'] == receiver)
                and (not text or text in ' '.join((m['id'], m['content'], m['sender'], m['receiver'])).casefold())]

    def related_entities(self, node_id: str) -> list[str]:
        """Return participants, including the symmetric relationship encoding."""
        neighbors = {e['source'] for e in self.incoming[node_id]} | {e['target'] for e in self.outgoing[node_id]}
        return sorted(i for i in neighbors if self.nodes[i]['type'] == 'Entity')

    def evidence(self, node_id: str) -> dict:
        n = self.nodes[node_id]
        incoming, outgoing = self.incoming[node_id], self.outgoing[node_id]
        support_ids = sorted({e['source'] for e in incoming if e.get('type') == 'evidence_for'})
        if node_id in self.message_index:
            support_ids = [node_id]
        targets = [e['target'] for e in outgoing if e.get('type') == 'evidence_for']
        participants = self.related_entities(node_id)
        messages = [self.message_index[i] for i in support_ids if i in self.message_index]
        checks, nearby = [], []
        timestamp = n.get('timestamp')
        if n['type'] == 'Event' and not timestamp:
            checks.append(dict(code='missing_time', text='原始 timestamp 缺失；不表示事件没有发生。'))
        if timestamp and not self.first[:10] <= timestamp[:10] <= self.last[:10]:
            checks.append(dict(code='outside_observation', text='原始时间位于通信观察期外，保留原值。'))
        if node_id not in self.message_index and timestamp and any(timestamp > m['timestamp'] for m in messages):
            checks.append(dict(code='event_after_support', text='事件时间晚于部分支撑通信；可能是计划、回述或推断，不能据此确认行动已执行。'))
        if node_id in self.message_index:
            selected = self.message_index[node_id]
            pair = {selected['sender'], selected['receiver']}
            when = datetime.fromisoformat(selected['timestamp'])
            if len(pair) == 2:
                related = [m for m in self.messages if m['id'] != node_id and {m['sender'], m['receiver']} == pair
                           and abs((datetime.fromisoformat(m['timestamp']) - when).total_seconds()) <= 86400]
                related.sort(key=lambda m: (abs((datetime.fromisoformat(m['timestamp']) - when).total_seconds()), m['id']))
                nearby = sorted(related[:6], key=lambda m: (m['timestamp'], m['id']))
        return dict(node=n, participants=participants, symmetric=n.get('sub_type') in ('Friends', 'Colleagues'),
                    edges=incoming + outgoing,
                    messages=messages, checks=checks,
                    message_checks={m['id']: self.message_checks(m) for m in messages}, nearby_exchange=nearby,
                    targets=[self.nodes[i] for i in targets],
                    status='observed' if node_id in self.message_index else 'text_inferred',
                    source=dict(archive='data/raw/MC3_release.zip', member='MC3_release/MC3_graph.json',
                                node_id=node_id, sha256=self.source_hash))

    def message_checks(self, message: dict) -> list[dict]:
        checks = []
        if message['sender'] == message['receiver']:
            checks.append(dict(code='self_loop', text='图中发送方与接收方相同；需核对原文角色，不将其直接解释为自我通信。'))
        duplicate_ids = [mid for mid in self.content_message_ids[message['content']] if mid != message['id']]
        if duplicate_ids:
            checks.append(dict(code='duplicate_content', text='正文与其他节点完全相同，不能自动视为独立佐证。', related_ids=duplicate_ids))
        cue = re.match(r"^[^,]{1,70},\s+(?:this is\s+|it['’]s\s+)?(.{1,60}?)\s+(?:here|reporting)\b", message['content'], re.I)
        names = self.speaker_names.get(cue.group(1).strip().casefold(), set()) if cue else set()
        if len(names) == 1 and message['sender'] not in names:
            checks.append(dict(code='speaker_mismatch', text=f"原文开头似乎自称 {next(iter(names))}，图中发送方为 {message['sender']}；这是称呼启发式提示，保留原值，不自动纠正或合并身份。"))
        return checks


dataset = Dataset()
