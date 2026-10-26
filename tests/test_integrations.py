import json
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest
from app import create_app
from budget import monthly_budget
from integrations.export_rumo_budget import export_budget


@pytest.fixture
def proxy_app(tmp_path, monkeypatch):
    secret = tmp_path / 'secret'
    secret.write_text('test-proxy-secret-' * 4)
    monkeypatch.setenv('DESPENSA_AUTH_MODE', 'proxy')
    monkeypatch.setenv('DESPENSA_PROXY_SECRET_FILE', str(secret))
    monkeypatch.setenv('DESPENSA_LOGIN_URL', 'https://shopping.example.org/')
    monkeypatch.setenv('DESPENSA_LOGOUT_URL', 'https://auth.example.org/logout')
    return create_app(tmp_path / 'app', testing=True)


def proxy_headers(subject='alice'):
    return {'Remote-User': subject, 'X-Despensa-Proxy-Token': 'test-proxy-secret-' * 4}


def test_proxy_rejects_forgery_and_disables_local_auth(proxy_app):
    client = proxy_app.test_client()
    assert client.get('/api/me', headers={'Remote-User': 'alice'}).status_code == 401
    assert client.get('/api/me', headers=dict(proxy_headers(), **{'X-Despensa-Proxy-Token': 'wrong'})).status_code == 401
    assert client.get('/api/me', headers={'X-Despensa-Proxy-Token': 'test-proxy-secret-' * 4}).status_code == 401
    for action in ('login', 'register'):
        assert client.post('/api/auth/' + action, json={'username': 'alice', 'password': 'long-password'}).status_code == 403


def test_proxy_provisions_once_and_isolates_users(proxy_app):
    client = proxy_app.test_client()
    alice = client.get('/api/me', headers=proxy_headers()).json['user']
    assert alice['username'] == 'alice'
    assert client.get('/api/me', headers=proxy_headers()).json['user'] == alice
    client.post('/api/items', json={'name': 'Arroz', 'unit': 'kg'}, headers=proxy_headers())
    assert len(client.get('/api/items', headers=proxy_headers()).json['items']) == 1
    assert client.get('/api/items', headers=proxy_headers('bob')).json['items'] == []
    result = client.post('/api/auth/logout', json={}).json
    assert result['redirect'] == 'https://auth.example.org/logout'


def test_proxy_does_not_merge_matching_local_username(proxy_app):
    with proxy_app.database() as db:
        db.execute('INSERT INTO users VALUES(?,?,?,?)', ('local-id', 'alice', 'existing-hash', '2026-01-01'))
    result = proxy_app.test_client().get('/api/me', headers=proxy_headers()).json
    assert result['user']['id'] != 'local-id'


def test_proxy_explicit_identity_link_preserves_existing_profile(proxy_app):
    with proxy_app.database() as db:
        db.execute('INSERT INTO users VALUES(?,?,?,?)', ('local-id', 'alice', 'existing-hash', '2026-01-01'))
        db.execute('INSERT INTO identities VALUES(?,?,?)', ('authelia', 'alice', 'local-id'))
    assert proxy_app.test_client().get('/api/me', headers=proxy_headers()).json['user']['id'] == 'local-id'


def test_proxy_without_secret_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv('DESPENSA_AUTH_MODE', 'proxy')
    monkeypatch.delenv('DESPENSA_PROXY_SECRET_FILE', raising=False)
    with pytest.raises(ValueError, match='secret'):
        create_app(tmp_path)


def test_rumo_changes_follow_each_selected_month_without_touching_database(tmp_path, monkeypatch):
    source = tmp_path / 'rumo.db'
    db = sqlite3.connect(source)
    db.executescript('''CREATE TABLE months(id INTEGER PRIMARY KEY,year INTEGER,month INTEGER);
        CREATE TABLE month_expenses(id INTEGER PRIMARY KEY,month_id INTEGER,name TEXT,category TEXT,planned REAL,actual REAL);
        INSERT INTO months VALUES(1,2026,10),(2,2026,11);
        INSERT INTO month_expenses VALUES(1,1,'Supermercado','DESPESAS',300,25),
        (2,2,'Supermercado','DESPESAS',420,NULL),(3,1,'Compras Online','DESPESAS',999,NULL);''')
    db.commit()
    target = tmp_path / 'budgets' / 'budget.json'
    export_budget(source, target)
    monkeypatch.setenv('DESPENSA_RUMO_SNAPSHOT', str(target))
    monkeypatch.setenv('DESPENSA_RUMO_USER_IDS', 'alice')
    p = {'budget': 250}
    assert monthly_budget('alice', p, '2026-10')['amount_cents'] == 30000
    assert monthly_budget('alice', p, '2026-11')['amount_cents'] == 42000
    assert monthly_budget('alice', p, '2026-12')['status'] == 'month_missing'
    assert monthly_budget('bob', p, '2026-10')['source'] == 'manual'
    db.execute('UPDATE month_expenses SET planned=350 WHERE id=1'); db.commit()
    export_budget(source, target)
    assert monthly_budget('alice', p, '2026-10')['amount_cents'] == 35000
    assert 'Compras Online' not in target.read_text()
    data=json.loads(target.read_text());data['updated_at']=(datetime.now(timezone.utc)-timedelta(minutes=10)).isoformat()
    target.write_text(json.dumps(data))
    assert monthly_budget('alice', p, '2026-10')['status'] == 'stale'
    assert monthly_budget('alice', p, '2026-10')['amount_cents'] is None
    db.close()


def test_delivery_pass_never_unlocks_product_discount(tmp_path):
    app = create_app(tmp_path, testing=True)
    c = app.test_client()
    c.post('/api/auth/register', json={'username': 'tester', 'password': 'temporary-password'})
    p=c.put('/api/profile',json={'stores':{'auchan':{'subscription':True,'delivery_subscription':True},'continente':{'delivery_subscription':True}}}).json['profile']
    assert not p['stores']['auchan']['subscription']
    assert not p['stores']['auchan']['delivery_subscription']
    assert p['stores']['continente']['delivery_subscription']
    for sid in ('auchan','continente'):
        assert c.post('/api/offers/manual',json=dict(name='Arroz',store=sid,price=1,size=1,unit='kg',condition='subscription')).status_code==400
