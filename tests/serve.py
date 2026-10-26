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
