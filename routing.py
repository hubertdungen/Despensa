"""Optional OpenStreetMap geocoding and OSRM road estimates, with bounded requests/cache."""
import itertools
import os
import threading
import time
from datetime import date
import requests

_cache = {}
_lock = threading.Lock()
_last_geocode = 0.0
HEADERS = {'User-Agent': 'Despensa/0.1 (+https://github.com/hubertdungen/Despensa; self-hosted grocery planner)'}


def geocode(query):
    global _last_geocode
    query = query.strip()[:300]
    if len(query) < 4:
        raise ValueError('Indique uma morada ou localização mais completa')
    key = ('geo', query.casefold())
    with _lock:
        if key in _cache:
            return _cache[key][1]
        if time.monotonic() - _last_geocode < 1.1:
            raise ValueError('Aguarde um momento antes de localizar outra morada')
        _last_geocode = time.monotonic()
        # Keep a single request in flight to respect the public service rate limit.
        r = requests.get(os.environ.get('DESPENSA_GEOCODER_URL', 'https://nominatim.openstreetmap.org/search'), params={
            'q': query, 'format': 'jsonv2', 'limit': 5, 'countrycodes': 'pt,es',
        }, headers=HEADERS, timeout=(5, 12))
        r.raise_for_status()
        result = [dict(label=x['display_name'], coords=[float(x['lon']), float(x['lat'])]) for x in r.json()]
        if len(_cache) > 500:
            _cache.clear()
        _cache[key] = (time.monotonic(), result)
        return result


def road_matrix(profile, store_ids, day, mode='auto'):
    home = profile.get('home_coords')
    work = profile.get('work_coords')
    if not home:
        return None
    is_workday = date.fromisoformat(day).weekday() in profile.get('workdays', [])
    work_route = mode == 'work' or (mode == 'auto' and is_workday and bool(work))
    if work_route and not work:
        return None
    selected = [s for s in store_ids if profile['stores'].get(s, {}).get('coords')]
    if not selected or len(selected) > 8:
        return None
    origin = work if work_route else home
    points = [origin, home] + [profile['stores'][s]['coords'] for s in selected]
    coords = ';'.join(','.join(str(n) for n in point) for point in points)
    key = ('road', coords)
    with _lock:
        cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < 21600:
        data = cached[1]
    else:
        response = requests.get(os.environ.get('DESPENSA_ROUTER_URL', 'https://router.project-osrm.org').rstrip('/') + '/table/v1/driving/' + coords,
            params={'annotations': 'distance,duration'}, headers=HEADERS, timeout=(5, 12))
        response.raise_for_status()
        data = response.json()
        if data.get('code') != 'Ok':
            raise ValueError('Não foi possível obter distâncias rodoviárias')
        with _lock:
            _cache[key] = (time.monotonic(), data)
    return dict(ids={sid: i+2 for i, sid in enumerate(selected)}, distances=data['distances'], durations=data['durations'],
        base='work' if work_route else 'home')


def distance_for(stores, matrix):
    if not matrix or any(s not in matrix['ids'] for s in stores):
        return None
    distances, durations = matrix['distances'], matrix['durations']
    if distances[0][1] is None:
        return None
    best = None
    for order in itertools.permutations(stores):
        nodes = [0] + [matrix['ids'][s] for s in order] + [1]
        legs = list(zip(nodes, nodes[1:]))
        if any(distances[a][b] is None or durations[a][b] is None for a, b in legs):
            continue
        meters = max(0, sum(distances[a][b] for a, b in legs) - distances[0][1])
        minutes = max(0, sum(durations[a][b] for a, b in legs) - durations[0][1]) / 60
        if best is None or meters < best['meters']:
            best = dict(meters=meters, km=round(meters/1000, 2), extra_minutes=round(minutes), order=list(order), base=matrix['base'])
    return best
