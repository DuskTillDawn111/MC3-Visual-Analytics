"""Recompute reproducible course findings from the current official input."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.data import dataset as d
from backend.app.graph import graph
from backend.app.aliases import aliases, person_vessel_roles, period_profiles
from backend.app.events import anomalies, timeline
from backend.app.topics import topics

if __name__ == '__main__':
    g = graph({})
    result = dict(source_sha256=d.source_hash, communication_participants=len(g['nodes']),
                  directed_communication_pairs=len(g['edges']), communities=g['communities'],
                  components=g['components'], temporal=anomalies({})['items'][:5],
                  daily_counts=d.quality['daily_counts'],
                  nadia=dict(messages=d.filter_messages(entity_id='Nadia Conti'),
                             events=timeline({'entity_id': 'Nadia Conti'}, page_size=500)),
                  boss_candidates=aliases('Boss', {})['items'],
                  lookout_candidates=aliases('The Lookout', {})['items'],
                  quality=d.quality)
    path = ROOT / 'docs/FINDINGS_DATA.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    current = dict(source_sha256=d.source_hash, messages=len(d.messages), communities=g['communities'],
                   topics=topics({}, 6),
                   candidates={name: aliases(name, {}) for name in ('Boss', 'The Intern', 'The Lookout', 'Mako')},
                   roles=person_vessel_roles('Mako', {}),
                   periods={name: period_profiles(name, {}) for name in ('Boss', 'The Intern', 'The Lookout', 'Mako')},
                   nadia_events=timeline({'entity_id': 'Nadia Conti'}, page_size=500))
    (ROOT / 'docs/CURRENT_ANALYSIS.json').write_text(
        json.dumps(current, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Recomputed findings: {path}')
    for event in result['nadia']['events']['items'][:3]:
        print(event['id'], event['timestamp'], event['evidence_ids'])
