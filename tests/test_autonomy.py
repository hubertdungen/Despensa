"""Work routine, best shopping windows, refuel log, plates and EU vehicle data."""
import time
import uuid
from datetime import date, datetime, timedelta, timezone

import mobility_sources as sources
import plan_service
import research
import requests
import schedule
import travel
from app import create_app
from planner import make_plan


def register(client, name):
    assert client.post('/api/auth/register', json=dict(username=name, password='temporary-password-2026')).status_code == 200


def test_schedule_selfcheck():
    assert schedule._selfcheck()


def test_closed_shop_is_never_recommended_and_unknown_hours_are_flagged():
    zone = schedule.ZoneInfo('Europe/Lisbon')
    profile = dict(workdays=[], countries=['PT'], shop_from='20:00', shop_until='23:00', cost_per_km=.2,
        mobility=dict(stop_minutes=15, traffic_scale=1.0))
    matrix = dict(points=[[1, 1], [1, 1], [2, 2], [3, 3]], durations=[[0, 0, 300, 300]] * 4,
        places={2: dict(store='lidl-pt', opening_hours='Mo-Su 08:00-21:00'), 3: dict(store='auchan', opening_hours='')})
    lidl = dict(id='l', stores=['lidl-pt'], basket_cents=900, coverage=1, total_items=1, complete=True, route=dict(km=2, nodes=[0, 2, 1]))
    auchan = dict(id='a', stores=['auchan'], basket_cents=1000, coverage=1, total_items=1, complete=True, route=dict(km=2, nodes=[0, 3, 1]))
    result = schedule.best_windows(lambda day, base: [lidl, auchan], dict(home=matrix), profile, '2026-11-07',
        datetime(2026, 11, 6, 9, tzinfo=zone), horizon=1)
    # 21:00 closes Lidl: the late slot falls back to Auchan, whose hours are only typical.
    late = [w for w in result['windows'] if w['departure'][11:16] >= '21:00']
    assert result['windows'][0]['stores'] == ['lidl-pt'] and not result['windows'][0]['hours_unknown']
    assert all(w['stores'] == ['auchan'] and w['hours_unknown'] for w in late)


def test_projection_reuses_todays_regular_price_for_future_days_and_flags_it():
    now = datetime.now(timezone.utc)
    p = create_app.__globals__['default_profile']()
    item = dict(id='i', name='Arroz', query='arroz', quantity=1, unit='kg', checked=False, needed_on='')
    offer = dict(id='o', store='continente', country='PT', name='Arroz Carolino', size=1, unit='kg', pack='1 kg', price_cents=150,
        condition='public', vat_included=True, observed_at=now.isoformat())
    tomorrow = (now + timedelta(days=1)).date().isoformat()
    assert not make_plan([item], [offer], p, tomorrow, now)['plans']
    plan = make_plan([item], [offer], p, tomorrow, now, projection=True)['plans'][0]
    assert plan['projected'] and plan['selections'][0]['projected']
    assert not make_plan([item], [offer], p, now.date().isoformat(), now, projection=True)['plans'][0]['projected']


def test_tank_to_tank_consumption_and_cost_per_km():
    rows = [dict(day='2026-10-01', litres=40, total_cents=7000, odometer=10000, full=True),
            dict(day='2026-10-10', litres=10, total_cents=1800, odometer=10200, full=False),
            dict(day='2026-10-20', litres=26, total_cents=4600, odometer=10600, full=True),
            dict(day='2026-10-25', litres=5, total_cents=900, odometer=None, full=False)]
    m = travel.measured(rows)
    assert m['consumption'] == 6.0 and m['km'] == 600 and m['intervals'] == 1
    assert m['cost_per_km_cents'] == round((1800 + 4600) / 600, 1) and m['spent_cents'] == 14300
    assert travel.measured(rows[:1])['consumption'] is None


def test_refuel_log_updates_measured_consumption_and_is_private(tmp_path):
    app = create_app(tmp_path, testing=True)
    a, b = app.test_client(), app.test_client()
    register(a, 'driver'); register(b, 'other')
    assert a.put('/api/profile', json=dict(mobility=dict(consumption_source='refuels', consumption=5))).status_code == 200
    today = date.today()
    for days, litres, odo in [(20, 40, 50000), (10, 30, 50500)]:
        r = a.post('/api/refuels', json=dict(id=uuid.uuid4().hex, day=(today - timedelta(days=days)).isoformat(), litres=litres,
            total=litres * 1.8, odometer=odo, full=True))
        assert r.status_code == 201
    assert a.post('/api/refuels', json=dict(id=uuid.uuid4().hex, day=today.isoformat(), litres=10, total=18, odometer=100)).status_code == 400
    data = a.get('/api/refuels?month=' + today.strftime('%Y-%m')).json
    assert data['measured']['consumption'] == 6.0
    assert a.get('/api/me').json['profile']['mobility']['consumption'] == 6.0
    assert b.get('/api/refuels').json['refuels'] == []
    assert len(a.get('/api/export').json['refuels']) == 2
    app.planning.pool.shutdown()


def test_work_hours_are_validated_together(tmp_path):
    app = create_app(tmp_path, testing=True); c = app.test_client(); register(c, 'routine')
    assert c.put('/api/profile', json=dict(work_start='09:00')).status_code == 400
    assert c.put('/api/profile', json=dict(work_start='18:00', work_end='09:00')).status_code == 400
    p = c.put('/api/profile', json=dict(work_start='09:00', work_end='18:00', shop_from='08:30', shop_until='21:30')).json['profile']
    assert (p['work_start'], p['work_end'], p['shop_until']) == ('09:00', '18:00', '21:30')
    app.planning.pool.shutdown()


def test_window_run_can_be_selected_and_survives_midnight(tmp_path, monkeypatch):
    app = create_app(tmp_path, testing=True); c = app.test_client(); register(c, 'windows')
    month = date.today().strftime('%Y-%m')
    c.post('/api/items', json=dict(name='Leite', quantity=1, unit='l', month=month))
    departure = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    window = dict(plan_id='p1', day=departure.date().isoformat(), departure=departure.isoformat(),
        arrival=(departure + timedelta(minutes=40)).isoformat(), stops=[dict(store='lidl-pt')], drive_minutes=25)
    def windows(uid, month, params, report):
        report('optimizing')
        return dict(kind='windows', calculated_at=time.time(), windows=[window],
            plans=dict(p1=dict(id='p1', stores=['lidl-pt'], selections=[], basket_cents=100, route=dict(km=1, nodes=[0, 2, 1]))))
    monkeypatch.setattr(app.planning, 'calculate_windows', windows)
    run = c.post('/api/plans', json=dict(kind='windows', month=month, day=date.today().isoformat())).json['run']
    for _ in range(100):
        run = c.get('/api/plans/' + run['id']).json['run']
        if run['status'] == 'ready':
            break
        time.sleep(.02)
    assert run['status'] == 'ready'
    assert c.post('/api/plans/select', json=dict(run_id=run['id'], plan_id='7')).status_code == 400
    saved = c.post('/api/plans/select', json=dict(run_id=run['id'], plan_id='0')).json['selected']
    assert saved['departure'] == window['departure'] and saved['params']['day'] == window['day']
    selected = c.get('/api/plans/selected?month=' + month).json['selected']
    assert not selected['stale'] and not selected['expired']
    uid = c.get('/api/me').json['user']['id']
    params = dict(kind='windows', day='2026-01-01', route='auto')
    assert app.planning.selection_signature(uid, month, params) == app.planning.selection_signature(uid, month, dict(params, day='2026-01-02'))
    app.planning.pool.shutdown()


def test_plate_sequences_estimate_registration_dates():
    today = date(2026, 10, 29)
    assert sources.plate_year('3926 MXP', today)['estimate'] == '2024-12'
    assert sources.plate_year('1234-BBB', today)['estimate'] == '2000-09'
    pt = sources.plate_year('68-tr-04', today)
    assert pt['country'] == 'PT' and 2005 <= pt['year'] <= 2020 and pt['precision'] == 'approximate'
    assert sources.plate_year('AA-01-AA', today)['year_from'] == 2020 and sources.plate_year('AA-01-AA', today)['year'] is None
    for bad in ('ABC', '1234 AEI', "1'; DROP"):
        try:
            sources.plate_year(bad, today)
            raise AssertionError(bad)
        except ValueError:
            pass


def test_eea_search_sanitises_input_converts_co2_and_skips_plugins(monkeypatch):
    sent = []
    def fake(query):
        sent.append(query)
        return [dict(mk='RENAULT', cn='CLIO', ft='petrol', fm='M', cc=999, kw=67, wltp=116.5, n=900),
                dict(mk='RENAULT', cn='CLIO', ft='petrol/electric', fm='P', cc=1598, kw=67, wltp=30, n=900),
                dict(mk='RENAULT', cn='CLIO', ft='diesel', fm='M', cc=1461, kw=63, wltp=None, nedc=95.4, n=900),
                dict(mk='RENAULT', cn='CLIO', ft='petrol', fm='M', cc=1333, kw=96, wltp=140, n=3)]
    monkeypatch.setattr(sources, 'eea_post', fake)
    rows = sources.eea_search("Renault'; --", 'Clio', 2019)
    assert "'" not in sent[0].split("LIKE '")[1].split('%')[0] and 'co2cars]' in sent[0]
    assert [r['fuel'] for r in rows] == ['petrol95', 'diesel']
    assert rows[0]['consumption_lab'] == 5.0 and rows[0]['consumption'] == round(116.5 / 23.3 * 1.18, 2)
    assert rows[1]['basis'] == 'nedc' and rows[1]['consumption'] == round(95.4 / 26.5 * 1.39, 2)
    sources.eea_search('Peugeot', '208', 2024)
    assert 'co2cars_2024Fv30' in sent[-1] and 'Enedc' not in sent[-1]


def test_captcha_robots_page_counts_as_access_block(monkeypatch):
    monkeypatch.setattr(research, 'read', lambda url, limit: b'<!doctype html><title>captcha</title>')
    research._rules.clear()
    try:
        research.robots('https://example.invalid')
        raise AssertionError('expected block')
    except research.AccessBlocked as error:
        assert research.access_blocked(error)
    response = requests.Response(); response.status_code = 403
    assert research.access_blocked(requests.HTTPError(response=response))
    response.status_code = 404
    assert not research.access_blocked(requests.HTTPError(response=response))
