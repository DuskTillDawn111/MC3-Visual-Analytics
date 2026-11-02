"""Uncalibrated, transparent candidate comparison; never resolves an identity."""
from collections import Counter
from functools import lru_cache
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .data import dataset as d

DEFAULT_WEIGHTS = dict(neighbors=.30, temporal=.20, text=.30, context=.20, conflict=.20)
PEOPLE = sorted(n['id'] for n in d.entities if n['sub_type'] == 'Person')
VESSELS = sorted(n['id'] for n in d.entities if n['sub_type'] == 'Vessel')
COMPARABLE = PEOPLE + VESSELS
SUGGESTED_ALIASES = [name for name in PEOPLE if name.startswith(('The ', 'Mrs. ')) or name in ('Boss', 'Small Fry')]
NAME_PATTERN = re.compile('|'.join(re.escape(n['id']) for n in sorted(d.entities, key=lambda n: -len(n['id']))), re.I)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    norm = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.clip(np.dot(a, b) / norm, 0, 1)) if norm else 0.0


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


@lru_cache(maxsize=64)
def text_features(filter_items: tuple):
    records = d.filter_messages(**dict(filter_items))
    texts = [NAME_PATTERN.sub(' ', m['content']) for m in records]
    try:
        vectorizer = TfidfVectorizer(stop_words='english', sublinear_tf=True)
        matrix = vectorizer.fit_transform(texts)
        terms = vectorizer.get_feature_names_out()
    except ValueError:
        matrix = None
        terms = []
    return records, matrix, terms


def aliases(alias: str, filters: dict, weights: dict | None = None, candidates: list[str] | None = None,
            diagnostics: bool = False, _excluded_ids: set | None = None) -> dict:
    if alias not in COMPARABLE or candidates is not None and any(name not in COMPARABLE for name in candidates):
        raise ValueError('Alias and candidates must be existing Person or Vessel entities')
    alias_type = d.nodes[alias]['sub_type']
    if candidates is not None and any(d.nodes[name]['sub_type'] != alias_type for name in candidates):
        raise ValueError('Identity comparison requires the same entity type; use /api/aliases/roles for Person-Vessel roles')
    # Candidate comparison must include both identities: global entity focus is intentionally not applied.
    scope_filters = {k: v for k, v in filters.items() if k != 'entity_id'}
    records, matrix, terms = text_features(tuple(sorted(scope_filters.items())))
    if _excluded_ids:
        keep = [i for i, message in enumerate(records) if message['id'] not in _excluded_ids]
        records = [records[i] for i in keep]
        matrix = matrix[keep] if matrix is not None else None
    by_entity = {name: [i for i, m in enumerate(records) if name in (m['sender'], m['receiver'])] for name in COMPARABLE}
    weights = weights or DEFAULT_WEIGHTS.copy()
    normalizer = sum(weights[k] for k in ('neighbors', 'temporal', 'text', 'context'))
    if normalizer <= 0:
        raise ValueError('At least one positive similarity weight is required')
    candidates = candidates if candidates is not None else [name for name in COMPARABLE
                  if d.nodes[name]['sub_type'] == alias_type and name not in SUGGESTED_ALIASES]
    results = []
    for candidate in candidates:
        if candidate == alias or not by_entity.get(alias) or not by_entity.get(candidate):
            continue
        direct = sorted(set(by_entity[alias]) & set(by_entity[candidate]))
        # Direct exchanges are counter-evidence and excluded from similarity documents and neighborhoods.
        ia = sorted(set(by_entity[alias]) - set(direct))
        ib = sorted(set(by_entity[candidate]) - set(direct))
        ma, mb = [records[i] for i in ia], [records[i] for i in ib]
        na = {m[k] for m in ma for k in ('sender', 'receiver')} - {alias, candidate}
        nb = {m[k] for m in mb for k in ('sender', 'receiver')} - {alias, candidate}
        ca, cb = {t for m in ma for t in m['evidence_ids']}, {t for m in mb for t in m['evidence_ids']}
        ta, tb = np.bincount([m['hour'] for m in ma], minlength=24), np.bincount([m['hour'] for m in mb], minlength=24)
        text_score = 0.0
        text_evidence = []
        if matrix is not None and ia and ib:
            va, vb = np.asarray(matrix[ia].mean(axis=0)).ravel(), np.asarray(matrix[ib].mean(axis=0)).ravel()
            text_score = cosine(va, vb)
            denominator = float(np.linalg.norm(va) * np.linalg.norm(vb))
            term_contributions = va * vb / denominator if denominator else np.zeros_like(va)
            for column in term_contributions.argsort()[::-1][:6]:
                if term_contributions[column] <= 0:
                    continue
                term = str(terms[column])
                sides = []
                for indexes in (ia, ib):
                    ranked = sorted(indexes, key=lambda i: (-float(matrix[i, column]), records[i]['id']))
                    sides.append([records[i]['id'] for i in ranked if matrix[i, column] > 0][:2])
                examples = []
                for mid in sides[0] + sides[1]:
                    content = d.message_index[mid]['content']
                    match = re.search(r'\b' + re.escape(term) + r'\b', content, re.I)
                    if match:
                        examples.append(dict(id=mid, excerpt=content[max(0, match.start()-50):match.end()+85]))
                text_evidence.append(dict(label=term, contribution=round(float(term_contributions[column]), 6),
                                          alias_ids=sides[0], candidate_ids=sides[1], examples=examples))
        conflict = len(direct) / max(1, min(len(by_entity[alias]), len(by_entity[candidate])))
        features = dict(neighbors=jaccard(na, nb), temporal=cosine(ta.astype(float), tb.astype(float)),
                        text=text_score, context=jaccard(ca, cb), conflict=conflict)
        contributions = {key: weights[key] * value / normalizer if key != 'conflict' else -weights[key] * value
                         for key, value in features.items()}
        shared = na & nb
        shared_context = ca & cb
        def examples_for(predicate):
            return dict(alias_ids=[m['id'] for m in ma if predicate(m)][:3],
                        candidate_ids=[m['id'] for m in mb if predicate(m)][:3])

        evidence = dict(
            neighbors=[dict(label=peer, **examples_for(lambda m: peer in (m['sender'], m['receiver'])))
                       for peer in sorted(shared)],
            temporal=[dict(label=f'{hour:02}:00–{hour+1:02}:00', hour=hour,
                           alias_count=int(ta[hour]), candidate_count=int(tb[hour]),
                           **examples_for(lambda m: m['hour'] == hour))
                      for hour in sorted(range(24), key=lambda h: (-int(ta[h]*tb[h]), h))
                      if ta[hour] and tb[hour]][:4],
            text=text_evidence,
            context=[dict(label=target, **examples_for(lambda m: target in m['evidence_ids']))
                     for target in sorted(shared_context)],
        )
        supporting = [mid for feature in evidence.values() for item in feature
                      for mid in item['alias_ids'] + item['candidate_ids']]
        results.append(dict(candidate=candidate, candidate_type=alias_type,
                            score=round(max(0.0, min(1.0, sum(contributions.values()))), 6),
                            features={k: round(v, 6) for k, v in features.items()},
                            contributions={k: round(v, 6) for k, v in contributions.items()},
                            support_ids=sorted(set(supporting))[:12], context_ids=sorted(shared_context),
                            refuting_ids=[records[i]['id'] for i in direct], shared_neighbors=sorted(shared),
                            feature_evidence=evidence,
                            sample_size=dict(alias=len(ma), candidate=len(mb)),
                            conflicts=[f'{len(direct)} direct exchanges exist; distinct radio identities are counter-evidence, not a definitive exclusion.'] if direct else [],
                            evidence_note='Each feature links evidence from both sides. Text examples are ranked by TF-IDF for shared terms contributing to cosine, not arbitrary early messages. These are received or sent communication contexts, not verified authorship or identity proof.'))
    results.sort(key=lambda row: (-row['score'], row['candidate']))
    result = dict(alias=alias, alias_type=alias_type, aliases=SUGGESTED_ALIASES, weights=weights, items=results,
                comparison='same_type_similarity', source_sha256=d.source_hash,
                status='exploratory_candidates_not_confirmed' if results else 'insufficient_data',
                method='Weighted Jaccard neighbors + cosine 24h activity + TF-IDF cosine + Jaccard evidence context - direct-exchange penalty; uncalibrated heuristic.',
                scope='Uses current dates/hour/text query across both identities; entity focus excluded. Same-type similarity does not prove identity; vessel radio operators may vary. Alias suggestions are lexical hints, not factual identity classifications.')
    if diagnostics:
        scenarios = []
        for feature in ('neighbors', 'temporal', 'text', 'context'):
            alternate_weights = dict(weights, **{feature: 0})
            if sum(alternate_weights[k] for k in ('neighbors', 'temporal', 'text', 'context')) <= 0:
                continue
            alternate = aliases(alias, filters, alternate_weights, candidates)
            scenarios.append(dict(key=f'without-{feature}', kind='weight_ablation',
                                  included_messages=len(records), excluded_message_ids=[],
                                  ranking=[dict(candidate=r['candidate'], score=r['score']) for r in alternate['items']]))
        seen, duplicate_ids = set(), set()
        for message in records:
            if message['content'] in seen:
                duplicate_ids.add(message['id'])
            seen.add(message['content'])
        samples = [('unique-content', 'content_perturbation', duplicate_ids)]
        samples += [(f'without-day-{day}', 'leave_day_out', {m['id'] for m in records if m['date'] == day})
                    for day in sorted({m['date'] for m in records})]
        for key, kind, excluded in samples:
            alternate = aliases(alias, filters, weights, candidates, _excluded_ids=excluded)
            scenarios.append(dict(key=key, kind=kind, included_messages=len(records)-len(excluded),
                                  excluded_message_ids=sorted(excluded),
                                  ranking=[dict(candidate=r['candidate'], score=r['score']) for r in alternate['items']]))
        result['diagnostics'] = dict(scenarios=scenarios,
            method='Weight ablation and record perturbation; TF-IDF vocabulary and IDF fixed on the selected baseline corpus. Duplicate removal is an exploratory sensitivity scenario only; original records are unchanged.',
            limitation='Rank stability is not identity accuracy. Empty rankings mean insufficient remaining evidence; scores from different scopes are not calibrated probabilities.')
    return result


def person_vessel_roles(entity_id: str, filters: dict) -> dict:
    """Expose original Operates relationships without treating operators as aliases."""
    if entity_id not in COMPARABLE:
        raise ValueError('Role lookup requires an existing Person or Vessel entity')
    scope_filters = {key: value for key, value in filters.items() if key != 'entity_id'}
    in_scope = {m['id'] for m in d.filter_messages(**scope_filters)}
    scoped = any(value is not None and value != '' for value in scope_filters.values())
    opposite = 'Vessel' if d.nodes[entity_id]['sub_type'] == 'Person' else 'Person'
    adjacent = {edge['source'] for edge in d.incoming[entity_id]} | {edge['target'] for edge in d.outgoing[entity_id]}
    items, excluded = [], 0
    for relationship_id in sorted(adjacent):
        node = d.nodes[relationship_id]
        if node['type'] != 'Relationship' or node['sub_type'] != 'Operates':
            continue
        partners = [name for name in d.related_entities(relationship_id) if d.nodes[name]['sub_type'] == opposite]
        if not partners:
            continue
        edges = d.incoming[relationship_id] + d.outgoing[relationship_id]
        all_ids = sorted({edge['source'] for edge in d.incoming[relationship_id]
                          if edge.get('type') == 'evidence_for' and edge['source'] in d.message_index})
        evidence_ids = [mid for mid in all_ids if mid in in_scope]
        if scoped and not evidence_ids:
            excluded += 1
            continue
        for partner in partners:
            person, vessel = (entity_id, partner) if opposite == 'Vessel' else (partner, entity_id)
            items.append(dict(relationship_id=relationship_id, person=person, vessel=vessel,
                              role=node.get('operational_role'), relationship=node, edges=edges,
                              is_inferred=any(edge['is_inferred'] for edge in edges),
                              evidence_ids=evidence_ids, all_evidence_ids=all_ids))
    return dict(entity_id=entity_id, entity_type=d.nodes[entity_id]['sub_type'], items=items,
                comparison='person_vessel_roles', source_sha256=d.source_hash,
                status='role_links_not_identity' if items else 'no_role_evidence_in_scope',
                excluded_relationships=excluded,
                scope='Dates/hour/text filter supporting communications, not assumed employment dates. Entity focus does not remove indirect supporting messages. Original relationship fields and full source IDs are retained.',
                limitation='Operates describes a recorded role claim, possibly inferred from text; it is not an identity equivalence or proof that an operation occurred.')


def period_profiles(alias: str, filters: dict, split_date: str | None = None) -> dict:
    if alias not in COMPARABLE:
        raise ValueError('Period comparison requires an existing Person or Vessel entity')
    scope = {key: value for key, value in filters.items() if key != 'entity_id'}
    rows = d.filter_messages(**scope, entity_id=alias)
    days = [day for day in d.days if (not scope.get('start') or day >= scope['start'])
            and (not scope.get('end') or day <= scope['end'])]
    middle = (len(days) + 1) // 2
    if split_date is not None:
        if not days or not days[0] < split_date <= days[-1]:
            raise ValueError('split_date must be after the first and no later than the last observed calendar day in scope')
        middle = sum(day < split_date for day in days)
    segments = []
    for window in (days[:middle], days[middle:]):
        if not window:
            continue
        messages = [m for m in rows if window[0] <= m['date'] <= window[-1]]
        peers = sorted({m[key] for m in messages for key in ('sender', 'receiver')} - {alias})
        contacts = []
        for peer in peers:
            related = [m for m in messages if peer in (m['sender'], m['receiver'])]
            contacts.append(dict(entity_id=peer, count=len(related),
                                 sent=sum(m['sender'] == alias for m in related),
                                 received=sum(m['receiver'] == alias for m in related),
                                 message_ids=[m['id'] for m in related]))
        contacts.sort(key=lambda row: (-row['count'], row['entity_id']))
        segments.append(dict(start=window[0], end=window[-1], count=len(messages),
                             sent=sum(m['sender'] == alias and m['receiver'] != alias for m in messages),
                             received=sum(m['receiver'] == alias and m['sender'] != alias for m in messages),
                             self_loops=sum(m['sender'] == m['receiver'] for m in messages),
                             hour_counts=[sum(m['hour'] == hour for m in messages) for hour in range(24)],
                             contacts=contacts, message_ids=[m['id'] for m in messages]))
    comparable = len(segments) == 2 and all(row['count'] for row in segments)
    return dict(alias=alias, alias_type=d.nodes[alias]['sub_type'], segments=segments,
                split_date=split_date, split_mode='custom_boundary' if split_date else 'chronological_halves',
                source_sha256=d.source_hash,
                contact_jaccard=jaccard({c['entity_id'] for c in segments[0]['contacts']},
                                        {c['entity_id'] for c in segments[1]['contacts']}) if comparable else None,
                hour_cosine=cosine(np.asarray(segments[0]['hour_counts'], dtype=float),
                                   np.asarray(segments[1]['hour_counts'], dtype=float)) if comparable else None,
                limitation='Splits the selected calendar days into two chronological halves or at an explicit boundary (second period begins on split_date). Differences may reflect tasks, sampling, or shared operators; they do not identify who used a radio alias. Self-loops are counted separately.')
