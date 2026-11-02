from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data import dataset as d


def test_findings_recompute_statistics_and_preserve_exact_sources():
    response = TestClient(app).get('/api/findings')
    assert response.status_code == 200
    result = response.json()
    assert result['source_sha256'] == d.source_hash
    cards = {card['id']: card for card in result['items']}
    assert cards['rhythm']['statistics']['morning_messages'] == sum(8 <= m['hour'] < 12 for m in d.messages)
    assert cards['rhythm']['statistics']['first_week_median'] == '10:23'
    assert cards['rhythm']['statistics']['second_week_median'] == '10:27'
    assert cards['groups']['statistics']['internal'] + cards['groups']['statistics']['cross_group'] == len(d.messages)
    assert cards['identity']['statistics']['default_top'] != cards['identity']['statistics']['without_text_top']
    assert cards['nadia']['statistics']['direct_messages'] == 26
    for card in cards.values():
        assert card['level'] == 'author_analysis'
        assert card['competing_explanation'] and card['limitation']
        assert card['state']['message_ids'] == [m['id'] for m in card['evidence']]
        for message in card['evidence']:
            assert message == d.message_index[message['id']]
        for stage in card['stages']:
            assert stage['gap']
            assert set(stage['support_ids'] + stage['counter_ids']) <= set(card['state']['message_ids'])


def test_case_study_notes_and_temporal_comparisons_use_original_records():
    cards = {row['id']: row for row in TestClient(app).get('/api/findings').json()['items']}
    for row in cards['rhythm']['statistics']['entity_changes']:
        messages = d.filter_messages(entity_id=row['entity'])
        assert row['first_count'] == sum(m['date'] <= d.days[6] for m in messages)
        assert row['second_count'] == sum(m['date'] > d.days[6] for m in messages)
        assert set(row['message_ids']) == {m['id'] for m in messages}
    notes = cards['nadia']['source_notes']
    assert {n['id'] for n in notes} == set(cards['nadia']['state']['message_ids'])
    for note in notes:
        assert note['excerpt'] in d.message_index[note['id']]['content']
        assert note['reading'] and note['label']
    for card in cards.values():
        assert card['reasoning_steps']
        for step in card['reasoning_steps']:
            assert set(step['message_ids']) <= set(d.message_index)
            assert step['observation'] and step['interpretation']
