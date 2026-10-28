"""Despensa: personal grocery lists, observed prices and explainable shopping plans."""
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from decimal import InvalidOperation
from urllib.parse import urlsplit

from flask import Flask, g, jsonify, request, send_from_directory, Response
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from catalog import STORE_MAP, cents, fold, product_text
from planner import make_plan

from travel import defaults as travel_defaults

APP_VERSION = '0.6.0'
ROOT = Path(__file__).resolve().parent
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS profiles(user_id TEXT PRIMARY KEY,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS identities(provider TEXT NOT NULL,subject TEXT NOT NULL,user_id TEXT NOT NULL,PRIMARY KEY(provider,subject));
CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,month TEXT NOT NULL,data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS item_owner ON items(user_id,month);
CREATE TABLE IF NOT EXISTS offers(id TEXT PRIMARY KEY,user_id TEXT NOT NULL DEFAULT '',store TEXT NOT NULL,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS history(offer_id TEXT NOT NULL,observed TEXT NOT NULL,price INTEGER NOT NULL,PRIMARY KEY(offer_id,observed));
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT NOT NULL,created TEXT NOT NULL,finished TEXT,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS purchases(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,month TEXT NOT NULL,item_id TEXT NOT NULL,data TEXT NOT NULL,UNIQUE(user_id,item_id));
CREATE TABLE IF NOT EXISTS trips(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,month TEXT NOT NULL,data TEXT NOT NULL);
'''


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def default_profile():
    return dict(locale='pt-PT', countries=['PT'], budget=250, budget_source='auto', reference_store='', interval_hours=24, automatic=True,
        mobility=travel_defaults(),max_stops=4, cost_per_km=.20, home='', work='', home_coords=None, work_coords=None,
        workdays=[0, 1, 2, 3, 4], stores={s: dict(enabled=not STORE_MAP[s]['professional'], card=False,
        subscription=False, delivery_subscription=False, access=False, coupons=[], extra_km=None, address='', coords=None) for s in STORE_MAP})


def create_app(data_dir=None, testing=False):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=1_000_000, JSON_AS_ASCII=False)
    auth_mode = os.environ.get('DESPENSA_AUTH_MODE', 'local')
    if auth_mode not in ('local', 'proxy'):
        raise ValueError('DESPENSA_AUTH_MODE must be local or proxy')
    proxy_secret = ''
    if auth_mode == 'proxy':
        secret_file = os.environ.get('DESPENSA_PROXY_SECRET_FILE', '')
        if secret_file:
            proxy_secret = Path(secret_file).read_text().strip()
        if len(proxy_secret) < 32:
            raise ValueError('Proxy authentication requires a secret file with at least 32 characters')
    auth_info = dict(mode=auth_mode, login_url=os.environ.get('DESPENSA_LOGIN_URL', ''),
        logout_url=os.environ.get('DESPENSA_LOGOUT_URL', ''),settings_url=os.environ.get('DESPENSA_AUTH_SETTINGS_URL',''))
    if auth_mode == 'proxy' and not auth_info['settings_url'] and auth_info['logout_url']:
        portal=urlsplit(auth_info['logout_url'])
        auth_info['settings_url']=f'{portal.scheme}://{portal.netloc}/settings'
    for key in ('login_url', 'logout_url','settings_url'):
        if auth_info[key] and (urlsplit(auth_info[key]).scheme != 'https' or not urlsplit(auth_info[key]).netloc):
            raise ValueError('Authentication URLs must use HTTPS')
    folder = Path(data_dir or os.environ.get('DESPENSA_DATA', ROOT / 'data'))
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    app.config['DATABASE'] = str(folder / 'despensa.sqlite3')
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.executescript(SCHEMA)
        from research import setup
        setup(db)
        db.execute('PRAGMA journal_mode=WAL')
        from research import upgrade_adapters
        upgrade_adapters(db)
        db.execute("UPDATE research_tasks SET status='queued' WHERE status='running'")
        # A process restart must not strand an interrupted refresh indefinitely.
        db.execute("UPDATE jobs SET status='interrupted',finished=? WHERE status='running'", (utcnow(),))

    @contextmanager
    def database():
        db = sqlite3.connect(app.config['DATABASE'], timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.database = database

    def profile(uid):
        with database() as db:
            row = db.execute('SELECT data FROM profiles WHERE user_id=?', (uid,)).fetchone()
        defaults = default_profile()
        saved = json.loads(row['data']) if row else {}
        stores = saved.pop('stores', {})
        defaults.update(saved)
        for sid, values in stores.items():
            if sid in defaults['stores']:
                defaults['stores'][sid].update(values)
        return defaults

    def require_user(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if auth_mode == 'proxy':
                supplied = request.headers.get('X-Despensa-Proxy-Token', '')
                subject = request.headers.get('Remote-User', '').strip()
                if (not hmac.compare_digest(supplied.encode(), proxy_secret.encode())
                        or not subject or len(subject) > 200 or any(ord(c) < 32 for c in subject)):
                    return jsonify(error='Autenticação Authelia necessária', code='proxy_auth_required', auth=auth_info), 401
                with database() as db:
                    # Serialize first-use provisioning; never merge accounts merely by username.
                    db.execute('BEGIN IMMEDIATE')
                    row = db.execute('SELECT users.id,users.username FROM identities JOIN users ON users.id=identities.user_id WHERE provider=? AND subject=?', ('authelia', subject)).fetchone()
                    if not row:
                        uid = uuid.uuid4().hex
                        db.execute('INSERT INTO users VALUES(?,?,?,?)', (uid, 'authelia:' + subject, '', utcnow()))
                        db.execute('INSERT INTO profiles VALUES(?,?)', (uid, json.dumps(default_profile())))
                        db.execute('INSERT INTO identities VALUES(?,?,?)', ('authelia', subject, uid))
                        row = dict(id=uid)
                g.user = dict(id=row['id'], username=subject)
                return fn(*args, **kwargs)
            raw = request.cookies.get('despensa_session', '')
            token = hashlib.sha256(raw.encode()).hexdigest()
            with database() as db:
                row = db.execute('SELECT users.id,username FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?', (token, time.time())).fetchone()
            if not row:
                return jsonify(error='Sessão necessária', code='auth_required'), 401
            g.user = dict(row)
            return fn(*args, **kwargs)
        return wrapped

    @app.before_request
    def protect_origin():
        if request.method in ('POST', 'PATCH', 'PUT', 'DELETE') and request.path.startswith('/api/'):
            origin = request.headers.get('Origin')
            if (origin and urlsplit(origin).netloc != request.host) or request.headers.get('Sec-Fetch-Site') == 'cross-site':
                return jsonify(error='Origem não autorizada'), 403
            if not request.is_json:
                return jsonify(error='É necessário JSON'), 415

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; font-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'"
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        if request.path in ('/', '/sw.js'):
            response.headers['Cache-Control'] = 'no-cache'
        return response

    @app.errorhandler(Exception)
    def error_handler(err):
        if isinstance(err, HTTPException):
            return jsonify(error=err.description), err.code
        if isinstance(err, (ValueError, TypeError, InvalidOperation)):
            return jsonify(error=str(err)[:200]), 400
        app.logger.exception('Request failed')
        return jsonify(error='Não foi possível concluir. Tente novamente.'), 500

    @app.get('/')
    def index():
        return send_from_directory(ROOT / 'static', 'index.html')

    @app.get('/<name>')
    def pwa(name):
        if name not in {'manifest.webmanifest', 'sw.js', 'logo.svg', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png'}:
            return jsonify(error='Não encontrado'), 404
        return send_from_directory(ROOT / 'static', name)

    @app.get('/api/health')
    def health():
        with database() as db:
            db.execute('SELECT 1')
        return jsonify(ok=True, app='Despensa', version=APP_VERSION)

    login_attempts = {}
    login_lock = threading.Lock()

    @app.get('/api/auth/info')
    def authentication_info():
        return jsonify(auth=auth_info)

    @app.post('/api/auth/<action>')
    def authenticate(action):
        if action not in ('login', 'register', 'logout'):
            return jsonify(error='Não encontrado'), 404
        if auth_mode == 'proxy':
            if action == 'logout':
                response = jsonify(ok=True, redirect=auth_info['logout_url'])
                response.delete_cookie('despensa_session', path='/')
                return response
            return jsonify(error='Utilize a sessão Authelia', code='proxy_auth_required', auth=auth_info), 403
        if action == 'logout':
            with database() as db:
                db.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(request.cookies.get('despensa_session', '').encode()).hexdigest(),))
            response = jsonify(ok=True)
            response.delete_cookie('despensa_session', path='/')
            return response
        data = request.get_json()
        username, password = str(data.get('username', '')).strip().lower(), str(data.get('password', ''))
        if not re.fullmatch(r'[a-z0-9._@+-]{3,80}', username) or not 10 <= len(password) <= 256:
            raise ValueError('Use um nome de 3–80 caracteres e uma palavra-passe com pelo menos 10 caracteres.')
        # Peer IP is used rather than trusting client-supplied forwarding headers.
        peer = request.remote_addr or 'unknown'
        with login_lock:
            now = time.time()
            for key in list(login_attempts):
                if now - login_attempts[key][0] > 900:
                    del login_attempts[key]
            attempt = login_attempts.get(peer, (now, 0))
            if attempt[1] >= 20:
                return jsonify(error='Demasiadas tentativas. Aguarde 15 minutos.'), 429
            login_attempts[peer] = (attempt[0], attempt[1] + 1)
        with database() as db:
            if action == 'register':
                if os.environ.get('DESPENSA_REGISTRATION', 'true').lower() != 'true' and db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                    return jsonify(error='Registo desativado nesta instalação'), 403
                uid = uuid.uuid4().hex
                try:
                    db.execute('INSERT INTO users VALUES(?,?,?,?)', (uid, username, generate_password_hash(password), utcnow()))
                    db.execute('INSERT INTO profiles VALUES(?,?)', (uid, json.dumps(default_profile())))
                except sqlite3.IntegrityError:
                    raise ValueError('Este nome já está em uso')
            else:
                row = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
                if not row or not check_password_hash(row['password'], password):
                    return jsonify(error='Nome ou palavra-passe incorretos'), 401
                uid = row['id']
            token = secrets.token_urlsafe(40)
            db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), uid, time.time() + 86400 * 30))
        response = jsonify(user=dict(id=uid, username=username))
        response.set_cookie('despensa_session', token, max_age=86400 * 30, httponly=True, samesite='Lax',
            secure=request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' or os.environ.get('DESPENSA_SECURE_COOKIE') == 'true', path='/')
        return response

    @app.get('/api/me')
    @require_user
    def me():
        return jsonify(user=g.user, profile=profile(g.user['id']), stores=list(STORE_MAP.values()), auth=auth_info)

    @app.put('/api/profile')
    @require_user
    def save_profile():
        p, d = profile(g.user['id']), request.get_json()
        for key in ('home', 'work'):
            value=str(d.get(key,p[key]))[:300]
            if value!=p[key] and key+'_coords' not in d:
                p[key+'_coords']=None
            p[key]=value
        for key in ('home_coords', 'work_coords'):
            value = d.get(key, p.get(key))
            if value is not None and (not isinstance(value, list) or len(value) != 2 or not all(isinstance(n, (int, float)) for n in value) or not -180 <= value[0] <= 180 or not -90 <= value[1] <= 90):
                raise ValueError('Coordenadas inválidas')
            p[key] = value
        p['locale'] = 'es-ES' if d.get('locale', p['locale']) == 'es-ES' else 'pt-PT'
        p['countries'] = [c for c in d.get('countries', p['countries']) if c in ('PT', 'ES')]
        if not p['countries']:
            raise ValueError('Escolha pelo menos um país')
        for key, low, high in [('budget', 0, 100000), ('interval_hours', 6, 168), ('max_stops', 1, 4), ('cost_per_km', 0, 10)]:
            value = float(d.get(key, p[key]))
            if not low <= value <= high:
                raise ValueError(f'Valor inválido: {key}')
            p[key] = int(value) if key in ('interval_hours', 'max_stops') else value
        if 'mobility' in d:
            from travel import validate
            p['mobility']=validate(d['mobility'],p.get('mobility'),folder)
        p['automatic'] = bool(d.get('automatic', p['automatic']))
        p['budget_source'] = 'manual' if d.get('budget_source', p.get('budget_source')) == 'manual' else 'auto'
        ref=str(d.get('reference_store', p.get('reference_store','')))
        if ref and ref not in STORE_MAP:
            raise ValueError('Loja de referência inválida')
        p['reference_store']=ref
        p['workdays'] = sorted({int(x) for x in d.get('workdays', p['workdays']) if str(x).isdigit() and 0 <= int(x) <= 6})
        for sid, value in d.get('stores', {}).items():
            if sid not in STORE_MAP or not isinstance(value, dict):
                continue
            current = p['stores'][sid]
            for key in ('enabled', 'card', 'subscription', 'delivery_subscription', 'access'):
                current[key] = bool(value.get(key, current.get(key, False)))
            store = STORE_MAP[sid]
            if not store['loyalty']:
                current['card'] = False
            subscription = store['subscription']
            if not subscription or subscription['kind'] != 'product':
                current['subscription'] = False
            if not subscription or subscription['kind'] != 'delivery':
                current['delivery_subscription'] = False
            if not store['professional']:
                current['access'] = False
            new_address=str(value.get('address',current.get('address','')))[:300]
            if new_address!=current.get('address','') and 'coords' not in value:
                current.update(coords=None,branch_id='',branch_name='')
            current['address']=new_address
            current['branch_id']=str(value.get('branch_id',current.get('branch_id','')))[:120]
            current['branch_name']=str(value.get('branch_name',current.get('branch_name','')))[:160]
            current['coupons'] = [str(c)[:60] for c in value.get('coupons', current['coupons'])][:30]
            km = value.get('extra_km', current.get('extra_km'))
            if km is not None and not 0 <= float(km) <= 2000:
                raise ValueError('Distância inválida')
            current['extra_km'] = float(km) if km is not None else None
            coords = value.get('coords', current.get('coords'))
            if coords is not None and (not isinstance(coords, list) or len(coords) != 2 or not all(isinstance(n, (int, float)) for n in coords) or not -180 <= coords[0] <= 180 or not -90 <= coords[1] <= 90):
                raise ValueError('Coordenadas da loja inválidas')
            current['coords'] = coords
        with database() as db:
            db.execute('INSERT OR REPLACE INTO profiles VALUES(?,?)', (g.user['id'], json.dumps(p)))
        return jsonify(profile=p)

    def month_arg(value=None):
        month = value or request.args.get('month', date.today().strftime('%Y-%m'))
        if not re.fullmatch(r'20\d\d-(0[1-9]|1[0-2])', month):
            raise ValueError('Mês inválido')
        return month

    def get_items(uid, month):
        with database() as db:
            return [dict(json.loads(r['data']), id=r['id']) for r in db.execute('SELECT * FROM items WHERE user_id=? AND month=? ORDER BY rowid', (uid, month))]

    @app.get('/api/budget')
    @require_user
    def budget():
        from budget import monthly_budget
        return jsonify(budget=monthly_budget(g.user['id'], profile(g.user['id']), month_arg()))

    @app.get('/api/nearby')
    @require_user
    def nearby():
        from nearby import discover
        try:
            return jsonify(nearby=discover(profile(g.user['id'])))
        except Exception:
            return jsonify(nearby=dict(stores=[],status='unavailable',distance_method='unavailable'))

    @app.get('/api/items')
    @require_user
    def items():
        return jsonify(items=get_items(g.user['id'], month_arg()))

    def clean_item(d):
        name = str(d.get('name', '')).strip()[:160]
        query = str(d.get('query') or name).strip()[:120]
        quantity = float(d.get('quantity', 1))
        unit = d.get('unit', 'un')
        if not name or len(query) < 2 or not 0 < quantity <= 10000 or unit not in ('kg', 'l', 'un'):
            raise ValueError('Indique um produto, quantidade e unidade válidos')
        needed = str(d.get('needed_on', ''))
        if needed:
            date.fromisoformat(needed)
        return dict(name=name, query=query, quantity=quantity, unit=unit, checked=bool(d.get('checked', False)),
            category=str(d.get('category', 'Mercearia'))[:60], needed_on=needed, offer_id=str(d.get('offer_id', ''))[:120],
            family=str(d.get('family', ''))[:200], note=str(d.get('note', ''))[:300])

    @app.post('/api/items')
    @require_user
    def add_item():
        d = request.get_json()
        item = clean_item(d)
        iid = str(d.get('client_id') or uuid.uuid4().hex)
        if not re.fullmatch('[a-f0-9]{32}', iid):
            raise ValueError('Identificador inválido')
        with database() as db:
            existing = db.execute('SELECT data FROM items WHERE id=? AND user_id=?', (iid, g.user['id'])).fetchone()
            if existing:
                return jsonify(item=dict(json.loads(existing['data']), id=iid))
            if db.execute('SELECT COUNT(*) FROM items WHERE user_id=? AND month=?', (g.user['id'], month_arg(d.get('month')))).fetchone()[0] >= 300:
                raise ValueError('Limite de 300 produtos por mês')
            db.execute('INSERT INTO items VALUES(?,?,?,?)', (iid, g.user['id'], month_arg(d.get('month')), json.dumps(item)))
            from research import request_query
            request_query(db, item['query'],owner=g.user['id'])
        return jsonify(item=dict(item, id=iid)), 201

    @app.route('/api/items/<iid>', methods=['PATCH', 'DELETE'])
    @require_user
    def edit_item(iid):
        with database() as db:
            row = db.execute('SELECT * FROM items WHERE id=? AND user_id=?', (iid, g.user['id'])).fetchone()
            if not row:
                return jsonify(error='Produto não encontrado'), 404
            if request.method == 'DELETE':
                db.execute('DELETE FROM items WHERE id=? AND user_id=?', (iid, g.user['id']))
                return jsonify(ok=True)
            item = clean_item(dict(json.loads(row['data']), **request.get_json()))
            db.execute('UPDATE items SET data=? WHERE id=? AND user_id=?', (json.dumps(item), iid, g.user['id']))
            if any(k in request.get_json() for k in ('name', 'query', 'family')):
                from research import request_query
                request_query(db, item['query'],owner=g.user['id'])
        return jsonify(item=dict(item, id=iid))

    @app.post('/api/items/copy')
    @require_user
    def copy_month():
        d = request.get_json()
        source, target = month_arg(d.get('source')), month_arg(d.get('target'))
        if source == target:
            raise ValueError('Escolha dois meses diferentes')
        with database() as db:
            existing = {fold(i['name']) for i in get_items(g.user['id'], target)}
            count = 0
            for item in get_items(g.user['id'], source):
                if fold(item['name']) in existing:
                    continue
                item.pop('id')
                item.update(checked=False, needed_on='')
                db.execute('INSERT INTO items VALUES(?,?,?,?)', (uuid.uuid4().hex, g.user['id'], target, json.dumps(item)))
                count += 1
        return jsonify(copied=count)

    def get_offers(uid):
        with database() as db:
            return [json.loads(r['data']) for r in db.execute("SELECT data FROM offers WHERE user_id='' OR user_id=?", (uid,))]

    @app.get('/api/offers')
    @require_user
    def offers():
        p = profile(g.user['id'])
        query = product_text(request.args.get('q', '')[:120])
        store = request.args.get('store', '')
        country=request.args.get('country','profile')
        countries=['PT','ES'] if country=='all' else [country] if country in ('PT','ES') else p['countries']
        stores=[sid for sid,s in STORE_MAP.items() if s['country'] in countries and (not store or sid==store)]
        from research import request_query, query_progress
        with database() as db:
            if query and request.args.get('investigate','true')!='false':
                request_query(db,query,stores=stores,owner=g.user['id'])
            progress=query_progress(db,query,stores,g.user['id']) if query else dict(sources=[],pending=0,total=0,finished=0)
        from searching import find
        found, approximate=find([o for o in get_offers(g.user['id']) if o['country'] in countries and (not store or o['store']==store)],query)
        from collections import Counter
        matches=Counter(o['store'] for o in found)
        for source in progress['sources']:
            source['matches']=matches[source['store']]
        from products import comparisons
        comparison_profile=p
        if country!='profile':
            comparison_profile=dict(p,countries=countries,stores={sid:dict(v,enabled=True) for sid,v in p['stores'].items()})
        groups=comparisons(found,comparison_profile)
        if query:
            ranks={o['id']:i for i,o in enumerate(found)}
            groups.sort(key=lambda group:min(ranks[o['id']] for o in group['offers']))
        offset=max(0,int(request.args.get('offset',0)))
        limit=max(1,min(60,int(request.args.get('limit',30))))
        page=groups[offset:offset+limit]
        return jsonify(offers=[o for group in page for o in group['offers']],comparisons=page,total=len(found),group_total=len(groups),
            has_more=offset+limit<len(groups),next_offset=offset+len(page),research=progress,
            approximate=approximate,observed_only=True)

    @app.post('/api/research/search')
    @require_user
    def research_search():
        d=request.get_json()
        query=product_text(str(d.get('q',''))[:120])
        if len(query)<3:
            raise ValueError('Escreva pelo menos três caracteres')
        p=profile(g.user['id'])
        country=d.get('country','profile')
        countries=['PT','ES'] if country=='all' else [country] if country in ('PT','ES') else p['countries']
        stores=[sid for sid,s in STORE_MAP.items() if s['country'] in countries and (not d.get('store') or sid==d['store'])]
        from research import request_query,query_progress
        with database() as db:
            request_query(db,query,stores=stores,force=True,owner=g.user['id'])
            result=query_progress(db,query,stores,g.user['id'])
        return jsonify(research=result),202

    @app.get('/api/research')
    @require_user
    def research_status():
        p = profile(g.user['id'])
        with database() as db:
            states = {r['store']: json.loads(r['data']) for r in db.execute('SELECT * FROM research_sources')}
        return jsonify(sources=[dict(states.get(sid,dict(status='pending',count=0,methods=[],indexed=0)),store=sid)
            for sid, s in STORE_MAP.items() if s['country'] in p['countries']])

    @app.get('/api/image')
    @require_user
    def product_image():
        from images import thumbnail
        oid=request.args.get('id','')
        offer=next((o for o in get_offers(g.user['id']) if o['id']==oid),None)
        if not offer:
            return '',404
        try:
            data=thumbnail(offer)
            if data:
                return Response(data[0],mimetype=data[1])
        except Exception:
            pass
        return '',404

    @app.get('/api/history')
    @require_user
    def history():
        oid = request.args.get('id', '')
        if not any(o['id'] == oid for o in get_offers(g.user['id'])):
            return jsonify(error='Produto não encontrado'), 404
        with database() as db:
            rows = [dict(r) for r in db.execute('SELECT observed,price FROM history WHERE offer_id=? ORDER BY observed DESC LIMIT 60', (oid,))]
        return jsonify(history=rows)

    @app.post('/api/offers/manual')
    @require_user
    def manual_offer():
        d = request.get_json()
        store = str(d.get('store', ''))
        if store not in STORE_MAP:
            raise ValueError('Loja desconhecida')
        name = str(d.get('name', '')).strip()[:160]
        size, unit = float(d.get('size', 0)), d.get('unit', 'un')
        condition = d.get('condition', 'public')
        if not name or not 0 < size <= 10000 or unit not in ('kg', 'l', 'un') or condition not in ('public', 'card', 'subscription', 'coupon', 'professional'):
            raise ValueError('Preço ou formato inválido')
        capability = STORE_MAP[store]
        if condition in ('card', 'coupon') and not capability['loyalty']:
            raise ValueError('Esta loja não tem um programa de fidelização configurado')
        if condition == 'subscription' and (not capability['subscription'] or capability['subscription']['kind'] != 'product'):
            raise ValueError('Uma subscrição de entregas não é um desconto no produto')
        if condition == 'professional' and not capability['professional']:
            raise ValueError('Esta loja não exige acesso profissional')
        start, end = str(d.get('valid_from', '')), str(d.get('valid_to', ''))
        if start:
            date.fromisoformat(start)
        if end:
            date.fromisoformat(end)
        if start and end and start > end:
            raise ValueError('Intervalo de datas inválido')
        source = str(d.get('source_url', ''))[:500]
        if source and (urlsplit(source).scheme not in ('https', 'http') or not urlsplit(source).netloc):
            raise ValueError('Ligação inválida')
        coupon = str(d.get('coupon', '')).strip()[:60]
        if condition == 'coupon' and not coupon:
            raise ValueError('Indique o código do cupão')
        balance = str(d.get('balance', '0')).replace(',', '.')
        balance_cents = 0 if float(balance) == 0 else cents(balance)
        o = dict(id='manual:' + uuid.uuid4().hex, store=store, country=STORE_MAP[store]['country'], name=name,
            brand='', size=size, unit=unit, pack=f'{size:g} {unit}', price_cents=cents(d.get('price')),
            condition=condition, coupon=coupon, balance_cents=balance_cents, source_url=source,
            channel='physical', location=str(d.get('location', 'Loja por identificar'))[:200],
            valid_from=start, valid_to=end, source_kind='manual', observed_at=utcnow(),
            conditions_note=str(d.get('conditions_note', 'Introduzido pelo utilizador'))[:300], vat_included=bool(d.get('vat_included', True)))
        with database() as db:
            db.execute('INSERT INTO offers VALUES(?,?,?,?)', (o['id'], g.user['id'], store, json.dumps(o)))
            db.execute('INSERT INTO history VALUES(?,?,?)', (o['id'], o['observed_at'], o['price_cents']))
        return jsonify(offer=o), 201

    @app.delete('/api/offers/manual/<oid>')
    @require_user
    def delete_offer(oid):
        with database() as db:
            db.execute('DELETE FROM offers WHERE id=? AND user_id=?', ('manual:' + oid, g.user['id']))
        return jsonify(ok=True)

    @app.get('/api/plan')
    @require_user
    def plan():
        day = request.args.get('day', date.today().isoformat())
        date.fromisoformat(day)
        p = profile(g.user['id'])
        items = [i for i in get_items(g.user['id'], month_arg()) if not i['needed_on'] or i['needed_on'] <= day]
        offers = get_offers(g.user['id'])
        road, route_error = None, False
        # Road requests only occur in the plan view, not on every list checkbox.
        if request.args.get('roads') == 'true':
            from routing import road_matrix
            from planner import eligible, match
            ids = sorted({o['store'] for o in offers if eligible(o, p, day) and any(match(i, o) for i in items if not i['checked'])})
            try:
                from nearby import discover
                # Reuse cached discovery; querying both origins is bounded and cached for a day.
                branches = discover(p)['stores'] if p.get('home_coords') else []
                road = road_matrix(p, ids, day, request.args.get('route', 'auto'), branches=branches)
            except Exception:
                route_error = True
        result = make_plan(items, offers, p, day, road=road)
        result['route_error'] = route_error
        mode=request.args.get('route','auto')
        work_route=mode=='work' or (mode=='auto' and date.fromisoformat(day).weekday() in p.get('workdays',[]) and bool(p.get('work_coords')))
        for option in result['plans']:
            option['distance_reason']=None if option['route'] else ('not_requested' if request.args.get('roads')!='true' else
                'missing_home' if not p.get('home_coords') else 'missing_work' if work_route and not p.get('work_coords') else
                'service_unavailable' if route_error else 'no_branch' if not road or any(s not in road['ids'] for s in option['stores']) else 'unreachable')
        result['plans']=result['plans'][:12]
        return jsonify(result)

    from plan_service import PlanService
    planning=PlanService(database,profile,get_items,get_offers,folder)
    app.planning=planning

    @app.get('/api/vehicles')
    @require_user
    def vehicles():
        from mobility_sources import search_vehicles
        return jsonify(search_vehicles(folder,request.args.get('q',''),request.args.get('year') or None))

    @app.get('/api/vehicles/detail')
    @require_user
    def vehicle_detail():
        from mobility_sources import get_vehicle
        return jsonify(vehicle=get_vehicle(folder,request.args.get('id','')))

    @app.get('/api/fuel-prices')
    @require_user
    def fuel_data():
        from mobility_sources import fuel_prices
        return jsonify(fuel_prices(folder,request.args.get('country','PT')))

    @app.post('/api/plans')
    @require_user
    def start_plan():
        data=request.get_json();month=month_arg(data.get('month'));day=str(data.get('day',date.today().isoformat()))
        date.fromisoformat(day)
        mode=data.get('route','auto')
        if mode not in ('auto','home','work'):raise ValueError('Origem inválida')
        clock=str(data.get('departure_time',''))
        if clock and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',clock):raise ValueError('Hora inválida')
        from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
        zone=str(data.get('timezone','Europe/Lisbon'))[:64]
        try:ZoneInfo(zone)
        except (ValueError,ZoneInfoNotFoundError):raise ValueError('Fuso horário inválido') from None
        maximum=int(data.get('max_stops',4))
        if not 1<=maximum<=4:raise ValueError('Escolha entre uma e quatro lojas')
        identifier=planning.start(g.user['id'],month,dict(day=day,route=mode,departure_time=clock,max_stops=maximum,timezone=zone))
        return jsonify(run=planning.get(g.user['id'],identifier)),202

    @app.get('/api/plans/<identifier>')
    @require_user
    def get_plan_run(identifier):
        value=planning.get(g.user['id'],identifier)
        if not value:return jsonify(error='Cálculo não encontrado'),404
        return jsonify(run=value)

    @app.post('/api/plans/select')
    @require_user
    def select_plan():
        data=request.get_json()
        return jsonify(selected=planning.select(g.user['id'],str(data.get('run_id','')),str(data.get('plan_id',''))))

    @app.get('/api/plans/selected')
    @require_user
    def selected_plan():
        return jsonify(selected=planning.selected(g.user['id'],month_arg()))

    @app.delete('/api/plans/selected')
    @require_user
    def clear_selected_plan():
        with database() as db:db.execute('DELETE FROM selected_plans WHERE user_id=? AND month=?',(g.user['id'],month_arg(request.get_json().get('month'))))
        return jsonify(ok=True)

    @app.get('/api/geocode')
    @require_user
    def locate():
        from routing import geocode
        try:
            return jsonify(results=geocode(request.args.get('q', '')))
        except ValueError:
            raise
        except Exception:
            return jsonify(error='O serviço de localização não respondeu. Pode guardar a morada sem coordenadas.'), 502

    @app.get('/api/status')
    @require_user
    def status():
        with database() as db:
            jobs = [dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 8')]
            for job in jobs:
                job['data'] = json.loads(job['data'])
            count = db.execute("SELECT count(*) FROM offers WHERE user_id='' OR user_id=?", (g.user['id'],)).fetchone()[0]
            meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM meta')}
            sources = {r['store']: json.loads(r['data']) for r in db.execute('SELECT * FROM research_sources')}
        return jsonify(version=APP_VERSION,jobs=jobs, offer_count=count, meta=meta, sources=sources)

    @app.post('/api/purchases')
    @require_user
    def record_purchase():
        import math
        from decimal import Decimal, ROUND_HALF_UP
        from planner import eligible, match
        d=request.get_json()
        pid=str(d.get('id',''))
        if not re.fullmatch('[a-f0-9]{32}',pid):
            raise ValueError('Identificador de compra inválido')
        day=str(d.get('purchased_on',date.today().isoformat()))
        if date.fromisoformat(day)>date.today():
            raise ValueError('A compra não pode ter uma data futura')
        paid=Decimal(str(d.get('paid','')).replace(',','.'))
        if not paid.is_finite() or not 0<=paid<=100000:
            raise ValueError('Preço pago inválido')
        paid_cents=int((paid*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        sid=str(d.get('store',''))
        if sid not in STORE_MAP:
            raise ValueError('Loja inválida')
        with database() as db:
            old=db.execute('SELECT data FROM purchases WHERE id=? AND user_id=?',(pid,g.user['id'])).fetchone()
            if old:
                return jsonify(purchase=json.loads(old['data']))
            row=db.execute('SELECT * FROM items WHERE id=? AND user_id=?',(str(d.get('item_id','')),g.user['id'])).fetchone()
            if not row:
                return jsonify(error='Produto não encontrado'),404
            item=json.loads(row['data'])
            if day[:7]!=row['month']:
                raise ValueError('A data da compra deve pertencer ao mês da lista')
            quantity=float(d.get('quantity',item['quantity']))
            if not 0<quantity<=10000:
                raise ValueError('Quantidade inválida')
            item_for_comparison=dict(item,quantity=quantity)
            p=profile(g.user['id'])
            ref=p.get('reference_store','')
            candidates=[] if d.get('offline') or day!=date.today().isoformat() else [o for o in get_offers(g.user['id']) if o['store']==ref and eligible(o,p,day) and match(item_for_comparison,o)]
            from planner import purchase_cost
            benchmark=min(candidates,key=lambda o:purchase_cost(o,quantity,item['unit'])[1]) if candidates else None
            reference_cents=purchase_cost(benchmark,quantity,item['unit'])[1] if benchmark else None
            reference_kind='catalog' if benchmark else None
            manual_reference=d.get('reference_price')
            if manual_reference not in ('',None):
                number=Decimal(str(manual_reference).replace(',','.'))
                if not number.is_finite() or not 0<=number<=100000:
                    raise ValueError('Preço de referência inválido')
                reference_cents=int((number*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                reference_kind='manual'
            purchase=dict(id=pid,item_id=row['id'],name=item['name'],quantity=quantity,unit=item['unit'],store=sid,
                purchased_on=day,paid_cents=paid_cents,reference_cents=reference_cents,reference_store=ref,
                reference_kind=reference_kind,reference_offer=benchmark if reference_kind=='catalog' else None,
                savings_cents=reference_cents-paid_cents if reference_cents is not None else None,recorded_at=utcnow())
            try:
                db.execute('INSERT INTO purchases VALUES(?,?,?,?,?)',(pid,g.user['id'],row['month'],row['id'],json.dumps(purchase)))
            except sqlite3.IntegrityError:
                return jsonify(error='Já existe uma compra registada para este produto. Elimine o registo anterior para corrigir.'),409
            item['checked']=True
            db.execute('UPDATE items SET data=? WHERE id=? AND user_id=?',(json.dumps(item),row['id'],g.user['id']))
        return jsonify(purchase=purchase),201

    @app.delete('/api/purchases/<pid>')
    @require_user
    def delete_purchase(pid):
        with database() as db:
            row=db.execute('SELECT item_id FROM purchases WHERE id=? AND user_id=?',(pid,g.user['id'])).fetchone()
            if row:
                item=db.execute('SELECT data FROM items WHERE id=? AND user_id=?',(row['item_id'],g.user['id'])).fetchone()
                if item:
                    data=json.loads(item['data']);data['checked']=False
                    db.execute('UPDATE items SET data=? WHERE id=? AND user_id=?',(json.dumps(data),row['item_id'],g.user['id']))
                db.execute('DELETE FROM purchases WHERE id=? AND user_id=?',(pid,g.user['id']))
        return jsonify(ok=True)

    @app.post('/api/trips')
    @require_user
    def record_trip():
        from decimal import Decimal, ROUND_HALF_UP
        d=request.get_json()
        tid=str(d.get('id',''))
        if not re.fullmatch('[a-f0-9]{32}',tid):
            raise ValueError('Identificador inválido')
        day=str(d.get('day',date.today().isoformat()))
        if date.fromisoformat(day)>date.today():
            raise ValueError('Não pode registar uma deslocação futura')
        amount=Decimal(str(d.get('cost','')).replace(',','.'))
        if not amount.is_finite() or not 0<=amount<=10000:
            raise ValueError('Custo inválido')
        trip=dict(id=tid,day=day,cost_cents=int((amount*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)),
            estimated=bool(d.get('estimated',False)),note=str(d.get('note',''))[:200])
        with database() as db:
            db.execute('INSERT OR IGNORE INTO trips VALUES(?,?,?,?)',(tid,g.user['id'],day[:7],json.dumps(trip)))
        return jsonify(trip=trip),201

    @app.delete('/api/trips/<tid>')
    @require_user
    def delete_trip(tid):
        with database() as db:
            db.execute('DELETE FROM trips WHERE id=? AND user_id=?',(tid,g.user['id']))
        return jsonify(ok=True)

    @app.get('/api/savings')
    @require_user
    def savings():
        month=month_arg()
        with database() as db:
            purchases=[json.loads(r['data']) for r in db.execute('SELECT data FROM purchases WHERE user_id=? AND month=? ORDER BY rowid DESC',(g.user['id'],month))]
            trips=[json.loads(r['data']) for r in db.execute('SELECT data FROM trips WHERE user_id=? AND month=? ORDER BY rowid DESC',(g.user['id'],month))]
        benchmarked=[p for p in purchases if p['reference_cents'] is not None]
        gross=sum(p['savings_cents'] for p in benchmarked)
        travel=sum(t['cost_cents'] for t in trips)
        recorded_ids={p['item_id'] for p in purchases}
        unpriced=sum(i['checked'] and i['id'] not in recorded_ids for i in get_items(g.user['id'],month))
        return jsonify(savings=dict(month=month,purchases=purchases,trips=trips,spent_cents=sum(p['paid_cents'] for p in purchases),
            compared_count=len(benchmarked),purchase_count=len(purchases),unpriced_count=unpriced,
            product_savings_cents=gross if benchmarked else None,travel_cents=travel if trips else None,
            net_savings_cents=gross-travel if benchmarked and trips else None,
            travel_estimated=any(t.get('estimated') for t in trips),partial=len(benchmarked)!=len(purchases) or unpriced>0))

    @app.post('/api/refresh')
    @require_user
    def refresh():
        jid = enqueue_refresh(app)
        return jsonify(job_id=jid, queued=True), 202

    @app.get('/api/export')
    @require_user
    def export_data():
        with database() as db:
            rows = [dict(r) for r in db.execute('SELECT month,data FROM items WHERE user_id=?', (g.user['id'],))]
            purchases=[json.loads(r['data']) for r in db.execute('SELECT data FROM purchases WHERE user_id=?',(g.user['id'],))]
            trips=[json.loads(r['data']) for r in db.execute('SELECT data FROM trips WHERE user_id=?',(g.user['id'],))]
            selected=[json.loads(r['data']) for r in db.execute('SELECT data FROM selected_plans WHERE user_id=?',(g.user['id'],))]
        response = jsonify(version=1, exported_at=utcnow(), selected_plans=selected, profile=profile(g.user['id']),
            items=[dict(json.loads(r['data']), month=r['month']) for r in rows],
            offers=[o for o in get_offers(g.user['id']) if o['source_kind'] == 'manual'],purchases=purchases,trips=trips)
        response.headers['Content-Disposition'] = 'attachment; filename="despensa.json"'
        return response

    return app


REFRESH_LOCK = threading.Lock()


def enqueue_refresh(app, internal=False):
    with REFRESH_LOCK, app.database() as db:
        running = db.execute("SELECT id FROM jobs WHERE status IN ('queued','running') LIMIT 1").fetchone()
        if running:
            return running['id']
        last = db.execute('SELECT created FROM jobs ORDER BY created DESC LIMIT 1').fetchone()
        if not internal and last and (datetime.now(timezone.utc) - datetime.fromisoformat(last['created'])).total_seconds() < 900:
            raise ValueError('O catálogo foi atualizado há pouco. Aguarde 15 minutos entre recolhas.')
        jid = uuid.uuid4().hex
        db.execute('INSERT INTO jobs VALUES(?,?,?,?,?)', (jid, 'queued', utcnow(), None, json.dumps({'sources': []})))
        return jid


def run_job(app, job):
    from research import run_research
    reports = []
    with app.database() as db:
        db.execute("UPDATE jobs SET status='running' WHERE id=?", (job['id'],))
    def report(state):
        reports[:] = [r for r in reports if r['store'] != state['store']]
        reports.append(dict(state, category='Pesquisa automática', ok=state['status'] in ('ok','partial')))
        with app.database() as db:
            db.execute('UPDATE jobs SET data=? WHERE id=?', (json.dumps({'sources': reports}), job['id']))
    run_research(app, report)
    ok = sum(r['ok'] for r in reports)
    with app.database() as db:
        db.execute('UPDATE jobs SET status=?,finished=? WHERE id=?', ('done' if ok == len(reports) else 'partial' if ok else 'failed', utcnow(), job['id']))
        db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)', ('last_refresh', json.dumps(utcnow())))

def worker(app, stop=None):
    stop = stop or threading.Event()
    while not stop.is_set():
        try:
            with app.database() as db:
                job = db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
                profiles = [json.loads(r['data']) for r in db.execute('SELECT data FROM profiles')]
                last = db.execute('SELECT created FROM jobs ORDER BY created DESC LIMIT 1').fetchone()
                requested = db.execute('SELECT MAX(requested) FROM research_queries').fetchone()[0] or 0
                sources = [json.loads(r[0]) for r in db.execute('SELECT data FROM research_sources')]
            if job:
                run_job(app, job)
            else:
                active = [p['interval_hours'] for p in profiles if p.get('automatic')]
                last_time = datetime.fromisoformat(last['created']).timestamp() if last else 0
                due_retry = any(s.get('status') == 'unavailable' and s.get('retry_at',0) <= time.time() for s in sources)
                due_discovery = any(s.get('remaining',0) and s.get('retry_at',0) <= time.time() for s in sources)
                if active and (due_retry or due_discovery or time.time() - last_time >= min(active) * 3600):
                    enqueue_refresh(app, internal=True)
        except Exception:
            logging.exception('Worker error')
        stop.wait(15)


if __name__ == '__main__':
    from waitress import serve
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    threading.Thread(target=worker, args=(app,), daemon=True).start()
    from research import priority_worker
    for _ in range(2):
        threading.Thread(target=priority_worker,args=(app,),daemon=True).start()
    serve(app, host=os.environ.get('DESPENSA_HOST', '0.0.0.0'), port=int(os.environ.get('DESPENSA_PORT', '8108')), threads=8)
