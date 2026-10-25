"""Explainable basket comparison. Costs are integer cents; quantities account for whole packs."""
import itertools
import math
from datetime import datetime, timezone
from catalog import fold


def eligible(offer, prefs, day, now=None):
    now = now or datetime.now(timezone.utc)
    setting = prefs.get('stores', {}).get(offer['store'], {})
    if not setting.get('enabled') or offer['country'] not in prefs.get('countries', ['PT']):
        return False
    # Don't claim unannounced future prices or use stale observations.
    observed = datetime.fromisoformat(offer['observed_at'])
    if (now - observed).total_seconds() > 72 * 3600:
        return False
    if day < observed.date().isoformat():
        return False
    if day > now.date().isoformat() and not offer.get('valid_to'):
        return False
    if offer.get('valid_from') and day < offer['valid_from']:
        return False
    if offer.get('valid_to') and day > offer['valid_to']:
        return False
    condition = offer['condition']
    if condition == 'unknown':
        return False
    if condition == 'card' and not setting.get('card'):
        return False
    if condition == 'subscription' and not setting.get('subscription'):
        return False
    if condition == 'professional' and not setting.get('access'):
        return False
    if condition == 'coupon' and offer.get('coupon') not in setting.get('coupons', []):
        return False
    if offer['store'].startswith(('makro', 'recheio')) and not setting.get('access'):
        return False
    return offer.get('vat_included', False)


def match(item, offer):
    if not offer.get('size') or item['unit'] != offer['unit']:
        return False
    if item.get('offer_id'):
        return item['offer_id'] == offer['id']
    tokens = fold(item['query']).split()
    words = set(fold(offer['name']).split())
    # Conservative family exclusions: generic eggs are not quail/chocolate eggs,
    # and a rice drink or rice flour is not a pack of rice. Explicit queries opt in.
    families = {
        'ovos': {'codorniz', 'chocolate', 'claras', 'gemas', 'liquidos', 'pasteurizados'},
        'arroz': {'bebida', 'farinha', 'tortitas', 'bolachas', 'vinagre', 'papa', 'barras'},
        'leite': {'condensado', 'po', 'infantil', 'lactentes', 'crescimento', 'chocolate', 'creme'},
        'azeite': {'oleo', 'spray', 'aromatizado'},
        'massa': {'tomate', 'pimentao', 'folhada', 'quebrada', 'pizza'},
    }
    for family, exclusions in families.items():
        if family in tokens and (words & exclusions) - set(tokens):
            return False
    return bool(tokens) and all(t in words for t in tokens)


def route_extra(stores, prefs):
    """Sum user-entered additional route distances. Explicitly an estimate, not road routing."""
    distances = [prefs.get('stores', {}).get(store, {}).get('extra_km') for store in stores]
    if any(d is None for d in distances):
        return None
    return round(sum(distances), 2)


def make_plan(items, offers, prefs, day, now=None, road=None):
    pending = [i for i in items if not i['checked']]
    choices = {}
    for item in pending:
        candidates = []
        for o in offers:
            if eligible(o, prefs, day, now) and match(item, o):
                packs = math.ceil(round(item['quantity'] / o['size'], 9))
                candidates.append(dict(item_id=item['id'], item_name=item['name'], offer=o,
                    packs=packs, cost_cents=packs * o['price_cents'], balance_cents=packs * o.get('balance_cents', 0)))
        choices[item['id']] = sorted(candidates, key=lambda c: c['cost_cents'])
    missing = [i['name'] for i in pending if not choices[i['id']]]
    store_ids = sorted({c['offer']['store'] for options in choices.values() for c in options})
    plans = []
    maximum = min(int(prefs.get('max_stops', 2)), 3)
    for n in range(1, maximum + 1):
        for stores in itertools.combinations(store_ids, n):
            selected = [next((c for c in choices[i['id']] if c['offer']['store'] in stores), None) for i in pending]
            found = [c for c in selected if c]
            if not found:
                continue
            used = sorted({c['offer']['store'] for c in found})
            if used != list(stores):
                continue
            from routing import distance_for
            route = distance_for(used, road)
            km = route['km'] if route else route_extra(used, prefs)
            travel = round(km * float(prefs.get('cost_per_km', .2)) * 100) if km is not None else None
            basket = sum(c['cost_cents'] for c in found)
            plans.append(dict(stores=used, selections=found, coverage=len(found), total_items=len(pending),
                complete=len(found) == len(pending), basket_cents=basket, travel_cents=travel,
                total_cents=basket + travel if travel is not None else basket,
                extra_km=km, route=route, distance_method='road' if route else 'user_estimate', balance_cents=sum(c['balance_cents'] for c in found)))
    # Never rank a partially priced basket ahead of a fully covered one.
    plans.sort(key=lambda p: (-p['coverage'], p['total_cents'], len(p['stores'])))
    return dict(plans=plans[:12], missing=missing, pending=len(pending), day=day,
        comparison='keyword_suggestions', distance_method='road' if road else 'user_estimate',
        warning='Alternativas por pesquisa: confirme marca, tipo e formato. Distâncias são estimativas introduzidas por si; não são rotas calculadas.')
