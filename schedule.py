"""When to shop: departure windows around the work routine, typical traffic and opening hours.

Every window is costed as the *extra* trip beyond what would be driven anyway:
after work the commute work→home is sunk, before work home→work is sunk, and on
days off the whole home→shops→home loop counts.
"""
import math
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

# Travel-time multiplier over OSRM free flow, by local hour. Derived from the
# TomTom Traffic Index 2025 hourly profile for Lisbon metro (Porto is within a
# few %), plus ~5–8 % because OSRM's urban free flow is optimistic even at night.
# ponytail: one national curve applied to the whole route (motorway legs
# included); per-city curves, or live TomTom data when DESPENSA_TOMTOM_KEY is set.
WEEKDAY = [1.06, 1.05, 1.05, 1.05, 1.05, 1.08, 1.15, 1.35, 1.65, 1.51, 1.33, 1.3,
           1.29, 1.3, 1.3, 1.34, 1.45, 1.65, 1.69, 1.48, 1.28, 1.17, 1.12, 1.08]
SATURDAY = [1.05] * 8 + [1.08, 1.12, 1.2, 1.27, 1.3, 1.25, 1.18, 1.2, 1.25, 1.28, 1.27, 1.2, 1.12, 1.08, 1.06, 1.05]
SUNDAY = [1.05] * 9 + [1.07, 1.1, 1.15, 1.18, 1.15, 1.1, 1.12, 1.15, 1.18, 1.2, 1.15, 1.1, 1.07, 1.05, 1.05]
# Unknown branch hours fall back to the usual national pattern, flagged as unconfirmed.
TYPICAL_HOURS = {'PT': 'Mo-Su 08:30-21:00', 'ES': 'Mo-Sa 09:00-21:00'}


def opening(text):
    """Common OSM opening_hours → {weekday: [(start_min, end_min)]}; None when not understood."""
    text = (text or '').strip()
    if not text:
        return None
    if text == '24/7':
        return {d: [(0, 1440)] for d in range(7)}
    week = {}
    day = r'(?:Mo|Tu|We|Th|Fr|Sa|Su)'
    for rule in text.split(';'):
        rule = rule.strip()
        if not rule:
            continue
        m = re.fullmatch(rf'((?:(?:{day}(?:-{day})?|PH)\s*,?\s*)+)?\s*(off|closed|(?:\d\d?:\d\d-\d\d?:\d\d\s*,?\s*)+)', rule)
        if not m:
            return None
        days = set()
        if m.group(1):
            for part in re.split(r'[,\s]+', m.group(1).strip()):
                if part in ('', 'PH'):
                    continue
                a, _, b = part.partition('-')
                i, j = DAYS.index(a), DAYS.index(b or a)
                days.update(range(i, j + 1) if i <= j else [*range(i, 7), *range(0, j + 1)])
            if not days:
                continue  # holiday-only rule
        else:
            days = set(range(7))
        spans = []
        if m.group(2) not in ('off', 'closed'):
            for start, end in re.findall(r'(\d\d?:\d\d)-(\d\d?:\d\d)', m.group(2)):
                a, b = (int(x.split(':')[0]) * 60 + int(x.split(':')[1]) for x in (start, end))
                spans.append((a, b if b > a else b + 1440))
        for d in days:
            week[d] = spans
    return week or None


def is_open(week, arrive, leave):
    start = arrive.hour * 60 + arrive.minute
    end = start + math.ceil((leave - arrive).total_seconds() / 60)
    return any(a <= start and end <= b for a, b in week.get(arrive.weekday(), []))


def congestion(when, scale=1.0):
    """Travel-time multiplier at a local time, interpolated between hours."""
    curve = SUNDAY if when.weekday() == 6 else SATURDAY if when.weekday() == 5 else WEEKDAY
    h = when.hour + when.minute / 60
    a, b = curve[int(h) % 24], curve[(int(h) + 1) % 24]
    return 1 + scale * (a + (b - a) * (h - int(h)) - 1)


def hours_for(place, country):
    week = opening(place.get('opening_hours'))
    return (week, True) if week else (opening(TYPICAL_HOURS.get(country, TYPICAL_HOURS['PT'])), False)


def drive(matrix, nodes, depart, stop_minutes, scale, country):
    """Timeline of one ordered trip; durations come from the free-flow matrix × congestion."""
    t, free, loaded, stops, durations = depart, 0.0, 0.0, [], matrix['durations']
    for a, b in zip(nodes, nodes[1:]):
        seconds = durations[a][b]
        factor = congestion(t, scale)
        free += seconds
        loaded += seconds * factor
        t += timedelta(seconds=seconds * factor)
        if b >= 2:
            place = matrix.get('places', {}).get(b, {})
            week, known = hours_for(place, country)
            leave = t + timedelta(minutes=stop_minutes)
            stops.append(dict(store=place.get('store'), name=place.get('name', ''), address=place.get('address', ''),
                coords=place.get('coords'), arrive=t.isoformat(), leave=leave.isoformat(),
                hours_known=known, open=is_open(week, t, leave)))
            t = leave
    return dict(end=t, free_seconds=free, seconds=loaded, stops=stops, factor=loaded / free if free else 1.0)


def plan_nodes(route):
    return route.get('nodes') if route else None


def slots(day, profile, now, zone):
    """Candidate (kind, base, departure | arrive_by) moments for one day."""
    local = lambda clock: datetime.fromisoformat(f'{day}T{clock}').replace(tzinfo=zone)
    work = bool(profile.get('work_coords')) and date.fromisoformat(day).weekday() in profile.get('workdays', [])
    start, end = profile.get('shop_from') or '09:00', profile.get('shop_until') or '21:00'
    found = []
    if work and profile.get('work_start') and profile.get('work_end'):
        found.append(('before_work', 'morning', dict(arrive_by=local(profile['work_start']))))
        found.append(('after_work', 'work', dict(depart=local(profile['work_end']))))
        later = local(profile['work_end']) + timedelta(hours=2)
        later += timedelta(minutes=-later.minute % 30)
        if later <= local(end) - timedelta(minutes=45):
            found.append(('evening_home', 'home', dict(depart=later)))
    elif not work:
        t = local(start)
        while t <= local(end) - timedelta(minutes=60):
            found.append(('day_off', 'home', dict(depart=t)))
            t += timedelta(hours=1)
    return found


def evaluate(plan, matrix, moment, profile, rate_cents, country, now, scale):
    m = profile['mobility']
    nodes = plan_nodes(plan.get('route'))
    if not nodes or not matrix:
        return None
    stops, stay = len(plan['stores']), m.get('stop_minutes', 15)
    if 'arrive_by' in moment:
        # Leave early enough to reach work on time; congestion depends on the
        # departure itself, so settle it in a few fixed-point steps.
        target = moment['arrive_by'] - timedelta(minutes=5)
        depart = target
        for _ in range(4):
            depart -= drive(matrix, nodes, depart, stay, scale, country)['end'] - target
        depart = depart.replace(second=0, microsecond=0) - timedelta(minutes=depart.minute % 5)
    else:
        depart = moment['depart']
    if depart < now + timedelta(minutes=10):
        return None
    trip = drive(matrix, nodes, depart, stay, scale, country)
    base = drive(matrix, [0, 1], depart, 0, scale, country) if matrix['points'][0] != matrix['points'][1] else dict(seconds=0)
    route = plan['route']
    extra_minutes = max(0, round((trip['seconds'] - base['seconds']) / 60)) + stops * stay
    # Stop-and-go burns more fuel than free flow; half the time penalty is a
    # common urban rule of thumb. ponytail: flat factor, calibrate from refuels.
    fuel_factor = 1 + .5 * (trip['factor'] - 1)
    extra_fuel = round((route.get('km') or 0) * rate_cents * fuel_factor)
    extras = round((stops * m.get('parking_per_stop', 0) + m.get('tolls', 0)) * 100)
    time_cost = round(extra_minutes / 60 * m.get('time_value', 0) * 100)
    closed = [s for s in trip['stops'] if not s['open']]
    return dict(plan_id=plan['id'], departure=depart.isoformat(), arrival=trip['end'].isoformat(),
        drive_minutes=round(trip['seconds'] / 60), free_flow_minutes=round(trip['free_seconds'] / 60),
        extra_minutes=extra_minutes, extra_km=route.get('km'), total_km=route.get('total_km'),
        traffic_factor=round(trip['factor'], 2), extra_fuel_cents=extra_fuel, extras_cents=extras,
        time_cost_cents=time_cost, trip_cents=extra_fuel + extras,
        decision_cents=plan['basket_cents'] + extra_fuel + extras + time_cost,
        stops=trip['stops'], closed=bool(closed), hours_unknown=any(not s['hours_known'] for s in trip['stops']))


def km_rate(profile):
    """Cents per km from the vehicle's consumption and energy price, else the declared €/km."""
    m = profile['mobility']
    quote, rate = m.get('fuel_quote'), m.get('consumption')
    if rate and quote:
        return rate / 100 * quote['unit_price'] * 100, 'vehicle'
    return float(profile.get('cost_per_km', .2)) * 100, 'per_km'


def best_windows(make_day_plans, matrices, profile, start_day, now, zone_name='Europe/Lisbon', horizon=7, per_slot=8, scale=None):
    """Rank every (day, moment, shops) option over the horizon by its decision cost.

    make_day_plans(day, base) returns ranked plan dicts (with route.nodes) for that day/base.
    """
    zone = ZoneInfo(zone_name)
    now = now.astimezone(zone)
    country = (profile.get('countries') or ['PT'])[0]
    scale = profile['mobility'].get('traffic_scale', 1.0) if scale is None else scale
    rate, rate_source = km_rate(profile)
    windows, plans = [], {}
    for offset in range(horizon):
        day = (date.fromisoformat(start_day) + timedelta(days=offset)).isoformat()
        cache = {}
        for kind, base, moment in slots(day, profile, now, zone):
            matrix = matrices.get(base)
            if not matrix:
                continue
            if base not in cache:
                cache[base] = make_day_plans(day, base)
            options = [p for p in cache[base] if p.get('route')][:per_slot]
            best = None
            for plan in options:
                value = evaluate(plan, matrix, moment, profile, rate, country, now, scale)
                if not value or value['closed']:
                    continue
                key = (-plan['coverage'], value['decision_cents'], value['extra_minutes'])
                if best is None or key < best[0]:
                    best = (key, value, plan)
            if best:
                _, value, plan = best
                plans[plan['id']] = plan
                windows.append(dict(value, day=day, kind=kind, base=base, coverage=plan['coverage'],
                    total_items=plan['total_items'], complete=plan['complete'], basket_cents=plan['basket_cents'],
                    stores=plan['stores'], projected=plan.get('projected', False)))
    windows.sort(key=lambda w: (-w['coverage'], w['decision_cents'], w['extra_minutes'], w['departure']))
    for w in windows:
        w['versus_best_cents'] = w['decision_cents'] - windows[0]['decision_cents'] if w['coverage'] == windows[0]['coverage'] else None
    days = {}
    for i, w in enumerate(windows):
        days.setdefault(w['day'], i)
    return dict(windows=windows, plans=plans, best=windows[0] if windows else None,
        day_best=[dict(day=d, index=i) for d, i in sorted(days.items())],
        assumptions=dict(traffic='typical_curve', traffic_scale=scale, km_rate_cents=round(rate, 2), km_rate_source=rate_source,
            horizon=horizon, start_day=start_day))


def _selfcheck():
    week = opening('Mo-Sa 08:00-21:00; Su 09:00-13:00; PH off')
    assert week[0] == [(480, 1260)] and week[6] == [(540, 780)]
    assert opening('Mo-Fr 08:00-12:00,14:00-19:00')[2] == [(480, 720), (840, 1140)] and 5 not in opening('Mo-Fr 08:00-12:00')
    assert opening('Mo-Su 08:00-24:00')[3] == [(480, 1440)] and opening('foo bar') is None and opening('24/7')[5] == [(0, 1440)]
    zone = ZoneInfo('Europe/Lisbon')
    sunday = datetime(2026, 11, 1, 12, 50, tzinfo=zone)
    assert not is_open(week, sunday, sunday + timedelta(minutes=15)) and is_open(week, sunday - timedelta(hours=1), sunday - timedelta(minutes=45))
    rush, night = datetime(2026, 11, 2, 18, tzinfo=zone), datetime(2026, 11, 2, 3, tzinfo=zone)
    assert congestion(rush) > 1.6 and congestion(night) < 1.1 and congestion(rush, 0) == 1
    # Work 09:00–18:00 on Monday; matrix: 0=work, 1=home, 2=shop next to home.
    profile = dict(work_coords=[0, 0], workdays=[0], work_start='09:00', work_end='18:00', countries=['PT'],
        mobility=dict(stop_minutes=15, consumption=6, fuel_quote=dict(unit_price=1.8), traffic_scale=1.0), cost_per_km=.2)
    kinds = [k for k, _, _ in slots('2026-11-02', profile, datetime(2026, 11, 2, 6, tzinfo=zone), zone)]
    assert kinds == ['before_work', 'after_work', 'evening_home'], kinds
    assert all(k == 'day_off' for k, _, _ in slots('2026-11-07', profile, datetime(2026, 11, 2, 6, tzinfo=zone), zone))
    work_home = dict(points=[[0, 0], [1, 1], [2, 2]], durations=[[0, 1200, 1300], [1200, 0, 120], [1300, 120, 0]],
        places={2: dict(store='lidl-pt', name='Lidl', opening_hours='Mo-Sa 08:00-21:00')})
    home = dict(work_home, points=[[1, 1], [1, 1], [2, 2]], durations=[[0, 0, 120], [0, 0, 120], [120, 120, 0]])
    plan = dict(id='p', stores=['lidl-pt'], basket_cents=1000, coverage=1, total_items=1, complete=True,
        route=dict(km=1.0, total_km=1.0, nodes=[0, 2, 1]))
    result = best_windows(lambda day, base: [plan], dict(work=work_home, home=home), profile, '2026-11-02',
        datetime(2026, 11, 2, 6, tzinfo=zone), horizon=1)
    assert result['best'] and result['best']['day'] == '2026-11-02'
    after = next(w for w in result['windows'] if w['kind'] == 'after_work')
    assert after['traffic_factor'] > 1.4 and after['extra_minutes'] >= 15 and after['stops'][0]['open']
    late = next(w for w in result['windows'] if w['kind'] == 'evening_home')
    assert late['traffic_factor'] < after['traffic_factor']
    return True


if __name__ == '__main__':
    print('schedule selfcheck', _selfcheck())
