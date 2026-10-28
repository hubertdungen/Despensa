"""Costs, provenance, asynchronous selection and private journey state."""
import copy
import json
import threading
import time
from datetime import date,datetime,timedelta,timezone

import pytest
import journey
import mobility_sources as sources
import plan_service
import travel
from app import create_app,default_profile


def test_car_charges_whole_journey_even_when_commute_detour_is_zero():
    p=default_profile();p['mobility'].update(consumption=6,fuel_quote=dict(unit_price=1.8,source='fixture'),parking_per_stop=1,tolls=2,stop_minutes=15,time_value=12)
    cost=travel.estimate(p,dict(total_km=10,km=0,total_minutes=20),2)
    assert cost['fuel_cents']==108
    assert cost['travel_cents']==508
    assert cost['extra_travel_cents']==400
    assert cost['total_minutes']==50
    assert cost['time_cost_cents']==1000 and cost['decision_cents']==1508


def test_missing_rate_is_explicit_manual_estimate_and_unknown_route_not_free():
    p=default_profile();p['cost_per_km']=.25
    assert travel.estimate(p,None,1)['travel_cents'] is None
    result=travel.estimate(p,dict(total_km=8,km=0,total_minutes=12),1)
    assert result['travel_method']=='manual_km' and result['travel_cents']==200
    assert result['extra_travel_cents']==0


def test_transit_requires_schedules_and_uses_declared_fare_or_pass():
    p=default_profile();p['mobility'].update(mode='transit',transit_ticket=1.8)
    assert travel.estimate(p,dict(total_km=10,total_minutes=20),2)['travel_cents'] is None
    r=dict(verified=True,boardings=3,total_minutes=80,stops=[{},{}])
    cost=travel.estimate(p,r,2)
    assert cost['travel_cents']==540 and cost['total_minutes']==80
    p['mobility']['transit_pass']=True
    assert travel.estimate(p,r,2)['travel_cents']==0


def option(n,basket,km,complete=True):
    return dict(id=str(n),stores=list('abcd')[:n],basket_cents=basket,coverage=4 if complete else 3,total_items=4,complete=complete,
                route=dict(total_km=km,km=km,total_minutes=10) if km is not None else None)


def test_up_to_four_shops_lose_to_one_when_extra_driving_exceeds_product_saving():
    p=default_profile();p['cost_per_km']=.2
    result=dict(plans=[option(1,10000,2),option(2,9900,20),option(3,9850,30),option(4,9800,40)])
    travel.summarize(result,p)
    assert result['plans'][0]['id']=='1' and result['plans'][0]['recommended']
    assert [f['stops'] for f in result['frontier']]==[1,2,3,4]
    assert result['plans'][1]['saving_cents']<0


def test_true_net_saving_compares_only_same_complete_basket():
    p=default_profile();p['cost_per_km']=.2
    result=dict(plans=[option(1,100,1,False),option(2,10000,5),option(3,9500,10),option(4,9000,None)])
    travel.summarize(result,p)
    best=result['plans'][0]
    assert best['id']=='3' and best['saving_cents']==400 and best['baseline_stops']==2
    assert next(o for o in result['plans'] if o['id']=='1')['saving_cents'] is None
    assert next(o for o in result['plans'] if o['id']=='4')['saving_cents'] is None


def test_four_shop_frontier_survives_many_cheaper_two_shop_variants():
    p=default_profile()
    plans=[dict(option(2,100+i,1),id='two'+str(i)) for i in range(30)]+[option(1,200,1),option(3,300,1),option(4,400,1)]
    result=travel.summarize(dict(plans=plans),p)
    assert len(result['plans'])==12
    assert {len(o['stores']) for o in result['plans']}=={1,2,3,4}
    assert all(f['plan_id'] in {o['id'] for o in result['plans']} for f in result['frontier'])


def test_published_vehicle_consumption_is_canonical_and_real_value_can_override(monkeypatch,tmp_path):
    v=dict(id='ademe:engine',label='Clio verified engine',consumption=4.637,fuel='diesel')
    monkeypatch.setattr(travel,'get_vehicle',lambda folder,identifier:dict(v))
    m=travel.validate(dict(vehicle_id=v['id'],consumption_source='catalogue',consumption=1,fuel='petrol95'),folder=tmp_path)
    assert m['consumption']==4.637 and m['fuel']=='diesel'
    m=travel.validate(dict(consumption_source='manual',consumption=5.2),m,tmp_path)
    assert m['consumption']==5.2
    m=travel.validate(dict(vehicle_id='',vehicle_label='My older car'),m,tmp_path)
    assert m['vehicle'] is None and m['vehicle_label']=='My older car'
    for bad in [dict(consumption=float('nan')),dict(time_value=-1),dict(mode='teleport'),dict(unit_price=0)]:
        with pytest.raises(ValueError):travel.validate(bad,folder=tmp_path)


def test_ademe_does_not_guess_old_year_or_plugin_fuel_consumption(monkeypatch,tmp_path):
    row=dict(_id='engine',Marque='RENAULT',Description_Commerciale='CLIO',Energie='GAZOLE',Conso_vitesse_mixte_Min=4.1,Conso_vitesse_mixte_Max=4.637)
    v=sources.ademe_vehicle(row)
    assert v['consumption']==4.637 and v['year'] is None
    assert sources.ademe_vehicle(dict(row,Energie='ESS+ELEC HR')) is None
    monkeypatch.setattr(sources,'vehicle_catalog',lambda f:pytest.fail('Do not match current ADEME vehicle to requested old year'))
    monkeypatch.setattr(sources,'epa_search',lambda query,year:[])
    assert sources.search_vehicles(tmp_path,'Renault Clio',2003)['status']=='no_verified_year'


def test_fuel_sources_parse_decimal_prices_dates_and_distinguish_averages():
    today=date(2026,10,28)
    rows=[dict(TipoCombustivel='Gasolina simples 95',UnidadeMedida='litro',Data='2026-10-27',PrecoMedioC4='1,8356 €'),
          dict(TipoCombustivel='Gasolina simples 95',UnidadeMedida='litro',Data='2026-10-29',PrecoMedioC4='0,5000 €')]
    q=sources.parse_pt_prices(dict(resultado=rows),today)['petrol95']
    assert q['unit_price']==1.8356 and q['observed_on']=='2026-10-27' and 'ponderado' in q['source']
    data=dict(Fecha='28/10/2026 12:00:00',ListaEESSPrecio=[{'Precio Gasoleo A':'1,900'},{'Precio Gasoleo A':'2,100'},{'Precio Gasoleo A':''}])
    q=sources.parse_es_prices(data,today)['diesel']
    assert q['unit_price']==2 and q['station_count']==2 and 'simples' in q['source']
    with pytest.raises(ValueError):sources.parse_es_prices(dict(data,Fecha='01/10/2026 12:00:00'),today)


def test_source_cache_uses_bounded_stale_fallback_and_rejects_old_quotes(tmp_path,monkeypatch):
    sources.cached(tmp_path,'quote',lambda:dict(value=1),ttl=0)
    def unavailable():raise ValueError('Unavailable')
    assert sources.cached(tmp_path,'quote',unavailable,ttl=0)[1]
    with pytest.raises(ValueError):sources.cached(tmp_path,'quote',unavailable,ttl=0,max_age=0)
    old=dict(prices={'diesel':dict(observed_on=(date.today()-timedelta(days=8)).isoformat())})
    monkeypatch.setattr(sources,'cached',lambda *args,**kwargs:(old['prices'],False))
    with pytest.raises(ValueError):sources.fuel_prices(tmp_path,'PT')


def test_dgeg_uses_iso_date_query_and_official_dynamic_fuel_ids(monkeypatch,tmp_path):
    calls=[]
    def fetch(url,params=None,**kwargs):
        calls.append((url,params))
        if url.endswith('GetTiposCombustiveis'):return dict(resultado=[dict(Id=3201,Descritivo='Gasolina simples 95')])
        return dict(resultado=[dict(TipoCombustivel='Gasolina simples 95',UnidadeMedida='litro',Data=date.today().isoformat(),PrecoMedioC4='1,8765 €')])
    monkeypatch.setattr(sources,'read_json',fetch)
    assert sources.fuel_prices(tmp_path,'PT')['prices']['petrol95']['unit_price']==1.8765
    assert calls[1][1]['dataFim']==date.today().isoformat() and calls[1][1]['idsTiposComb']=='3201'


def test_transit_legs_include_store_dwell_and_never_retain_car_distance(monkeypatch,tmp_path):
    when=datetime.now(timezone.utc);times=[]
    def leg(folder,start,end,stamp):
        times.append(stamp)
        return dict(arrival=(stamp+timedelta(minutes=10)).isoformat(),boardings=1,distance=2000,realtime=False,legs=[])
    monkeypatch.setattr(journey,'transit_leg',leg)
    route=dict(coordinates=[[0,0],[1,1],[2,2],[0,0]],stops=[{},{}],total_km=99,total_minutes=5)
    result=journey.enrich_transit(tmp_path,route,when,15)
    assert result['total_minutes']==60 and result['total_km']==6 and result['boardings']==3
    assert times[1]-times[0]==timedelta(minutes=25)
    def fail(*args):raise ValueError('Unavailable')
    monkeypatch.setattr(journey,'transit_leg',fail)
    result=journey.enrich_transit(tmp_path,route,when,15)
    assert not result['verified'] and result['total_km'] is None and result['total_minutes'] is None


def test_traffic_changes_full_cost_and_provenance_only_when_provider_responds(monkeypatch):
    monkeypatch.setattr(journey,'traffic_summary',lambda points,when:dict(meters=12000 if len(points)>2 else 8000,seconds=1200 if len(points)>2 else 600,delay_seconds=180,traffic='live',observed_at='now'))
    route=dict(coordinates=[[0,0],[1,1],[2,2]],total_km=10,km=0,total_minutes=10)
    result=journey.enrich_traffic(route,datetime.now(timezone.utc))
    assert result['total_km']==12 and result['km']==4 and result['traffic_delay_minutes']==3 and result['provider']=='TomTom'
    monkeypatch.setattr(journey,'traffic_summary',lambda *a:None)
    assert journey.enrich_traffic(route,datetime.now(timezone.utc))['traffic']=='unavailable'


def register(client,name):
    assert client.post('/api/auth/register',json=dict(username=name,password='temporary-password-2026')).status_code==200


def test_async_progress_coalescing_selection_and_cross_user_isolation(tmp_path,monkeypatch):
    app=create_app(tmp_path,testing=True);a=app.test_client();b=app.test_client();register(a,'alice');register(b,'bob')
    entered=threading.Event();release=threading.Event()
    original=app.planning.calculate
    def calculate(uid,month,params,report):
        report('locations');entered.set();assert release.wait(5)
        return dict(plans=[dict(id='canonical',stores=['auchan'],selections=[],basket_cents=100,total_cents=200)],calculated_at=time.time(),departure=datetime.now(timezone.utc).isoformat())
    monkeypatch.setattr(app.planning,'calculate',calculate)
    month=date.today().strftime('%Y-%m');payload=dict(month=month,day=date.today().isoformat(),max_stops=4)
    try:
        r=a.post('/api/plans',json=payload);assert r.status_code==202
        identifier=r.json['run']['id'];assert entered.wait(2)
        assert a.get('/api/plans/'+identifier).json['run']['phase']=='locations'
        assert a.get('/api/me').status_code==200
        assert a.post('/api/plans',json=payload).json['run']['id']==identifier
        assert b.get('/api/plans/'+identifier).status_code==404
        assert b.post('/api/plans/select',json=dict(run_id=identifier,plan_id='canonical')).status_code==400
    finally:release.set()
    for _ in range(100):
        run=a.get('/api/plans/'+identifier).json['run']
        if run['status']=='ready':break
        time.sleep(.02)
    assert run['status']=='ready'
    assert a.post('/api/plans/select',json=dict(run_id=identifier,plan_id='forged')).status_code==400
    assert a.post('/api/plans/select',json=dict(run_id=identifier,plan_id='canonical')).status_code==200
    assert a.get('/api/plans/selected?month='+month).json['selected']['plan']['total_cents']==200
    assert b.get('/api/plans/selected?month='+month).json['selected'] is None
    assert a.get('/api/export').json['selected_plans'][0]['plan']['id']=='canonical'
    a.put('/api/profile',json=dict(mobility=dict(consumption=7)))
    assert a.get('/api/plans/selected?month='+month).json['selected']['stale']
    assert a.post('/api/plans/select',json=dict(run_id=identifier,plan_id='canonical')).status_code==400
    assert a.delete('/api/plans/selected',json=dict(month=month)).status_code==200
    assert a.get('/api/plans/selected?month='+month).json['selected'] is None
    app.planning.pool.shutdown()


def test_saved_branch_survives_profile_and_is_used_even_when_discovery_fails(tmp_path,monkeypatch):
    app=create_app(tmp_path,testing=True);c=app.test_client();register(c,'branches')
    setting=dict(address='Rua de teste',coords=[-9.1,38.7],branch_id='official:123',branch_name='Auchan Teste')
    assert c.put('/api/profile',json=dict(stores=dict(auchan=setting))).status_code==200
    profile=c.get('/api/me').json['profile'];assert profile['stores']['auchan']['branch_name']=='Auchan Teste'
    import routing
    monkeypatch.setattr(routing,'table',lambda points:dict(distances=[[0]*len(points)]*len(points),durations=[[0]*len(points)]*len(points)))
    profile['home_coords']=[-9.2,38.7]
    road=routing.road_matrix(profile,['auchan'],date.today().isoformat(),mode='home',branches=[])
    assert road['places'][2]['address']=='Rua de teste' and road['places'][2]['name']=='Auchan Teste'
    app.planning.pool.shutdown()


def test_epa_string_false_is_not_plugin_and_electric_uses_energy_not_mpg(monkeypatch,tmp_path):
    row=dict(make='Tesla',model='Model 3',year='2024',fuelType1='Electricity',phevBlended='false',combE='25.4472',comb08='132')
    monkeypatch.setattr(sources,'read_json',lambda *args,**kwargs:row)
    vehicle=sources.get_vehicle(tmp_path,'epa:123')
    assert vehicle['fuel']=='electric' and vehicle['consumption']==15.812
    row['phevBlended']='true'
    with pytest.raises(ValueError):sources.get_vehicle(tmp_path,'epa:124')


def test_home_traffic_baseline_is_zero_without_an_invalid_origin_equals_destination_query(monkeypatch):
    calls=[]
    def traffic(points,when):
        calls.append(points);return dict(meters=10000,seconds=600,traffic='live',observed_at='now',delay_seconds=0)
    monkeypatch.setattr(journey,'traffic_summary',traffic)
    result=journey.enrich_traffic(dict(coordinates=[[0,0],[1,1],[0,0]]),datetime.now(timezone.utc))
    assert len(calls)==1 and result['base_km']==0 and result['km']==10


def test_missing_commute_baseline_does_not_become_a_free_detour():
    p=default_profile();p['mobility'].update(consumption=6,fuel_quote=dict(unit_price=1.8))
    r=travel.estimate(p,dict(total_km=10,total_minutes=20,km=None),1)
    assert r['travel_cents']==108 and r['extra_travel_cents'] is None


def test_changed_saved_address_invalidates_old_point_and_branch(tmp_path):
    app=create_app(tmp_path,testing=True);c=app.test_client();register(c,'address-change')
    c.put('/api/profile',json=dict(stores=dict(auchan=dict(address='Old',coords=[-9,38],branch_name='Old branch',branch_id='old'))))
    p=c.put('/api/profile',json=dict(stores=dict(auchan=dict(address='New')))).json['profile']['stores']['auchan']
    assert p['address']=='New' and p['coords'] is None and p['branch_id']==''
    app.planning.pool.shutdown()


def test_checking_a_purchase_preserves_selected_itinerary_but_quantity_changes_invalidate_it(tmp_path):
    app=create_app(tmp_path,testing=True);c=app.test_client();register(c,'shopping-progress')
    month=date.today().strftime('%Y-%m')
    item=c.post('/api/items',json=dict(name='Leite',quantity=1,unit='l',month=month)).json['item']
    uid=c.get('/api/me').json['user']['id'];params=dict(day=date.today().isoformat(),route='home')
    before=app.planning.selection_signature(uid,month,params)
    computing=app.planning.user_signature(uid,month,params)
    c.patch('/api/items/'+item['id'],json=dict(checked=True))
    assert app.planning.selection_signature(uid,month,params)==before
    assert app.planning.user_signature(uid,month,params)!=computing
    c.patch('/api/items/'+item['id'],json=dict(quantity=2))
    assert app.planning.selection_signature(uid,month,params)!=before
    app.planning.pool.shutdown()


def test_transit_request_normalizes_offset_and_fractional_time_without_departing_in_past(monkeypatch,tmp_path):
    from zoneinfo import ZoneInfo
    when=datetime(2026,10,28,15,12,34,123456,tzinfo=ZoneInfo('Europe/Madrid'))
    capture={}
    class Response:
        def raise_for_status(self):pass
        def json(self):
            return dict(itineraries=[dict(startTime='2026-10-28T14:13:00Z',endTime='2026-10-28T14:43:00Z',legs=[dict(mode='BUS',routeShortName='1',startTime='2026-10-28T14:13:00Z',endTime='2026-10-28T14:43:00Z',duration=1800,distance=5000)])])
    def get(url,**kwargs):capture.update(kwargs);return Response()
    monkeypatch.setattr(journey.requests,'get',get)
    journey._cache.clear()
    result=journey.transit_leg(tmp_path,[-3.1,40.1],[-3.2,40.2],when)
    assert capture['params']['time']=='2026-10-28T14:13:00Z'
    assert capture['params']['arriveBy']=='false' and result['boardings']==1
    assert result['minutes']==30 and result['distance']==5000


def test_fuel_quote_is_not_presented_as_used_when_manual_km_fallback_priced_the_trip():
    p=default_profile();p['mobility']['fuel_quote']=dict(unit_price=1.8)
    result=travel.estimate(p,dict(total_km=10,km=0,total_minutes=20),1)
    assert result['travel_method']=='manual_km' and result['fuel_quote'] is None
