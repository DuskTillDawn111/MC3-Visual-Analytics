from backend.app.data import dataset as d


def test_official_counts_and_direction():
    assert (len(d.nodes), len(d.edges), len(d.messages)) == (1159, 3226, 584)
    assert d.quality['node_types'] == {'Entity': 72, 'Event': 802, 'Relationship': 285}
    assert (d.quality['inferred_edges'], d.quality['recorded_edges']) == (2058, 1168)
    assert sum(d.quality['daily_counts'].values()) == 584
    assert d.quality['invalid_references'] == d.quality['invalid_communication_directions'] == 0
    m = d.message_index['Event_Communication_1']
    assert m['sender'] == 'The Lookout'
    assert m['timestamp'] == '2040-10-01 08:09:00'
    assert 'dolphins' in m['content']


def test_time_and_quality_not_rewritten():
    assert len(d.filter_messages(start='2040-10-01', end='2040-10-01')) == 44
    assert not d.filter_messages(start='2050-01-01')
    assert all(m['hour'] == 8 for m in d.filter_messages(hour=8))
    assert d.quality['missing_timestamp_count'] == 32
    assert len(d.quality['communications_without_evidence']) == 81
    assert d.nodes['Event_VesselMovement_1000']['timestamp'] == '2023-10-14 22:00:00'
    assert len(d.quality['timestamp_outliers']) == 1
    outside = {n['id'] for n in d.quality['outside_observation_events']}
    assert outside == {'Event_VesselMovement_944', 'Event_VesselMovement_1000'}
    assert not d.quality['coordinates_present']


def test_search_evidence_and_symmetric_relationships():
    for name in ('Nadia Conti', 'Boss', 'The Lookout'):
        assert d.filter_messages(q=name)
        assert d.filter_messages(entity_id=name)
    assert d.evidence('Event_Communication_1')['targets']
    for n in d.nodes.values():
        if n.get('sub_type') in ('Colleagues', 'Friends'):
            assert len(d.related_entities(n['id'])) == 2
            assert d.evidence(n['id'])['symmetric']


def test_evidence_checks_expose_duplicates_and_role_conflicts_without_rewriting():
    evidence = d.evidence('Event_Communication_805')
    codes = {row['code'] for row in evidence['message_checks']['Event_Communication_805']}
    assert {'duplicate_content', 'speaker_mismatch'} <= codes
    assert evidence['messages'][0] == d.message_index['Event_Communication_805']
    assert evidence['messages'][0]['sender'] == 'Rodriguez'
    loop = d.evidence('Event_Communication_142')
    assert 'self_loop' in {row['code'] for row in loop['message_checks']['Event_Communication_142']}
    normal = d.evidence('Event_Communication_1')
    assert 'speaker_mismatch' not in {row['code'] for row in normal['message_checks']['Event_Communication_1']}


def test_neighboring_exchange_and_future_event_time_are_inspection_not_causality():
    evidence = d.evidence('Event_Communication_161')
    assert 'Event_Communication_162' in {m['id'] for m in evidence['nearby_exchange']}
    assert all(m == d.message_index[m['id']] for m in evidence['nearby_exchange'])
    future = d.evidence('Event_Collaborate_868')
    assert 'event_after_support' in {row['code'] for row in future['checks']}
    assert future['node']['timestamp'] == '2040-10-14 09:00:00'
