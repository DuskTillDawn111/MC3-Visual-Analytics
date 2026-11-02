from math import isfinite
import pytest
from fastapi.testclient import TestClient
from backend.app.aliases import aliases, DEFAULT_WEIGHTS
from backend.app.data import dataset as d
from backend.app.main import app

client = TestClient(app)


def test_candidates_explain_scores_and_sources():
    result = aliases('Boss', {})
    assert result['items'] and result['status'] == 'exploratory_candidates_not_confirmed'
    for row in result['items']:
        assert isfinite(row['score']) and 0 <= row['score'] <= 1
        expected = max(0, min(1, sum(row['contributions'].values())))
        assert abs(expected - row['score']) < .00001
        assert all(i in d.message_index for i in row['support_ids'] + row['refuting_ids'])
        assert not set(row['support_ids']) & set(row['refuting_ids'])
        assert all(i in d.nodes for i in row['context_ids'])


def test_empty_scope_and_custom_weights():
    assert not aliases('Boss', {'start': '2050-01-01'})['items']
    zero = dict(DEFAULT_WEIGHTS, neighbors=0, temporal=0, text=0, context=0)
    try:
        aliases('Boss', {}, zero)
    except ValueError:
        pass
    else:
        raise AssertionError('Zero similarity weights must be rejected')
    result = aliases('The Lookout', {}, dict(DEFAULT_WEIGHTS, temporal=1), ['Nadia Conti'])
    assert len(result['items']) == 1
    assert result['items'][0]['candidate'] == 'Nadia Conti'


def test_focus_does_not_remove_comparison_partner():
    a = aliases('Boss', {})
    b = aliases('Boss', {'entity_id': 'Nadia Conti'})
    assert a['items'] == b['items']


def test_vessel_candidates_are_same_type_and_traceable():
    response = client.get('/api/aliases', params={'alias': 'Mako'})
    assert response.status_code == 200
    result = response.json()
    assert result['alias_type'] == 'Vessel'
    assert result['comparison'] == 'same_type_similarity'
    assert result['source_sha256'] == d.source_hash
    assert result['items']
    for row in result['items']:
        assert row['candidate'] != 'Mako'
        assert row['candidate_type'] == d.nodes[row['candidate']]['sub_type'] == 'Vessel'
        assert isfinite(row['score']) and 0 <= row['score'] <= 1
        assert abs(row['score'] - max(0, min(1, sum(row['contributions'].values())))) < .00001
        assert all(mid in d.message_index for mid in row['support_ids'] + row['refuting_ids'])
        assert not set(row['support_ids']) & set(row['refuting_ids'])


def test_cross_type_identity_is_rejected_and_roles_keep_original_provenance():
    for alias, candidate in [('Mako', 'Davis'), ('Boss', 'Mako')]:
        response = client.get('/api/aliases', params={'alias': alias, 'candidates': candidate})
        assert response.status_code == 422
        assert 'role' in response.json()['error']['message'].lower()
        with pytest.raises(ValueError):
            aliases(alias, {}, candidates=[candidate])
    response = client.get('/api/aliases/roles', params={'entity_id': 'Mako'})
    assert response.status_code == 200
    result = response.json()
    assert result['comparison'] == 'person_vessel_roles'
    assert result['source_sha256'] == d.source_hash
    assert {'Relationship_Operates_58', 'Relationship_Operates_75'} <= {
        row['relationship_id'] for row in result['items']}
    for row in result['items']:
        assert row['vessel'] == 'Mako' and d.nodes[row['person']]['sub_type'] == 'Person'
        assert not {'score', 'features', 'contributions'} & row.keys()
        assert row['relationship'] == d.nodes[row['relationship_id']]
        assert {row['person'], row['vessel']} <= set(d.related_entities(row['relationship_id']))
        original_edges = d.incoming[row['relationship_id']] + d.outgoing[row['relationship_id']]
        assert row['edges'] == original_edges
        original_support = sorted(edge['source'] for edge in d.incoming[row['relationship_id']]
                                  if edge.get('type') == 'evidence_for' and edge['source'] in d.message_index)
        assert row['all_evidence_ids'] == row['evidence_ids'] == original_support
        assert row['is_inferred'] == any(edge['is_inferred'] for edge in original_edges)
    inverse = client.get('/api/aliases/roles', params={'entity_id': 'Davis'}).json()
    assert any(row['person'] == 'Davis' and row['vessel'] == 'Mako' and
               row['relationship_id'] == 'Relationship_Operates_58' for row in inverse['items'])


def test_role_scope_uses_supporting_messages_without_requiring_direct_participation():
    # Message 142 is a Rodriguez self-loop in the graph, but supports the Mako captain relationship.
    assert 'Mako' not in (d.message_index['Event_Communication_142']['sender'],
                          d.message_index['Event_Communication_142']['receiver'])
    result = client.get('/api/aliases/roles', params={
        'entity_id': 'Mako', 'start': '2040-10-02', 'end': '2040-10-02',
        'q': 'Event_Communication_142',
    }).json()
    assert len(result['items']) == 1
    row = result['items'][0]
    assert row['relationship_id'] == 'Relationship_Operates_75'
    assert row['person'] == 'Rodriguez' and row['relationship']['start_date'] is None
    assert row['evidence_ids'] == ['Event_Communication_142']
    assert client.get('/api/aliases/roles', params={
        'entity_id': 'Mako', 'start': '2050-01-01',
    }).json()['items'] == []


def test_vessel_empty_scope_and_unsupported_types_do_not_generate_candidates():
    for params in [{'alias': "Mariner's Dream"}, {'alias': 'Mako', 'start': '2050-01-01'}]:
        response = client.get('/api/aliases', params=params)
        assert response.status_code == 200
        assert response.json()['items'] == []
        assert response.json()['status'] == 'insufficient_data'
    for alias in ['Nemo Reef', 'Oceanus City Council', 'unknown']:
        assert client.get('/api/aliases', params={'alias': alias}).status_code == 422
        assert client.get('/api/aliases/roles', params={'entity_id': alias}).status_code in (404, 422)
    assert client.get('/api/aliases/roles').status_code == 422


def test_existing_person_rankings_are_preserved_when_vessels_are_added():
    rows = aliases('Boss', {})['items']
    assert [row['candidate'] for row in rows[:2]] == ['Nadia Conti', 'Elise']
    assert abs(rows[0]['score'] - .351567) < .00001
    assert abs(rows[1]['score'] - .346349) < .00001
    assert all(d.nodes[row['candidate']]['sub_type'] == 'Person' for row in rows)


def test_alias_period_profiles_partition_sources_and_keep_direction():
    response = client.get('/api/aliases/segments', params={'alias': 'Boss'})
    assert response.status_code == 200
    result = response.json()
    assert len(result['segments']) == 2
    assert result['segments'][0]['end'] == '2040-10-07'
    assert result['segments'][1]['start'] == '2040-10-08'
    ids = [mid for segment in result['segments'] for mid in segment['message_ids']]
    assert len(ids) == len(set(ids)) == len(d.filter_messages(entity_id='Boss'))
    for segment in result['segments']:
        assert segment['count'] == sum(segment['hour_counts'])
        assert segment['count'] == segment['sent'] + segment['received'] + segment['self_loops']
        for contact in segment['contacts']:
            assert contact['entity_id'] != 'Boss'
            assert contact['count'] == len(contact['message_ids'])
            for mid in contact['message_ids']:
                assert {d.message_index[mid]['sender'], d.message_index[mid]['receiver']} == {'Boss', contact['entity_id']}
    assert result['source_sha256'] == d.source_hash
    assert 'identity_confirmed' not in result


def test_period_profiles_handle_single_and_missing_periods_without_fake_similarity():
    one = client.get('/api/aliases/segments', params={
        'alias': 'Mako', 'start': '2040-10-01', 'end': '2040-10-01',
    }).json()
    assert len(one['segments']) == 1 and one['contact_jaccard'] is None
    empty = client.get('/api/aliases/segments', params={'alias': 'Mako', 'start': '2050-01-01'}).json()
    assert empty['segments'] == [] and empty['hour_cosine'] is None
    focused = client.get('/api/aliases/segments', params={'alias': 'Boss', 'entity_id': 'Nadia Conti'}).json()
    full = client.get('/api/aliases/segments', params={'alias': 'Boss'}).json()
    assert focused == full


def test_feature_evidence_explains_both_sides_and_never_uses_direct_exchanges():
    result = aliases('Boss', {})
    for row in result['items']:
        for feature in ('neighbors', 'temporal', 'text', 'context'):
            for item in row['feature_evidence'][feature]:
                assert item['alias_ids'] and item['candidate_ids']
                for side, name in [('alias_ids', 'Boss'), ('candidate_ids', row['candidate'])]:
                    for mid in item[side]:
                        message = d.message_index[mid]
                        assert name in (message['sender'], message['receiver'])
                        assert mid not in row['refuting_ids']
                        if feature == 'neighbors':
                            assert item['label'] in (message['sender'], message['receiver'])
                        elif feature == 'temporal':
                            assert message['hour'] == item['hour']
                        elif feature == 'context':
                            assert item['label'] in message['evidence_ids']
                        else:
                            assert item['label'].casefold() in message['content'].casefold()
                if feature == 'text':
                    assert item['contribution'] > 0
                    for snippet in item['examples']:
                        assert snippet['excerpt'] in d.message_index[snippet['id']]['content']
                        assert item['label'].casefold() in snippet['excerpt'].casefold()


def test_sensitivity_recomputes_weight_ablation_and_discloses_fixed_vocabulary():
    result = client.get('/api/aliases', params={'alias': 'Boss', 'diagnostics': 'true'}).json()
    scenarios = result['diagnostics']['scenarios']
    without_text = next(row for row in scenarios if row['key'] == 'without-text')
    expected = aliases('Boss', {}, dict(DEFAULT_WEIGHTS, text=0))['items']
    assert without_text['ranking'] == [{'candidate': row['candidate'], 'score': row['score']} for row in expected]
    assert without_text['ranking'][0]['candidate'] != result['items'][0]['candidate']
    dedup = next(row for row in scenarios if row['key'] == 'unique-content')
    assert dedup['included_messages'] == 580
    assert len([row for row in scenarios if row['kind'] == 'leave_day_out']) == 14
    assert 'fixed' in result['diagnostics']['method'].lower()
    assert 'diagnostics' not in aliases('Boss', {})


def test_custom_period_boundary_partitions_sources_and_rejects_invalid_boundaries():
    custom = client.get('/api/aliases/segments', params={'alias': 'Boss', 'split_date': '2040-10-05'})
    assert custom.status_code == 200
    result = custom.json()
    assert result['segments'][0]['end'] == '2040-10-04'
    assert result['segments'][1]['start'] == '2040-10-05'
    ids = [mid for segment in result['segments'] for mid in segment['message_ids']]
    assert len(ids) == len(set(ids)) == len(d.filter_messages(entity_id='Boss'))
    for split in ('bad', '2040-10-01', '2040-10-15'):
        assert client.get('/api/aliases/segments', params={'alias': 'Boss', 'split_date': split}).status_code == 422
