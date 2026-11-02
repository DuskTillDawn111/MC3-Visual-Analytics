from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data import dataset as d
from backend.app.topics import topics


def test_topics_partition_official_messages_and_preserve_provenance():
    result = topics({})
    assert result['total'] == 584
    ids = [mid for topic in result['topics'] for mid in topic['message_ids']]
    assert len(ids) == len(set(ids)) == 584 - result['unassigned']
    assert set(ids) <= set(d.message_index)
    for topic in result['topics']:
        assert topic['keywords'] and topic['count'] == len(topic['message_ids'])
        for message in topic['representatives']:
            assert message == d.message_index[message['id']]
    for group in result['groups']:
        for count, group_ids in zip(group['counts'], group['message_ids']):
            assert count == len(set(group_ids))
            assert all(d.message_index[mid]['sender'] in group['members'] or
                       d.message_index[mid]['receiver'] in group['members'] for mid in group_ids)
    assert sum(sum(day['counts']) for day in result['daily']) == len(ids)


def test_filter_does_not_refit_model_and_empty_scope_has_no_fabricated_samples():
    full = topics({})
    selected = topics({'start': '2040-10-05', 'end': '2040-10-05', 'hour': 10})
    assert selected['total'] == 24
    assert selected['model'] == full['model']
    original = {a['message_id']: a for a in full['assignments']}
    assert all(a == original[a['message_id']] for a in selected['assignments'])
    empty = topics({'q': 'no-such-official-message-xyz'})
    assert empty['total'] == 0 and not empty['assignments']
    assert all(not t['representatives'] and t['count'] == 0 for t in empty['topics'])


def test_topic_endpoint_validates_inputs_and_keeps_selected_entity_scope():
    client = TestClient(app)
    assert client.get('/api/topics?topic_count=1').status_code == 422
    result = client.get('/api/topics?entity_id=Nadia%20Conti&topic_count=4').json()
    assert len(result['topics']) == 4
    assert result['total'] == len(d.filter_messages(entity_id='Nadia Conti'))
    assert all('Nadia Conti' in (d.message_index[a['message_id']]['sender'],
                               d.message_index[a['message_id']]['receiver']) for a in result['assignments'])


def test_topic_keywords_are_not_dominated_by_fragments_of_person_names():
    keywords = {word for topic in topics({})['topics'] for word in topic['keywords']}
    assert not keywords & {'miranda', 'jensen', 'jordan', 'clepper', 'conti', 'nadia'}


def test_topic_keywords_exclude_contraction_fragments_at_every_supported_resolution():
    fragments = {'ve', 'll', 're', 'don', 'doesn', 'didn', 'isn', 'aren', 'won'}
    for count in (4, 6, 8):
        tokens = {token for topic in topics({}, count)['topics']
                  for phrase in topic['keywords'] for token in phrase.split()}
        assert not tokens & fragments, (count, tokens & fragments)
