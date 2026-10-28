"""Optional live road traffic and bounded, attributed public-transport journeys."""
import hashlib
import json
import os
import threading
import time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from mobility_sources import AGENT

_cache={};_lock=threading.Lock()


def departure(day,clock='',country='PT',zone_name=None):
    zone=ZoneInfo(zone_name or ('Europe/Madrid' if country=='ES' else 'Europe/Lisbon'))
    now=datetime.now(zone)
    if not clock and day==now.date().isoformat():return now
    clock=clock or '10:00'
    value=datetime.fromisoformat(day+'T'+clock).replace(tzinfo=zone)
    if value<now-timedelta(minutes=5):raise ValueError('Escolha uma hora de partida atual ou futura')
    return value


def traffic_key():
    value=os.environ.get('DESPENSA_TOMTOM_KEY','')
    path=os.environ.get('DESPENSA_TOMTOM_KEY_FILE')
    if path:
        try:value=Path(path).read_text().strip()
        except OSError:return ''
    return value.strip()


def traffic_summary(points,when):
    key=traffic_key()
    if not key:return None
    coords=':'.join(f'{p[1]},{p[0]}' for p in points)
    cache_key=('traffic',coords,when.isoformat()[:16])
    with _lock:hit=_cache.get(cache_key)
    if hit and time.monotonic()-hit[0]<300:return hit[1]
    try:
        r=requests.get('https://api.tomtom.com/routing/1/calculateRoute/'+coords+'/json',
            params=dict(key=key,traffic='true',departAt='now' if abs((when-datetime.now(timezone.utc)).total_seconds())<60 else when.replace(microsecond=0).isoformat(),routeType='fastest',travelMode='car',
                computeTravelTimeFor='all',routeRepresentation='summaryOnly'),headers={'User-Agent':AGENT},timeout=(4,12))
        r.raise_for_status();summary=r.json()['routes'][0]['summary']
        result=dict(meters=float(summary['lengthInMeters']),seconds=float(summary['travelTimeInSeconds']),
            delay_seconds=float(summary.get('trafficDelayInSeconds',0)),
            traffic='live' if abs((when-datetime.now(timezone.utc)).total_seconds())<900 else 'historic',
            source='TomTom',observed_at=datetime.now(timezone.utc).isoformat())
        if result['meters']<0 or result['seconds']<0:raise ValueError('Invalid traffic route')
    except (requests.RequestException,ValueError,KeyError,IndexError,TypeError):
        return None
    with _lock:
        if len(_cache)>512:_cache.clear()
        _cache[cache_key]=(time.monotonic(),result)
    return result


def enrich_traffic(route,when):
    points=route.get('coordinates')
    if not points:return route
    result=traffic_summary(points,when)
    if not result:return dict(route,traffic='unavailable')
    baseline=dict(meters=0,seconds=0) if points[0]==points[-1] else traffic_summary([points[0],points[-1]],when)
    return dict(route,total_km=round(result['meters']/1000,2),total_minutes=round(result['seconds']/60),
        km=round(max(0,result['meters']-(baseline['meters'] if baseline else 0))/1000,2) if baseline else None,
        base_km=round(baseline['meters']/1000,2) if baseline else None,
        extra_minutes=round(max(0,result['seconds']-baseline['seconds'])/60) if baseline else None,
        traffic=result['traffic'],traffic_delay_minutes=round(result['delay_seconds']/60),provider='TomTom',
        observed_at=result['observed_at'])


def transit_leg(folder,start,end,when):
    # MOTIS can misparse fractional/offset timestamps. Send whole UTC minutes
    # in RFC3339 Z form, rounding up so a past departure cannot be selected.
    requested=when.astimezone(timezone.utc)
    if requested.second or requested.microsecond:requested+=timedelta(minutes=1)
    stamp=requested.replace(second=0,microsecond=0).isoformat().replace('+00:00','Z')
    cache_key=('transit',tuple(start),tuple(end),stamp)
    with _lock:
        hit=_cache.get(cache_key)
        if hit and time.monotonic()-hit[0]<900:return hit[1]
        # Budget persists over restarts; route coordinates stay only in memory.
        path=Path(folder)/'transit-usage.json'
        try:usage=json.loads(path.read_text())
        except (OSError,ValueError):usage={}
        today=datetime.now(timezone.utc).date().isoformat()
        count=usage.get('count',0) if usage.get('day')==today else 0
        if count>=200:raise ValueError('Limite diário do serviço de transportes atingido')
        path.write_text(json.dumps(dict(day=today,count=count+1)))
    base=os.environ.get('DESPENSA_TRANSIT_URL','https://api.transitous.org').rstrip('/')
    try:
        r=requests.get(base+'/api/v6/plan',params=dict(fromPlace=f'{start[1]},{start[0]}',toPlace=f'{end[1]},{end[0]}',
            time=stamp,arriveBy='false',transitModes='TRANSIT',directModes='WALK',numItineraries=1,maxItineraries=1,
            timetableView='false',maxTransfers=3),headers={'User-Agent':AGENT},timeout=(4,15))
        r.raise_for_status();data=r.json()
        options=(data.get('itineraries') or [])+(data.get('direct') or [])
        valid=[]
        for option in options:
            arrival=datetime.fromisoformat(option['endTime'].replace('Z','+00:00'))
            if not when<=arrival<=when+timedelta(hours=24):continue
            legs=option.get('legs',[])
            segments=[dict(mode=leg['mode'],line=leg.get('routeShortName') or leg.get('routeLongName') or '',
                start=leg['startTime'],end=leg['endTime'],realtime=bool(leg.get('realTime')),duration=leg['duration'],
                distance=leg.get('distance')) for leg in legs]
            valid.append(dict(arrival=arrival.isoformat(),minutes=round((arrival-when).total_seconds()/60),
                boardings=sum(s['mode'] not in ('WALK','FOOTPATH') for s in segments),legs=segments,
                realtime=any(s['realtime'] for s in segments),distance=sum(s['distance'] for s in segments) if all(s['distance'] is not None for s in segments) else None))
        if not valid:raise ValueError('Sem ligação de transportes para a hora escolhida')
        result=min(valid,key=lambda x:x['arrival'])
    except (requests.RequestException,KeyError,IndexError,TypeError,ValueError):
        raise ValueError('Não foi possível confirmar transportes para este trajeto e horário') from None
    with _lock:
        if len(_cache)>512:_cache.clear()
        _cache[cache_key]=(time.monotonic(),result)
    return result


def enrich_transit(folder,route,when,stop_minutes):
    points=route.get('coordinates')
    if not points:return dict(route,verified=False,total_km=None,total_minutes=None)
    current=when;segments=[];boardings=0;distance=0;distance_known=True
    try:
        for index,(start,end) in enumerate(zip(points,points[1:])):
            leg=transit_leg(folder,start,end,current);segments.append(leg);boardings+=leg['boardings']
            current=datetime.fromisoformat(leg['arrival'])
            if leg['distance'] is None:distance_known=False
            else:distance+=leg['distance']
            if index<len(points)-2:current+=timedelta(minutes=stop_minutes)
        return dict(route,provider='Transitous',traffic='not_applicable',verified=True,
            total_km=round(distance/1000,2) if distance_known else None,total_minutes=round((current-when).total_seconds()/60),
            base_km=None,km=None,extra_minutes=None,transit_legs=segments,boardings=boardings,
            realtime=any(s['realtime'] for s in segments),includes_shopping=True,
            observed_at=datetime.now(timezone.utc).isoformat())
    except ValueError:
        return dict(route,provider='Transitous',verified=False,total_km=None,total_minutes=None,
            base_km=None,km=None,extra_minutes=None,transit_error='unavailable')
