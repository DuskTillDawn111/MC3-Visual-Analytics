"""Fixed-corpus topic model; filtered views retain original message provenance."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import re

import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from .data import dataset as d
from .graph import graph


@lru_cache(maxsize=9)
def topic_features():
    names = {n['id'] for n in d.entities}
    # Radio messages also address named people by given/family name. Do not split
    # organization/vessel names or titles such as "Mrs. Money" into generic terms.
    for entity in d.entities:
        parts = re.findall(r'[A-Za-z]+', entity['id'])
        if entity['sub_type'] == 'Person' and len(parts) > 1 and parts[0].lower() not in {'the', 'mr', 'mrs', 'ms', 'dr'}:
            names.update(part for part in parts if len(part) >= 3)
    names = sorted(names, key=lambda name: (-len(name), name))
    name_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(n) for n in names) + r')\b', re.I)
    texts = [name_pattern.sub(' ', m['content']) for m in d.messages]
    stops = sorted(set(ENGLISH_STOP_WORDS) | {'hey', 'hello', 'thanks', 'thank', 'just', 'know',
                                          'let', 'roger', 'copy', 'responding', 'calling', 'okay',
                                          # Tokenization splits English contractions (we've, I'll, don't).
                                          've', 'll', 're', 'don', 'doesn', 'didn', 'isn', 'aren',
                                          'wasn', 'weren', 'won', 'haven', 'hasn', 'hadn',
                                          'wouldn', 'couldn', 'shouldn', 'ain'})
    vectorizer = TfidfVectorizer(stop_words=stops, min_df=2, max_df=.95,
                                ngram_range=(1, 2), max_features=4000, sublinear_tf=True)
    matrix = vectorizer.fit_transform(texts)
    return matrix, vectorizer.get_feature_names_out()


@lru_cache(maxsize=9)
def model(topic_count: int = 6, seed: int = 42) -> dict:
    matrix, terms = topic_features()
    estimator = NMF(n_components=topic_count, init='nndsvda', random_state=seed, max_iter=600)
    weights = estimator.fit_transform(matrix)
    totals = weights.sum(axis=1, keepdims=True)
    relative = np.divide(weights, totals, out=np.zeros_like(weights), where=totals > 1e-12)
    keywords = [[str(terms[i]) for i in component.argsort()[-8:][::-1]]
                for component in estimator.components_]
    return dict(weights=relative, keywords=keywords, components=estimator.components_,
                reconstruction_error=float(estimator.reconstruction_err_),
                version=sha256(f'{d.source_hash}:nmf-v3:{topic_count}:seed{seed}:min_df2:tfidf:contraction-stops'.encode()).hexdigest()[:16])


def topics(filters: dict, topic_count: int = 6) -> dict:
    fitted = model(topic_count)
    rows = d.filter_messages(**filters)
    indexes = {m['id']: i for i, m in enumerate(d.messages)}
    assignments = []
    for m in rows:
        weights = fitted['weights'][indexes[m['id']]]
        assignments.append(dict(message_id=m['id'], topic_id=int(weights.argmax()) if weights.sum() else None,
                                weights=[round(float(w), 6) for w in weights]))
    assignment_by_id = {a['message_id']: a for a in assignments}
    items = []
    for topic_id in range(topic_count):
        members = [m for m in rows if assignment_by_id[m['id']]['topic_id'] == topic_id]
        ranked = sorted(members, key=lambda m: (-assignment_by_id[m['id']]['weights'][topic_id], m['id']))
        items.append(dict(id=topic_id, keywords=fitted['keywords'][topic_id], count=len(members),
                          message_ids=[m['id'] for m in members], representatives=ranked[:3]))
    groups = []
    for group in graph(filters)['communities']:
        members = set(group['members'])
        related = [a for m in rows if m['sender'] in members or m['receiver'] in members
                   if (a := assignment_by_id[m['id']])['topic_id'] is not None]
        counts = Counter(a['topic_id'] for a in related)
        groups.append(dict(id=group['id'], members=group['members'],
                           counts=[counts[i] for i in range(topic_count)],
                           message_ids=[[a['message_id'] for a in related if a['topic_id'] == i]
                                        for i in range(topic_count)]))
    daily = []
    for day in d.days:
        counts = Counter(assignment_by_id[m['id']]['topic_id'] for m in rows if m['date'] == day)
        daily.append(dict(date=day, counts=[counts[i] for i in range(topic_count)]))
    return dict(topics=items, groups=groups, daily=daily, assignments=assignments,
                total=len(rows), unassigned=sum(a['topic_id'] is None for a in assignments),
                method='TF-IDF + NMF; highest relative factor assigns a message, not a calibrated probability',
                model=dict(version=fitted['version'], source_sha256=d.source_hash, topic_count=topic_count,
                           seed=42, fit_scope='all 584 official communications; full entity names, multi-part person-name tokens and English contraction fragments removed',
                           reconstruction_error=round(fitted['reconstruction_error'], 6)),
                limitation='Topics are exploratory and sensitive to training rows and initialization; IDs are not stable categories across models. Cross-community messages occur in both group rows; do not sum group rows as unique messages.')
