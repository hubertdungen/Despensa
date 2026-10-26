"""Discover retailer and OSM supermarket branches around both saved locations."""
import math
import os
import threading
import time
import requests
from catalog import fold, STORE_MAP
from routing import HEADERS, table
from store_locations import official_locations

_cache = {}
_lock = threading.Lock()


def haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, [*a, *b])
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def chain_for(tags, country):
    name = fold(' '.join(tags.get(k, '') for k in ('brand', 'name', 'operator')))
    brands = [('continente','continente'),('auchan','auchan' if country=='PT' else 'alcampo'),
        ('pingo doce','pingo-doce'),('lidl','lidl-pt' if country=='PT' else 'lidl-es'),
        ('aldi','aldi-pt' if country=='PT' else 'aldi-es'),('intermarche','intermarche'),('mercadona','mercadona-pt' if country=='PT' else 'mercadona-es'),
        ('makro','makro-pt' if country=='PT' else 'makro-es'),('recheio','recheio'),
        ('carrefour','carrefour'),('dia','dia'),('eroski','eroski'),('alcampo','alcampo')]
    return next((sid for brand,sid in brands if brand in name.split('  ') or (' '+brand+' ') in (' '+name+' ')
        if STORE_MAP[sid]['country']==country), None)


def discover(profile):
    origins = [profile.get('home_coords'), profile.get('work_coords')]
    points = [p for p in origins if p]
    if not points:
        return dict(stores=[], status='locations_required', distance_method='unavailable')
    countries = tuple(sorted(profile.get('countries', ['PT'])))
    radius = 6000
    key = (tuple(tuple(p) if p else None for p in origins), countries)
    with _lock:
        cached = _cache.get(key)
        if cached and time.monotonic()-cached[0] < (300 if cached[1]['status']=='unavailable' else 86400):
            return cached[1]
        # Serialize refreshes for the same small installation. No repeated searches on failures.
        stores = official_locations() if 'PT' in countries else []
        stores = [dict(s) for s in stores if any(haversine(p,s['coords'])<=radius/1000 for p in points)]
        for s in stores:
            s['home_km']=round(haversine(origins[0],s['coords']),2) if origins[0] else None
            s['work_km']=round(haversine(origins[1],s['coords']),2) if origins[1] else None
        # Public map data extends official locators to other chains. A failed
        # provider never discards verified branches from the retailer locators.
        osm_countries=list(countries)
        failed=False
        for country in osm_countries:
            clauses = ''.join(f'nwr(area.search)(around:{radius},{p[1]},{p[0]})["shop"~"^(supermarket|wholesale|convenience)$"];' for p in points)
            query = f'[out:json][timeout:18];area["ISO3166-1"="{country}"]["admin_level"="2"]->.search;({clauses});out center tags 250;'
            try:
                response = requests.get(os.environ.get('DESPENSA_OVERPASS_URL', 'https://overpass.private.coffee/api/interpreter'),
                    params={'data':query},headers=HEADERS,timeout=(4,18))
                response.raise_for_status()
                if len(response.content)>3_000_000:
                    raise ValueError('Pesquisa de lojas demasiado grande')
            except Exception:
                failed=True
                continue
            for element in response.json().get('elements', []):
                tags = element.get('tags', {})
                coords = element.get('center', element)
                if 'lat' not in coords or 'lon' not in coords:
                    continue
                point = [float(coords['lon']), float(coords['lat'])]
                sid = chain_for(tags, country)
                if not sid:
                    continue
                stores.append(dict(id=f'{element["type"]}:{element["id"]}', store=sid, country=country,
                    name=tags.get('name', STORE_MAP[sid]['name']), coords=point,
                    address=' '.join(tags.get(k,'') for k in ('addr:street','addr:housenumber','addr:postcode','addr:city')).strip(),
                    opening_hours=tags.get('opening_hours',''),
                    home_km=round(haversine(origins[0],point),2) if origins[0] else None,
                    work_km=round(haversine(origins[1],point),2) if origins[1] else None))
        # Preserve the closest branches of BOTH origins before imposing a bound.
        selected = {}
        for axis in ('home_km', 'work_km'):
            for store in sorted((s for s in stores if s[axis] is not None), key=lambda s:s[axis])[:12]:
                selected[store['id']] = store
        stores = list(selected.values())[:24]
        method = 'straight_line'
        try:
            home = origins[0] or origins[1]
            work = origins[1] or home
            matrix = table([home, work] + [s['coords'] for s in stores]) if stores else None
            if matrix:
                d = matrix['distances']
                for i, store in enumerate(stores, 2):
                    store['home_km'] = round(d[0][i]/1000,2) if origins[0] and d[0][i] is not None else None
                    store['work_km'] = round(d[1][i]/1000,2) if origins[1] and d[1][i] is not None else None
                    store['detour_km'] = round(max(0,d[1][i]+d[i][0]-d[1][0])/1000,2) if all(d[a][b] is not None for a,b in [(1,i),(i,0),(1,0)]) else None
                method = 'road'
        except Exception:
            pass
        for s in stores:
            s['enabled'] = bool(profile.get('stores',{}).get(s['store'],{}).get('enabled'))
        result = dict(stores=stores,status='unavailable' if failed and not stores else 'ok',distance_method=method, radius_km=radius/1000,
            partial=failed or not osm_countries, sources=sorted({s.get('source','OpenStreetMap') for s in stores}),
            near_home=sorted([s['id'] for s in stores if s['home_km'] is not None],key=lambda sid:next(s['home_km'] for s in stores if s['id']==sid)),
            near_work=sorted([s['id'] for s in stores if s['work_km'] is not None],key=lambda sid:next(s['work_km'] for s in stores if s['id']==sid)))
        if len(_cache)>100:
            _cache.clear()
        _cache[key] = (time.monotonic(),result)
        return result
