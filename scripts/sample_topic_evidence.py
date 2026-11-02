"""Reproducible boundary and fixed-seed sample set for semantic review, not accuracy."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.data import dataset as d
from backend.app.topics import topics


def sample_key(message_id):
    value = 42
    for char in message_id:
        value = ((value ^ ord(char)) * 16777619) & 0xffffffff
    return value


def main():
    result = topics({}, 6)
    assignments = {row['message_id']: row for row in result['assignments']}
    records = []
    for topic in result['topics']:
        def gap(mid):
            ranked = sorted(assignments[mid]['weights'], reverse=True)
            return ranked[0] - ranked[1]
        for mode, key in [('boundary', gap), ('fixed_seed', sample_key)]:
            for mid in sorted(topic['message_ids'], key=lambda mid: (key(mid), mid))[:2]:
                ranking = sorted(enumerate(assignments[mid]['weights']), key=lambda item: (-item[1], item[0]))
                records.append(dict(topic_id=topic['id'], mode=mode, message=d.message_index[mid],
                                    top_two=[dict(topic_id=i, weight=weight) for i, weight in ranking[:2]], gap=gap(mid)))
    output = dict(source_sha256=d.source_hash, model=result['model'], seed=42,
                  method='Two smallest top-factor gaps and two fixed-seed hash samples per maximum-weight topic; same ordering as UI. No independent semantic labels or accuracy claim.',
                  samples=records)
    path = ROOT / 'docs/TOPIC_SAMPLE_REVIEW.json'
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for row in records:
        print(f"T{row['topic_id']+1} {row['mode']} {row['message']['id']} gap={row['gap']:.4f} top={row['top_two']}")
        print(row['message']['content'])
    print(f'{len(records)} sample slots; {len({row["message"]["id"] for row in records})} unique messages; {path}')


if __name__ == '__main__':
    main()
