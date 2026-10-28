"""Isolated browser-test server: temporary database, no worker, no retailer requests."""
import sys
import tempfile
import os
import json
import threading
from datetime import datetime, date, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from waitress import serve
from app import create_app
import nearby
import plan_service
import travel

# Browser scenarios exercise forms and state; map-provider behaviour has its own
# Python tests. Never send these fixture coordinates to public services.
def fixture_nearby(profile):
    rows=[dict(id='branch:auchan:1',store='auchan',name='Auchan Teste Centro',address='Rua do Teste 1',country='PT',coords=[-9.11,38.71],home_km=1,work_km=2,detour_km=.5),
          dict(id='branch:auchan:2',store='auchan',name='Auchan Teste Norte',address='Avenida do Teste 22',country='PT',coords=[-9.12,38.72],home_km=2,work_km=1,detour_km=.5),
          dict(id='branch:continente:1',store='continente',name='Continente Teste',address='Praça do Teste 3',country='PT',coords=[-9.13,38.73],home_km=3,work_km=3,detour_km=1)]
    return dict(stores=rows if profile.get('home_coords') else [],status='ok' if profile.get('home_coords') or profile.get('work_coords') else 'locations_required',distance_method='road')
nearby.discover=fixture_nearby
# Public sources stay outside the deterministic browser fixture.
plan_service.resolve=lambda profile,folder:dict(profile.get('mobility',travel.defaults()),fuel_quote={'unit_price':1.8,'source':'Test fixture','observed_on':date.today().isoformat()})
import routing
_original_matrix=routing.road_matrix
def fixture_matrix(profile,ids,day,mode='auto',branches=None):
    points=[]
    original=routing.table
    def table(nodes):
        n=len(nodes)
        return dict(distances=[[0 if i==j else 2000 for j in range(n)] for i in range(n)],durations=[[0 if i==j else 300 for j in range(n)] for i in range(n)])
    routing.table=table
    try:return _original_matrix(profile,ids,day,mode,branches=branches)
    finally:routing.table=original
plan_service.road_matrix=fixture_matrix
fixture_vehicle=dict(id='ademe:fixture',label='Renault Clio 1.5 dCi Teste',consumption=4.637,fuel='diesel',unit='L/100 km',source='ADEME fixture',source_updated_at=date.today().isoformat())
travel.get_vehicle=lambda folder,identifier:dict(fixture_vehicle) if identifier=='ademe:fixture' else (_ for _ in ()).throw(ValueError('Fixture vehicle not found'))

with tempfile.TemporaryDirectory(prefix='despensa-e2e-') as folder:
    root=Path(folder)
    local=create_app(root/'local',testing=True)
    def seed(app):
        with app.database() as db:
            for sid,price in [('continente',100),('auchan',90)]:
                o=dict(id='test:'+sid,store=sid,country='PT',name='Leite UHT meio gordo',size=1,unit='l',
                    price_cents=price,condition='public',observed_at=datetime.now(timezone.utc).isoformat(),
                    vat_included=True,pack='1 l',source_url='',source_kind='automatic',location='Test fixture')
                db.execute('INSERT INTO offers VALUES(?,?,?,?)',(o['id'],'',sid,json.dumps(o)))
            for i in range(45):
                o=dict(id=f'page:{i}',store='continente',country='PT',name=f'Produto revisão {i:02d}',brand='Marca Radar',
                    size=1,unit='un',price_cents=200+i,condition='public',vat_included=True,pack='1 un',
                    observed_at=datetime.now(timezone.utc).isoformat(),source_url='',source_kind='automatic')
                db.execute('INSERT INTO offers VALUES(?,?,?,?)',(o['id'],'',o['store'],json.dumps(o)))
            for sid,price,condition in [('continente',119,'public'),('aldi-pt',95,'public'),('lidl-pt',99,'card')]:
                o=dict(id='banana:'+sid,store=sid,country='PT',name='Banana',size=1,unit='kg',
                    price_cents=price,condition=condition,observed_at=datetime.now(timezone.utc).isoformat(),
                    vat_included=True,pack='1 kg · venda a peso',variable_weight=True,source_url='',source_kind='automatic')
                db.execute('INSERT INTO offers VALUES(?,?,?,?)',(o['id'],'',sid,json.dumps(o)))
            o=dict(id='water:auchan',store='auchan',country='PT',name='ÁGUA MINERAL LUSO GARRAFÃO 7L',size=7,unit='l',
                price_cents=199,condition='public',observed_at=datetime.now(timezone.utc).isoformat(),
                vat_included=True,pack='7 l',source_url='',source_kind='automatic')
            db.execute('INSERT INTO offers VALUES(?,?,?,?)',(o['id'],'',o['store'],json.dumps(o)))
            for oid,name,brand,pack,size in [('delta-ground','Café Moído Brasil','Delta','220 g',.22),('delta-beans','Café em Grão Gold','Delta','500 g',.5),('fitness','Cereais Trigo e Aveia Integral','Fitness','625 g',.625),('fitness-fibre','Cereais Fitness Mel Fibra','Fitness','310 g',.31)]:
                o=dict(id=oid,store='auchan',country='PT',name=name,brand=brand,size=size,unit='kg',pack=pack,
                    price_cents=369,condition='public',vat_included=True,observed_at=datetime.now(timezone.utc).isoformat(),
                    category='Mercearia / Cereais Linha e Fibra' if oid=='fitness-fibre' else 'Café' if oid.startswith('delta') else '',source_url='',source_kind='automatic')
                db.execute('INSERT INTO offers VALUES(?,?,?,?)',(oid,'',o['store'],json.dumps(o)))
    seed(local)
    secret=root/'proxy-secret';secret.write_text('browser-test-proxy-secret-'*3)
    os.environ.update(DESPENSA_AUTH_MODE='proxy',DESPENSA_PROXY_SECRET_FILE=str(secret),
        DESPENSA_LOGIN_URL='https://shopping.example.org/',DESPENSA_LOGOUT_URL='https://auth.example.org/logout')
    proxy=create_app(root/'proxy',testing=True);seed(proxy)
    h={'Remote-User':'browser-sso','X-Despensa-Proxy-Token':secret.read_text()}
    uid=proxy.test_client().get('/api/me',headers=h).json['user']['id']
    current=date.today().strftime('%Y-%m')
    next_month=f'{date.today().year+1}-01'
    snapshot=root/'budget.json'
    snapshot.write_text(json.dumps(dict(version=1,updated_at=datetime.now(timezone.utc).isoformat(),months={
        current:dict(amount_cents=30000,actual_cents=None,lines=[]),next_month:dict(amount_cents=42000,actual_cents=None,lines=[])})))
    os.environ.update(DESPENSA_RUMO_SNAPSHOT=str(snapshot),DESPENSA_RUMO_USER_IDS=uid)
    os.environ.pop('DESPENSA_AUTH_MODE');os.environ.pop('DESPENSA_PROXY_SECRET_FILE')
    threading.Thread(target=serve,args=(proxy,),kwargs=dict(host='127.0.0.1',port=38109,threads=6),daemon=True).start()
    serve(local,host='127.0.0.1',port=38108,threads=6)
