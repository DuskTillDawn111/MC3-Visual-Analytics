from datetime import date
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .data import dataset as d, ROOT
from .queries import heatmap, overview
from .graph import graph
from .events import timeline, anomalies
from .aliases import aliases, DEFAULT_WEIGHTS, person_vessel_roles, period_profiles
from .topics import topics
from .findings import findings

app = FastAPI(title='暗潮寻踪 MC3', version='1.0.0', description='Auditable visual analytics for official MC3 records')
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:5173', 'http://localhost:5173'],
                   allow_methods=['GET'], allow_headers=['*'])


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={'error': {'code': exc.status_code, 'message': str(exc.detail)}})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={'error': {'code': 422, 'message': 'Invalid query parameters',
                                                         'fields': [str(e['loc']) for e in exc.errors()]}})


def filters(start: date | None = None, end: date | None = None, entity_id: str | None = None,
            hour: Annotated[int | None, Query(ge=0, le=23)] = None,
            q: Annotated[str, Query(max_length=200)] = '') -> dict:
    if start and end and start > end:
        raise HTTPException(422, 'start must not be after end')
    if entity_id and (entity_id not in d.nodes or d.nodes[entity_id]['type'] != 'Entity'):
        raise HTTPException(404, 'Entity not found')
    return dict(start=start.isoformat() if start else None, end=end.isoformat() if end else None,
                entity_id=entity_id, hour=hour, q=q)


F = Annotated[dict, Depends(filters)]


@app.get('/api/health')
def health():
    return dict(status='ok', data_loaded=True, messages=len(d.messages), source_sha256=d.source_hash)


@app.get('/api/overview')
def get_overview(f: F):
    return overview(f)


@app.get('/api/findings')
def get_findings():
    return findings()


@app.get('/api/temporal/heatmap')
def get_heatmap(f: F):
    return heatmap(f)


@app.get('/api/graph')
def get_graph(f: F, hops: Annotated[int, Query(ge=1, le=2)] = 1,
              mode: Annotated[str, Query(pattern='^(communication|original)$')] = 'communication',
              inferred: Annotated[str, Query(pattern='^(all|recorded|inferred)$')] = 'all',
              edge_type: str | None = None, community: int | None = None):
    return graph(f, hops, mode, inferred, edge_type, community)


@app.get('/api/events/timeline')
def get_timeline(f: F, event_type: str | None = None, include_outliers: bool = False,
                 missing_only: bool = False, page: Annotated[int, Query(ge=1)] = 1,
                 page_size: Annotated[int, Query(ge=1, le=100)] = 30):
    return timeline(f, event_type, include_outliers, missing_only, page, page_size)


@app.get('/api/temporal/anomalies')
def get_anomalies(f: F):
    return anomalies(f)


@app.get('/api/topics')
def get_topics(f: F, topic_count: Annotated[int, Query(ge=2, le=10)] = 6):
    return topics(f, topic_count)


@app.get('/api/aliases')
def get_aliases(f: F, alias: str = 'Boss', candidates: str | None = None, diagnostics: bool = False,
                neighbors: Annotated[float, Query(ge=0, le=1)] = DEFAULT_WEIGHTS['neighbors'],
                temporal: Annotated[float, Query(ge=0, le=1)] = DEFAULT_WEIGHTS['temporal'],
                text: Annotated[float, Query(ge=0, le=1)] = DEFAULT_WEIGHTS['text'],
                context: Annotated[float, Query(ge=0, le=1)] = DEFAULT_WEIGHTS['context'],
                conflict: Annotated[float, Query(ge=0, le=1)] = DEFAULT_WEIGHTS['conflict']):
    candidate_list = [name.strip() for name in candidates.split(',') if name.strip()] if candidates is not None else None
    try:
        return aliases(alias, f, dict(neighbors=neighbors, temporal=temporal, text=text, context=context, conflict=conflict), candidate_list, diagnostics)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get('/api/aliases/roles')
def get_alias_roles(f: F):
    try:
        return person_vessel_roles(f.get('entity_id'), f)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get('/api/entities')
def entities(q: str = '', type: str | None = None):
    counts = CounterForEntities()
    return [dict(n, communications=counts.get(n['id'], 0)) for n in sorted(d.entities, key=lambda n: n['id'])
            if q.casefold() in n['id'].casefold() and (not type or n['sub_type'] == type)]


@app.get('/api/aliases/segments')
def get_alias_segments(f: F, alias: str = 'Boss', split_date: date | None = None):
    try:
        return period_profiles(alias, f, split_date.isoformat() if split_date else None)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def CounterForEntities():
    from collections import Counter
    return Counter(entity for m in d.messages for entity in {m['sender'], m['receiver']})


@app.get('/api/entities/{entity_id}')
def entity(entity_id: str):
    if entity_id not in d.nodes or d.nodes[entity_id]['type'] != 'Entity':
        raise HTTPException(404, 'Entity not found')
    return dict(node=d.nodes[entity_id], communications=len(d.filter_messages(entity_id=entity_id)),
                evidence=d.evidence(entity_id))


@app.get('/api/messages')
def messages(f: F, page: Annotated[int, Query(ge=1)] = 1,
             page_size: Annotated[int, Query(ge=1, le=100)] = 20,
             sender: str | None = None, receiver: str | None = None, ids: str | None = None):
    rows = d.filter_messages(**f, sender=sender, receiver=receiver)
    if ids:
        selected = set(ids.split(','))
        rows = [m for m in rows if m['id'] in selected]
    offset = (page - 1) * page_size
    return dict(items=rows[offset:offset + page_size], total=len(rows), page=page, page_size=page_size)


@app.get('/api/evidence/{node_id}')
def evidence(node_id: str):
    if node_id not in d.nodes:
        raise HTTPException(404, 'Node not found')
    return d.evidence(node_id)


# Same-origin local production entry; development still uses Vite's /api proxy.
if (ROOT / 'frontend/dist').is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount('/', StaticFiles(directory=ROOT / 'frontend/dist', html=True), name='frontend')
