"""Despensa: personal grocery lists, observed prices and explainable shopping plans."""
import hashlib
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
from urllib.parse import urlsplit

from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from catalog import STORE_MAP, cents, fold
from planner import make_plan

ROOT = Path(__file__).resolve().parent
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS profiles(user_id TEXT PRIMARY KEY,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,month TEXT NOT NULL,data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS item_owner ON items(user_id,month);
CREATE TABLE IF NOT EXISTS offers(id TEXT PRIMARY KEY,user_id TEXT NOT NULL DEFAULT '',store TEXT NOT NULL,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS history(offer_id TEXT NOT NULL,observed TEXT NOT NULL,price INTEGER NOT NULL,PRIMARY KEY(offer_id,observed));
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT NOT NULL,created TEXT NOT NULL,finished TEXT,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
'''


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def default_profile():
    return dict(locale='pt-PT', countries=['PT'], budget=250, interval_hours=24, automatic=True,
        max_stops=2, cost_per_km=.20, home='', work='', home_coords=None, work_coords=None,
        workdays=[0, 1, 2, 3, 4], stores={s: dict(enabled=s in ('continente', 'auchan'), card=False,
        subscription=False, access=False, coupons=[], extra_km=None, address='', coords=None) for s in STORE_MAP})


def create_app(data_dir=None, testing=False):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=1_000_000, JSON_AS_ASCII=False)
    folder = Path(data_dir or os.environ.get('DESPENSA_DATA', ROOT / 'data'))
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    app.config['DATABASE'] = str(folder / 'despensa.sqlite3')
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.executescript(SCHEMA)
        db.execute('PRAGMA journal_mode=WAL')
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
        return json.loads(row['data']) if row else default_profile()

    def require_user(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
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
        if isinstance(err, (ValueError, TypeError)):
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
        return jsonify(ok=True, app='Despensa', version='0.1.0')

    login_attempts = {}
    login_lock = threading.Lock()

    @app.post('/api/auth/<action>')
    def authenticate(action):
        if action not in ('login', 'register', 'logout'):
            return jsonify(error='Não encontrado'), 404
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
        return jsonify(user=g.user, profile=profile(g.user['id']), stores=list(STORE_MAP.values()))

    @app.put('/api/profile')
    @require_user
    def save_profile():
        p, d = profile(g.user['id']), request.get_json()
        for key in ('home', 'work'):
            p[key] = str(d.get(key, p[key]))[:300]
        for key in ('home_coords', 'work_coords'):
            value = d.get(key, p.get(key))
            if value is not None and (not isinstance(value, list) or len(value) != 2 or not all(isinstance(n, (int, float)) for n in value) or not -180 <= value[0] <= 180 or not -90 <= value[1] <= 90):
                raise ValueError('Coordenadas inválidas')
            p[key] = value
        p['locale'] = 'es-ES' if d.get('locale', p['locale']) == 'es-ES' else 'pt-PT'
        p['countries'] = [c for c in d.get('countries', p['countries']) if c in ('PT', 'ES')]
        if not p['countries']:
            raise ValueError('Escolha pelo menos um país')
        for key, low, high in [('budget', 0, 100000), ('interval_hours', 6, 168), ('max_stops', 1, 3), ('cost_per_km', 0, 10)]:
            value = float(d.get(key, p[key]))
            if not low <= value <= high:
                raise ValueError(f'Valor inválido: {key}')
            p[key] = int(value) if key in ('interval_hours', 'max_stops') else value
        p['automatic'] = bool(d.get('automatic', p['automatic']))
        p['workdays'] = sorted({int(x) for x in d.get('workdays', p['workdays']) if str(x).isdigit() and 0 <= int(x) <= 6})
        for sid, value in d.get('stores', {}).items():
            if sid not in STORE_MAP or not isinstance(value, dict):
                continue
            current = p['stores'][sid]
            for key in ('enabled', 'card', 'subscription', 'access'):
                current[key] = bool(value.get(key, current[key]))
            current['address'] = str(value.get('address', current.get('address', '')))[:300]
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
            category=str(d.get('category', 'Mercearia'))[:60], needed_on=needed, offer_id=str(d.get('offer_id', ''))[:120], note=str(d.get('note', ''))[:300])

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
        words = fold(request.args.get('q', '')[:120]).split()
        store = request.args.get('store', '')
        found = [o for o in get_offers(g.user['id']) if all(w in fold(o['name']).split() for w in words)
            and o['country'] in p['countries'] and (not store or o['store'] == store)]
        found.sort(key=lambda o: (o['price_cents'] / o['size'] if o.get('size') else 1e9, o['name']))
        return jsonify(offers=found[:200], total=len(found), observed_only=True)

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
                road = road_matrix(p, ids, day, request.args.get('route', 'auto'))
            except Exception:
                route_error = True
        result = make_plan(items, offers, p, day, road=road)
        result['route_error'] = route_error
        return jsonify(result)

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
        return jsonify(jobs=jobs, offer_count=count, meta=meta)

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
        response = jsonify(version=1, exported_at=utcnow(), profile=profile(g.user['id']),
            items=[dict(json.loads(r['data']), month=r['month']) for r in rows],
            offers=[o for o in get_offers(g.user['id']) if o['source_kind'] == 'manual'])
        response.headers['Content-Disposition'] = 'attachment; filename="despensa.json"'
        return response

    return app


REFRESH_LOCK = threading.Lock()


def enqueue_refresh(app):
    with REFRESH_LOCK, app.database() as db:
        running = db.execute("SELECT id FROM jobs WHERE status IN ('queued','running') LIMIT 1").fetchone()
        if running:
            return running['id']
        last = db.execute('SELECT created FROM jobs ORDER BY created DESC LIMIT 1').fetchone()
        if last and (datetime.now(timezone.utc) - datetime.fromisoformat(last['created'])).total_seconds() < 900:
            raise ValueError('O catálogo foi atualizado há pouco. Aguarde 15 minutos entre recolhas.')
        jid = uuid.uuid4().hex
        db.execute('INSERT INTO jobs VALUES(?,?,?,?,?)', (jid, 'queued', utcnow(), None, json.dumps({'sources': []})))
        return jid


def run_job(app, job):
    from catalog import CATEGORY_SOURCES, fetch_category
    reports = []
    with app.database() as db:
        db.execute("UPDATE jobs SET status='running' WHERE id=?", (job['id'],))
    for source in CATEGORY_SOURCES:
        try:
            products = fetch_category(source)
            observed = utcnow()
            with app.database() as db:
                for o in products:
                    o['observed_at'] = observed
                    db.execute('INSERT OR REPLACE INTO offers VALUES(?,?,?,?)', (o['id'], '', o['store'], json.dumps(o)))
                    db.execute('INSERT OR REPLACE INTO history VALUES(?,?,?)', (o['id'], observed, o['price_cents']))
            reports.append(dict(store=source['store'], category=source['name'], count=len(products), ok=True))
        except Exception as e:
            logging.warning('Source %s: %s', source['name'], type(e).__name__)
            reports.append(dict(store=source['store'], category=source['name'], count=0, ok=False,
                error='A fonte não respondeu ou não permitiu a recolha. Últimos dados preservados.'))
        with app.database() as db:
            db.execute('UPDATE jobs SET data=? WHERE id=?', (json.dumps({'sources': reports}), job['id']))
        time.sleep(2)
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
            if job:
                run_job(app, job)
            else:
                active = [p['interval_hours'] for p in profiles if p.get('automatic')]
                if active and (not last or (datetime.now(timezone.utc) - datetime.fromisoformat(last['created'])).total_seconds() >= min(active) * 3600):
                    enqueue_refresh(app)
        except Exception:
            logging.exception('Worker error')
        stop.wait(15)


if __name__ == '__main__':
    from waitress import serve
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    threading.Thread(target=worker, args=(app,), daemon=True).start()
    serve(app, host=os.environ.get('DESPENSA_HOST', '0.0.0.0'), port=int(os.environ.get('DESPENSA_PORT', '8108')), threads=8)
