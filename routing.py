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
HEADERS = {'User-Agent': 'Despensa/0.3 (+https://github.com/hubertdungen/Despensa; self-hosted grocery planner)'}


def geocode(query):
    global _last_geocode
    query = query.strip()[:300]
    if len(query) < 4:
        raise ValueError('Indique uma morada ou localização mais completa')
    key = ('geo', query.casefold())
    with _lock:
        if key in _cache:
            return _cache[key][1]
        delay = 1.1 - (time.monotonic() - _last_geocode)
        if delay > 0:
            time.sleep(delay)
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


def table(points):
    if not 2 <= len(points) <= 32:
        raise ValueError('Número de localizações inválido')
    coords = ';'.join(','.join(str(n) for n in point) for point in points)
    key = ('road', coords)
    with _lock:
        cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < 21600:
        return cached[1]
    response = requests.get(os.environ.get('DESPENSA_ROUTER_URL', 'https://router.project-osrm.org').rstrip('/') + '/table/v1/driving/' + coords,
        params={'annotations':'distance,duration'},headers=HEADERS,timeout=(5,12))
    response.raise_for_status()
    data=response.json()
    if data.get('code')!='Ok':
        raise ValueError('Não foi possível obter distâncias rodoviárias')
    with _lock:
        if len(_cache)>500:
            _cache.clear()
        _cache[key]=(time.monotonic(),data)
    return data


def road_matrix(profile, store_ids, day, mode='auto', branches=None):
    home = profile.get('home_coords')
    work = profile.get('work_coords')
    if not home:
        return None
    is_workday = date.fromisoformat(day).weekday() in profile.get('workdays', [])
    work_route = mode == 'work' or (mode == 'auto' and is_workday and bool(work))
    if work_route and not work:
        return None
    selected = store_ids[:8]
    if not selected:
        return None
    origin = work if work_route else home
    points, ids, places = [origin, home], {}, {}
    for sid in selected:
        explicit = profile['stores'].get(sid, {})
        options = [dict(store=sid,coords=explicit['coords'],name=explicit.get('branch_name') or sid,address=explicit.get('address',''),id=explicit.get('branch_id') or 'saved:'+sid,source='saved')] if explicit.get('coords') else [s for s in (branches or []) if s['store']==sid]
        options.sort(key=lambda s: s.get('detour_km' if work_route else 'home_km') if s.get('detour_km' if work_route else 'home_km') is not None else 1e9)
        for option in options[:3]:
            index=len(points)
            ids.setdefault(sid,[]).append(index)
            points.append(option['coords'])
            places[index]=option
    if len(points)==2:
        return None
    data=table(points)
    return dict(ids=ids,places=places,distances=data['distances'],durations=data['durations'],base='work' if work_route else 'home',points=points)


def distance_for(stores, matrix):
    if not matrix or any(s not in matrix['ids'] for s in stores):
        return None
    distances, durations = matrix['distances'], matrix['durations']
    if distances[0][1] is None:
        return None
    best = None
    for order in itertools.permutations(stores):
        options = [matrix['ids'][s] if isinstance(matrix['ids'][s],list) else [matrix['ids'][s]] for s in order]
        for chosen in itertools.product(*options):
            nodes = [0] + list(chosen) + [1]
            legs = list(zip(nodes, nodes[1:]))
            if any(distances[a][b] is None or durations[a][b] is None for a, b in legs):
                continue
            total_meters=sum(distances[a][b] for a,b in legs)
            total_seconds=sum(durations[a][b] for a,b in legs)
            meters = max(0, total_meters - distances[0][1])
            minutes = max(0, total_seconds - durations[0][1]) / 60
            if best is None or (meters,total_seconds,total_meters) < (best['meters'],best['_seconds'],best['_total_meters']):
                best = dict(meters=meters,km=round(meters/1000,2),extra_minutes=round(minutes),_seconds=total_seconds,_total_meters=total_meters,
                    total_km=round(total_meters/1000,2),base_km=round(distances[0][1]/1000,2),total_minutes=round(total_seconds/60),order=list(order),
                    stops=[matrix.get('places',{}).get(i,{'store':s}) for i,s in zip(chosen,order)],base=matrix['base'],
                    coordinates=[matrix['points'][i] for i in nodes] if matrix.get('points') else [],provider='OSRM',traffic='unavailable')
    if best:
        best.pop('_seconds');best.pop('_total_meters')
    return best
