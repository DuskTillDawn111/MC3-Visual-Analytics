from math import isfinite
from backend.app.events import timeline, anomalies
from backend.app.data import dataset as d


def test_timeline_missing_and_outliers():
    rows = timeline({}, page_size=500)
    assert rows['excluded_outliers'] == 2
    assert 'Event_VesselMovement_1000' not in {n['id'] for n in rows['items']}
    all_rows = timeline({}, include_outliers=True, page_size=500)
    anomaly = next(n for n in all_rows['items'] if n['id'] == 'Event_VesselMovement_1000')
    assert anomaly['timestamp'] == '2023-10-14 22:00:00'
    assert anomaly['time_status'] == 'out_of_window'
    missing = timeline({}, missing_only=True, page_size=500)
    assert missing['total'] == 32
    assert all(not n['node'].get('timestamp') for n in missing['items'])


def test_nadia_chain_has_original_evidence():
    rows = timeline({'entity_id': 'Nadia Conti'}, page_size=500)
    assert rows['total']
    for event in rows['items']:
        assert event['id'] in d.nodes
        assert all(mid in d.message_index for mid in event['evidence_ids'])


def test_timeline_export_provenance_exists_for_full_and_empty_scopes():
    for filters in ({}, {'start': '2050-01-01', 'end': '2050-01-02'}):
        result = timeline(filters)
        assert result['source_sha256'] == d.source_hash


def test_anomaly_explanations_and_sparse_safety():
    results = anomalies({})
    assert results['items'] and any(n['flagged'] for n in results['items'])
    for row in results['items']:
        assert isfinite(row['score']) and row['message_ids']
        assert abs(sum(f['contribution'] for f in row['features']) - row['score']) < .001
    assert not anomalies({'start': '2050-01-01'})['items']
    for row in anomalies({'entity_id': 'Miranda Jordan'})['items']:
        assert isfinite(row['score'])
