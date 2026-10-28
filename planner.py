"""Explainable basket comparison. Costs are integer cents; quantities account for whole packs."""
import itertools
import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from catalog import fold, product_text, STORE_MAP


def purchase_cost(offer, quantity, unit=None):
    """Loose produce uses its requested weight; sealed packs remain indivisible."""
    if unit=='un' and offer.get('unit') in ('kg','l') and not offer.get('variable_weight'):
        packs=math.ceil(quantity)
        cost=packs*offer['price_cents']
    elif offer.get('variable_weight'):
        amount=max(float(quantity),offer.get('minimum_quantity') or 0)
        if offer.get('weight_step'):
            step=offer['weight_step']
            amount=math.ceil(round(amount/step,9))*step
        packs=round(amount/offer['size'],6)
        cost=int((Decimal(str(packs))*offer['price_cents']).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    else:
        packs=math.ceil(round(quantity/offer['size'],9))
        cost=packs*offer['price_cents']
    return packs,cost


def ineligible_reason(offer, prefs, day, now=None):
    now=now or datetime.now(timezone.utc)
    if offer.get('country') not in prefs.get('countries',['PT']):
        return 'country_disabled'
    setting=prefs.get('stores',{}).get(offer['store'],{})
    if not setting.get('enabled'):
        return 'store_disabled'
    if offer.get('available') is False:
        return 'unavailable'
    if not offer.get('vat_included',False):
        return 'vat_excluded'
    if offer.get('requires_location_confirmation'):
        return 'location_unconfirmed'
    try:
        observed=datetime.fromisoformat(offer.get('observed_at',''))
        if observed.tzinfo is None or (observed-now).total_seconds()>300:
            return 'unconfirmed_date'
    except (TypeError,ValueError):
        return 'unconfirmed_date'
    if (now-observed).total_seconds()>72*3600:
        return 'stale'
    if day<observed.date().isoformat():
        return 'past_date'
    if offer.get('valid_from') and day<offer['valid_from']:
        return 'not_started'
    if offer.get('valid_to') and day>offer['valid_to']:
        return 'expired'
    if day>now.date().isoformat() and not offer.get('valid_to'):
        return 'future_unconfirmed'
    condition=offer.get('condition','unknown')
    store=STORE_MAP.get(offer['store'],{})
    if condition=='unknown':
        return 'unknown_conditions'
    if condition=='card' and (not store.get('loyalty') or not setting.get('card')):
        return 'card_required'
    subscription=store.get('subscription')
    if condition=='subscription' and (not subscription or subscription['kind']!='product' or not setting.get('subscription')):
        return 'subscription_required'
    if condition=='professional' and (not store.get('professional') or not setting.get('access')):
        return 'professional_required'
    if condition=='coupon' and offer.get('coupon') not in setting.get('coupons',[]):
        return 'coupon_required'
    if offer['store'].startswith(('makro','recheio')) and not setting.get('access'):
        return 'professional_required'
    if condition not in ('public','card','subscription','professional','coupon'):
        return 'unknown_conditions'
    return None


def eligible(offer,prefs,day,now=None):
    return ineligible_reason(offer,prefs,day,now) is None


def match(item, offer):
    package_count=item['unit']=='un' and offer.get('unit') in ('kg','l') and not offer.get('variable_weight')
    if not offer.get('size') or (item['unit'] != offer['unit'] and not package_count):
        return False
    if item.get('offer_id'):
        return item['offer_id'] == offer['id']
    if item.get('family'):
        from products import family
        return family(offer)['key'] == item['family']
    from searching import rank,tokens as search_tokens,product_query
    tokens=search_tokens(item['query'])
    words=set(search_tokens(offer['name']))
    # Conservative family exclusions: generic eggs are not quail/chocolate eggs,
    # and a rice drink or rice flour is not a pack of rice. Explicit queries opt in.
    families = {
        'ovos': {'codorniz', 'chocolate', 'claras', 'gemas', 'liquidos', 'pasteurizados'},
        'arroz': {'bebida', 'farinha', 'tortitas', 'bolachas', 'vinagre', 'papa', 'barras', 'leite', 'sobremesa'},
        'leite': {'condensado', 'po', 'infantil', 'lactentes', 'crescimento', 'chocolate', 'creme'},
        'azeite': {'oleo', 'spray', 'aromatizado'},
        'massa': {'tomate', 'pimentao', 'folhada', 'quebrada', 'pizza'},
        'cereais': {'barra','barras','barrita','barritas','bar'},
        **{fruit:{'iogurte','bebida','sumo','pure','papa','bolachas','bolacha','gelado','congelada','seca','desidratada','chips','sabor'}
           for fruit in ('banana','maca','pera','laranja','morango','uva')},
        **{meat:{'racao','alimento','cao','gato','caes','gatos','sabor','caldo','sopa','refeicao','lasanha','empada','panado','panados','cozinhado','caril','noodles'}
           for meat in ('frango','porco','vaca','peru','carne')},
        'agua':{'tonica','coco','oxigenada','destilada','fruta','sabores','limao','colonia'},
    }
    for family, exclusions in families.items():
        if search_tokens(family)[0] in tokens and (words & set(search_tokens(' '.join(sorted(exclusions))))) - set(tokens):
            return False
    return bool(tokens) and bool(rank(product_query(item['query']),offer['name'],offer.get('brand',''),offer.get('pack','')))


def make_plan(items, offers, prefs, day, now=None, road=None):
    pending = [i for i in items if not i['checked']]
    choices = {}
    for item in pending:
        candidates = []
        for o in offers:
            if eligible(o, prefs, day, now) and match(item, o):
                packs,cost = purchase_cost(o,item['quantity'],item['unit'])
                candidates.append(dict(item_id=item['id'], item_name=item['name'], offer=o,
                    packs=packs, cost_cents=cost, estimated=bool(o.get('variable_weight')),
                    quantity_basis='packages' if item['unit']=='un' and o['unit'] in ('kg','l') else 'content',
                    balance_cents=round(packs * o.get('balance_cents', 0))))
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
            km = route['km'] if route else None
            travel = round(km * float(prefs.get('cost_per_km', .2)) * 100) if km is not None else None
            basket = sum(c['cost_cents'] for c in found)
            plans.append(dict(stores=used, selections=found, coverage=len(found), total_items=len(pending),
                missing=[i['name'] for i,c in zip(pending,selected) if not c],
                complete=len(found) == len(pending), basket_cents=basket, travel_cents=travel,
                total_cents=basket + travel if travel is not None else basket,
                extra_km=km, route=route, distance_method='road' if route else 'unavailable', balance_cents=sum(c['balance_cents'] for c in found)))
    # Never rank a partially priced basket ahead of a fully covered one.
    plans.sort(key=lambda p: (-p['coverage'], p['total_cents'], len(p['stores'])))
    return dict(plans=plans[:12], missing=missing, pending=len(pending), day=day,
        comparison='keyword_suggestions', distance_method='road' if road else 'unavailable',
        warning='Confirme marca, tipo, formato e disponibilidade na loja. Percursos por estrada calculados a partir de casa e trabalho; sem resposta do serviço, a deslocação fica por confirmar.')
