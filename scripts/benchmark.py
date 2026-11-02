"""Small local measurements; neither a load test nor a production SLA."""
from pathlib import Path
from statistics import median
from time import perf_counter
import json
import httpx

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    results = []
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=30, trust_env=False) as client:
        for path in ('/api/overview', '/api/temporal/heatmap', '/api/graph',
                     '/api/graph?mode=original', '/api/aliases?alias=Boss',
                     '/api/events/timeline?entity_id=Nadia%20Conti', '/api/messages?page_size=20'):
            times, size = [], 0
            for _ in range(6):
                before = perf_counter()
                response = client.get(path)
                response.raise_for_status()
                times.append(round((perf_counter() - before) * 1000, 3))
                size = len(response.content)
            results.append(dict(path=path, first_ms=times[0], subsequent_median_ms=median(times[1:]),
                                max_ms=max(times), response_bytes=size))
    path = ROOT / 'docs/performance-results.json'
    path.write_text(json.dumps(dict(scope='Local loopback; 1 initial + 5 repeated requests; warm server may already cache results.',
                                    measurements=results), indent=2), encoding='utf-8')
    for row in results:
        print(f"{row['path']}: median {row['subsequent_median_ms']:.2f} ms / {row['response_bytes']} bytes")
