from backend.app.graph import graph
from backend.app.data import dataset as d


def test_projection_is_exact_and_reproducible():
    g = graph({})
    assert sum(e['weight'] for e in g['edges']) == 584
    assert all(d.nodes[n['id']]['type'] == 'Entity' for n in g['nodes'])
    assert all(not e['is_inferred'] for e in g['edges'])
    assert g == graph({})
    assert sum(c['size'] for c in g['communities']) == len(g['nodes'])


def test_filtered_local_and_original_graph():
    g = graph({'start': '2040-10-01', 'end': '2040-10-01'})
    assert sum(e['weight'] for e in g['edges']) == 44
    local = graph({'entity_id': 'Nadia Conti'})
    assert any(n['id'] == 'Nadia Conti' for n in local['nodes'])
    raw = graph({}, mode='original', inferred='inferred')
    assert len(raw['nodes']) <= 180
    assert raw['edges'] and all(e['is_inferred'] for e in raw['edges'])
    assert not graph({'start': '2050-01-01'})['nodes']


def test_group_internal_and_boundary_counts_reconcile_without_double_counting():
    result = graph({})
    membership = {name: group['id'] for group in result['communities'] for name in group['members']}
    internal = 0
    for group in result['communities']:
        assert group['communications'] == group['internal_communications'] + group['sent_external'] + group['received_external']
        internal += group['internal_communications']
    cross = sum(membership[m['sender']] != membership[m['receiver']] for m in d.messages)
    assert internal + cross == 584
    assert [group['internal_communications'] for group in result['communities']] == [181, 156, 89, 38]


def test_node_message_counts_distinguish_unique_messages_from_weighted_degree():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    for filters in ({}, {'start': '2040-10-01', 'end': '2040-10-07'}):
        messages = d.filter_messages(**filters)
        for node in graph(filters)['nodes']:
            rows = [m for m in messages if node['id'] in (m['sender'], m['receiver'])]
            loops = sum(m['sender'] == m['receiver'] for m in rows)
            assert node['communications'] == len(rows)
            assert node['self_loops'] == loops
            assert node['sent'] + node['received'] + loops == len(rows)
            assert node['weighted_degree'] == len(rows) + loops
    raw = graph({}, mode='original')
    for node in raw['nodes']:
        assert node['communications'] == len(d.filter_messages(entity_id=node['id']))
    entities = TestClient(app).get('/api/entities').json()
    assert next(n for n in entities if n['id'] == 'Green Guardians')['communications'] == 59
