"""Audit the production topic model against seeds and fixed-vocabulary perturbations."""
from pathlib import Path
import hashlib
import json
import sys
import warnings

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import NMF
from sklearn.metrics import adjusted_rand_score
from sklearn.metrics.pairwise import cosine_similarity
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.data import dataset as d
from backend.app.topics import model, topic_features, topics


def compare(matrix, terms, baseline, count, mask, seed=42, init='nndsvda'):
    estimator = NMF(n_components=count, init=init, random_state=seed, max_iter=600)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        estimator.fit(matrix[mask])
        weights = estimator.transform(matrix)
    similarity = cosine_similarity(baseline['components'], estimator.components_)
    original, alternate = linear_sum_assignment(-similarity)
    mapping = dict(zip(alternate.tolist(), original.tolist()))
    predicted = np.array([mapping[int(i)] for i in weights.argmax(axis=1)])
    reference = baseline['weights'].argmax(axis=1)
    zero = weights.sum(axis=1) <= 1e-12
    predicted[zero] = -1
    changes = [m['id'] for i, m in enumerate(d.messages) if predicted[i] != reference[i]]
    matched = []
    for left, right in zip(original, alternate):
        words = [str(terms[i]) for i in estimator.components_[right].argsort()[-8:][::-1]]
        old = set(baseline['keywords'][left])
        matched.append(dict(topic_id=int(left), cosine=round(float(similarity[left, right]), 6),
                            keyword_jaccard=round(len(old & set(words)) / len(old | set(words)), 6),
                            keywords=words))
    return dict(training_messages=int(np.sum(mask)), seed=seed, init=init,
                ari=round(float(adjusted_rand_score(reference, predicted)), 6),
                changed_count=len(changes), changed_message_ids=changes,
                unassigned=int(zero.sum()), matched_topics=matched,
                warnings=sorted({str(item.message) for item in caught}))


def main():
    matrix, terms = topic_features()
    full = np.ones(len(d.messages), dtype=bool)
    seen = set()
    unique = []
    for message in d.messages:
        unique.append(message['content'] not in seen)
        seen.add(message['content'])
    result = dict(source_sha256=d.source_hash, messages=len(d.messages), vocabulary=len(terms),
                  method='NMF components aligned by maximum cosine Hungarian matching; ARI is permutation invariant',
                  perturbation_scope='TF-IDF vocabulary/IDF fixed on official full corpus; only NMF training rows change',
                  limitation='Seed agreement is not semantic validity. Random starts test local optima. Removed-day messages are projected for comparison, not held-out accuracy.',
                  source_files={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in ('backend/app/topics.py', 'scripts/review_topics.py')}, resolutions={})
    with threadpool_limits(limits=1):
        for count in (4, 6, 8):
            baseline = model(count)
            current = topics({}, count)
            checks = {}
            for seed in (0, 7, 99):
                checks[f'seed-{seed}'] = compare(matrix, terms, baseline, count, full, seed=seed)
                checks[f'random-init-{seed}'] = compare(matrix, terms, baseline, count, full, seed=seed, init='random')
            checks['deduplicated-content'] = compare(matrix, terms, baseline, count, np.array(unique))
            for day in d.days:
                mask = np.array([m['date'] != day for m in d.messages])
                checks[f'without-{day}'] = compare(matrix, terms, baseline, count, mask)
            result['resolutions'][str(count)] = dict(model=current['model'],
                topics=[dict(id=t['id'], count=t['count'], keywords=t['keywords'],
                             samples=[dict(id=m['id'], content=m['content'], sender=m['sender'],
                                           receiver=m['receiver']) for m in t['representatives']])
                        for t in current['topics']], checks=checks)
            print(f'Completed {count} topics: {len(checks)} perturbations', flush=True)
    output = ROOT / 'docs/TOPIC_QUALITY_REVIEW.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
