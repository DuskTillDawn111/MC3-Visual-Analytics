from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_phase_zero_and_filtering():
    assert client.get('/api/health').json()['data_loaded']
    overview = client.get('/api/overview').json()
    assert (overview['total_nodes'], overview['total_edges'], overview['communications']) == (1159, 3226, 584)
    one = client.get('/api/overview', params={'start': '2040-10-01', 'end': '2040-10-01'}).json()
    assert one['communications'] == 44
    heat = client.get('/api/temporal/heatmap').json()
    assert len(heat['cells']) == 336 and sum(c['count'] for c in heat['cells']) == 584
    assert client.get('/api/overview?start=2050-01-01').json()['communications'] == 0


def test_search_and_evidence():
    for name in ('Nadia Conti', 'Boss', 'The Lookout'):
        assert client.get('/api/entities', params={'q': name}).json()[0]['id'] == name
        assert client.get(f'/api/entities/{name}').status_code == 200
    evidence = client.get('/api/evidence/Event_Communication_1').json()
    assert evidence['messages'][0]['content'].startswith('Hey The Intern')
    assert evidence['targets']
    assert client.get('/api/messages?q=Event_Communication_1').json()['total'] >= 1


def test_errors_and_pagination():
    for url in ('/api/overview?hour=24', '/api/overview?start=2040-10-14&end=2040-10-01',
                '/api/messages?page=0', '/api/overview?start=bad'):
        response = client.get(url)
        assert response.status_code == 422
        assert 'error' in response.json()
    assert client.get('/api/evidence/unknown').status_code == 404
    assert client.get('/api/no-such-route').json()['error']['code'] == 404
    assert client.get('/api/messages?page_size=1').json()['items'][0]['id'] == 'Event_Communication_1'


def test_phase_two_three_endpoints_and_invalid_weights():
    assert client.get('/api/events/timeline?missing_only=true&page_size=100').json()['total'] == 32
    assert client.get('/api/events/timeline?include_outliers=true').json()['items'][0]['id'] == 'Event_VesselMovement_1000'
    assert client.get('/api/temporal/anomalies?entity_id=Nadia%20Conti').json()['items']
    assert client.get('/api/aliases?alias=The%20Lookout').json()['items']
    for query in ('alias=unknown', 'neighbors=0&temporal=0&text=0&context=0', 'candidates=unknown', 'text=-1'):
        assert client.get('/api/aliases?' + query).status_code == 422


def test_production_frontend_served_with_api():
    response = client.get('/')
    assert response.status_code == 200
    assert '暗潮寻踪' in response.text
