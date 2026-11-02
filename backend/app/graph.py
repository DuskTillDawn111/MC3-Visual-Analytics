"""A communication projection, kept explicitly separate from the original graph."""
from collections import Counter, defaultdict
from functools import lru_cache
import re
import networkx as nx
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from .data import dataset as d


def graph(filters: dict, hops: int = 1, mode: str = 'communication', inferred: str = 'all',
          edge_type: str | None = None, community: int | None = None) -> dict:
    return _cached(tuple(sorted(filters.items())), hops, mode, inferred, edge_type, community)


@lru_cache(maxsize=128)
def _cached(filter_items: tuple, hops: int, mode: str, inferred: str,
            edge_type: str | None, community: int | None) -> dict:
    filters = dict(filter_items)
    focus = filters.pop('entity_id', None)
    messages = d.filter_messages(**filters)
    sent = Counter(m['sender'] for m in messages if m['sender'] != m['receiver'])
    received = Counter(m['receiver'] for m in messages if m['sender'] != m['receiver'])
    self_loops = Counter(m['sender'] for m in messages if m['sender'] == m['receiver'])

    def counts(entity_id):
        unique = sent[entity_id] + received[entity_id] + self_loops[entity_id]
        return dict(communications=unique, sent=sent[entity_id], received=received[entity_id],
                    self_loops=self_loops[entity_id], weighted_degree=unique + self_loops[entity_id])

    pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for m in messages:
        pairs[m['sender'], m['receiver']].append(m['id'])
    directed = nx.DiGraph()
    undirected = nx.Graph()
    for (source, target), ids in sorted(pairs.items()):
        directed.add_edge(source, target, weight=len(ids), distance=1 / len(ids))
        previous = undirected.get_edge_data(source, target, {}).get('weight', 0)
        undirected.add_edge(source, target, weight=previous + len(ids))
    groups = nx.community.louvain_communities(undirected, weight='weight', seed=42) if undirected.number_of_edges() else []
    groups = sorted(groups, key=lambda g: (-len(g), sorted(g)))
    memberships = {node: i for i, group in enumerate(groups) for node in group}
    centrality = nx.betweenness_centrality(directed, weight='distance') if directed else {}
    visible = set(directed.nodes)
    if focus:
        visible = set(nx.single_source_shortest_path_length(undirected, focus, cutoff=hops)) if focus in undirected else {focus}
    if community is not None:
        visible = {n for n in visible if memberships.get(n) == community}
    nodes = [dict(d.nodes[i], community=memberships.get(i, -1), **counts(i),
                  centrality=round(centrality.get(i, 0), 6)) for i in sorted(visible)]
    edges = [dict(key=f'pair-{source}-{target}', source=source, target=target, weight=len(ids),
                  message_ids=ids, type='communication', is_inferred=False,
                  bridge=memberships[source] != memberships[target])
             for (source, target), ids in sorted(pairs.items()) if source in visible and target in visible]
    communities = []
    for i, group in enumerate(groups):
        related = [m for m in messages if m['sender'] in group or m['receiver'] in group]
        tokens = Counter(w for m in related for w in re.findall(r'[a-z]{3,}', m['content'].lower())
                         if w not in ENGLISH_STOP_WORDS and w not in {'hey', 'just', 'know', 'let', 'thanks', 'morning'})
        representatives = sorted(group, key=lambda n: (-counts(n)['communications'], n))[:3]
        communities.append(dict(id=i, members=sorted(group), size=len(group), representatives=representatives,
                                communications=len(related),
                                internal_communications=sum(m['sender'] in group and m['receiver'] in group for m in related),
                                sent_external=sum(m['sender'] in group and m['receiver'] not in group for m in related),
                                received_external=sum(m['receiver'] in group and m['sender'] not in group for m in related),
                                topics=[w for w, _ in tokens.most_common(4)]))
    result = dict(nodes=nodes, edges=edges, communities=communities, mode=mode,
                  total_projection_nodes=directed.number_of_nodes(), total_projection_edges=len(pairs),
                  components=nx.number_connected_components(undirected) if undirected else 0,
                  definition='A→B iff a sent/received communication exists; edge weight=message count; node size=unique messages in the date/hour/text scope. Sent and received exclude self-loops; weighted degree counts each self-loop twice. Entity/neighborhood and community controls only restrict visible nodes.',
                  truncated=False)
    if mode == 'original':
        scoped = [m for m in messages if not focus or m['sender'] in visible or m['receiver'] in visible]
        eligible = set(visible)
        for m in scoped:
            eligible.update((m['id'], m['sender'], m['receiver'], *m['evidence_ids']))
            for target in m['evidence_ids']:
                eligible.update(d.related_entities(target))
        # Deterministic bounded inspection, with all original edges between returned nodes.
        priority = sorted(eligible, key=lambda i: (i not in visible, d.nodes[i]['type'] != 'Entity', i))
        result['truncated'] = len(priority) > 180
        result['eligible_nodes'] = len(priority)
        chosen = set(priority[:180])
        raw_edges = [e for e in d.edges if e['source'] in chosen and e['target'] in chosen
                     and (inferred == 'all' or e['is_inferred'] == (inferred == 'inferred'))
                     and (not edge_type or (e.get('type') or 'structural') == edge_type)]
        endpoints = {e[k] for e in raw_edges for k in ('source', 'target')}
        result['nodes'] = [dict(d.nodes[i], community=memberships.get(i, -1), **counts(i),
                                centrality=round(centrality.get(i, 0), 6)) for i in sorted(endpoints)]
        result['edges'] = [dict(e, type=e.get('type') or 'structural', weight=1,
                                message_ids=sorted({i for i in (e['source'], e['target']) if i in d.message_index}))
                           for e in raw_edges]
        result['definition'] = 'Original heterogeneous edges; dashed=inferred; at most 180 nodes. Undated evidence remains linked.'
    elif inferred == 'inferred' or edge_type and edge_type != 'communication':
        result['edges'] = []
        result['nodes'] = []
    return result
