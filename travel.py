"""Explicit trip assumptions and comparable basket + journey estimates."""
import math
from copy import deepcopy
from datetime import date
from mobility_sources import fuel_prices,get_vehicle


def defaults():
    return dict(mode='car',vehicle_id='',vehicle_label='',vehicle=None,consumption=None,consumption_source='manual',
        fuel='petrol95',fuel_country='PT',price_mode='auto',unit_price=None,parking_per_stop=0,tolls=0,
        stop_minutes=15,time_value=0,transit_ticket=None,transit_pass=False)


def validate(data,current=None,folder=None):
    result=defaults();result.update(current or {})
    if not isinstance(data,dict):raise ValueError('Definições de deslocação inválidas')
    for key,values in {'mode':('car','transit'),'fuel':('petrol95','petrol98','diesel','lpg','electric'),
                       'fuel_country':('PT','ES'),'price_mode':('auto','manual'),'consumption_source':('manual','catalogue')}.items():
        value=data.get(key,result[key])
        if value not in values:raise ValueError('Opção de deslocação inválida: '+key)
        result[key]=value
    for key,low,high in [('consumption',.1,100),('unit_price',.01,10),('parking_per_stop',0,100),('tolls',0,500),
                         ('stop_minutes',0,180),('time_value',0,200),('transit_ticket',0,100)]:
        raw=data.get(key,result[key]);value=None if raw in (None,'') else float(raw)
        if value is not None and (not math.isfinite(value) or not low<=value<=high):raise ValueError('Valor inválido: '+key)
        if value is None and key in ('parking_per_stop','tolls','stop_minutes','time_value'):raise ValueError('Valor necessário: '+key)
        result[key]=value
    result['transit_pass']=bool(data.get('transit_pass',result['transit_pass']))
    identifier=str(data.get('vehicle_id',result['vehicle_id']))[:100]
    result['vehicle_label']=str(data.get('vehicle_label',result['vehicle_label']))[:160]
    if identifier:
        vehicle=result.get('vehicle') if identifier==result.get('vehicle_id') else None
        if not vehicle:vehicle=get_vehicle(folder,identifier)
        result.update(vehicle_id=identifier,vehicle=vehicle,vehicle_label=vehicle['label'])
        if result['consumption_source']=='catalogue':result.update(consumption=vehicle['consumption'],fuel=vehicle['fuel'])
    else:result.update(vehicle_id='',vehicle=None,consumption_source='manual')
    return result


def resolve(profile,folder):
    m=defaults();m.update(profile.get('mobility',{}));m=deepcopy(m)
    if m['mode']=='transit':return m
    m['fuel_quote']=None
    if m['price_mode']=='manual' and m.get('unit_price') is not None:
        m['fuel_quote']=dict(unit_price=m['unit_price'],source='Preço indicado por si',observed_on=date.today().isoformat(),manual=True)
    elif m['fuel']!='electric':
        try:
            data=fuel_prices(folder,m['fuel_country']);m['fuel_quote']=dict(data['prices'][m['fuel']],stale=data['stale'])
        except (ValueError,KeyError):m['fuel_error']='unavailable'
    return m


def estimate(profile,route,stops):
    m=defaults();m.update(profile.get('mobility',{}))
    unknown=dict(travel_cents=None,fuel_cents=None,extra_travel_cents=None,fuel_amount=None,travel_method='unavailable',time_cost_cents=0,decision_cents=None)
    if not route:return unknown
    if m['mode']=='transit':
        if not route.get('verified'):return unknown
        boardings=route.get('boardings')
        fare=0 if m['transit_pass'] else round(boardings*m['transit_ticket']*100) if boardings is not None and m['transit_ticket'] is not None else None
        minutes=route.get('total_minutes')
        time_cost=round(minutes/60*m['time_value']*100) if minutes is not None else 0
        return dict(unknown,travel_cents=fare,travel_method='pass' if m['transit_pass'] else 'ticket_estimate',
            decision_cents=fare+time_cost if fare is not None else None,time_cost_cents=time_cost,total_minutes=minutes,shopping_minutes=len(route.get('stops',[]))*m['stop_minutes'])
    km=route.get('total_km')
    if km is None:return unknown
    quote=m.get('fuel_quote');rate=m.get('consumption')
    if rate and quote:
        amount=km*rate/100;fuel=round(amount*quote['unit_price']*100)
        extra=round((route.get('km') or 0)*rate/100*quote['unit_price']*100)
        method='electric' if m['fuel']=='electric' else 'fuel'
    else:
        amount=None;fuel=round(km*float(profile.get('cost_per_km',.2))*100)
        extra=round((route.get('km') or 0)*float(profile.get('cost_per_km',.2))*100);method='manual_km'
    extras=round((stops*m['parking_per_stop']+m['tolls'])*100)
    minutes=route.get('total_minutes',0)+stops*m['stop_minutes']
    time_cost=round(minutes/60*m['time_value']*100)
    return dict(travel_cents=fuel+extras,fuel_cents=fuel,fuel_amount=round(amount,3) if amount is not None else None,
        extra_travel_cents=extra+extras if route.get('km') is not None else None,travel_method=method,parking_cents=round(stops*m['parking_per_stop']*100),
        tolls_cents=round(m['tolls']*100),time_cost_cents=time_cost,decision_cents=fuel+extras+time_cost,
        shopping_minutes=stops*m['stop_minutes'],total_minutes=round(minutes),fuel_quote=quote,
        consumption=rate,vehicle_label=m.get('vehicle_label',''),energy_unit='kWh' if m['fuel']=='electric' else 'L')


def summarize(result,profile):
    plans=result['plans'];m=defaults();m.update(profile.get('mobility',{}))
    for p in plans:
        cost=estimate(profile,p.get('route'),len(p['stores']));p.update(cost)
        p['total_cents']=p['basket_cents']+(p['travel_cents'] or 0)
        p['decision_total_cents']=p['basket_cents']+p['decision_cents'] if p['decision_cents'] is not None else None
        p['transport_mode']=m['mode']
    plans.sort(key=lambda p:(-p['coverage'],p['travel_cents'] is None,
        p['decision_total_cents'] if p['decision_total_cents'] is not None else p['total_cents'],len(p['stores'])))
    comparable=[p for p in plans if p['complete'] and p['travel_cents'] is not None]
    baseline=min(comparable,key=lambda p:(len(p['stores']),p['total_cents'])) if comparable else None
    for p in plans:
        p['saving_cents']=baseline['total_cents']-p['total_cents'] if baseline and p['complete'] and p['travel_cents'] is not None else None
        p['baseline_stops']=len(baseline['stores']) if baseline else None
        p['recommended']=bool(p is (comparable[0] if comparable else None))
    frontier=[]
    for n in range(1,min(4,int(profile.get('max_stops',4)))+1):
        best=next((p for p in plans if len(p['stores'])==n),None)
        frontier.append(dict(stops=n,plan_id=best['id'] if best else None,complete=best['complete'] if best else False,
            total_cents=best['total_cents'] if best and best['travel_cents'] is not None else None,
            basket_cents=best['basket_cents'] if best else None,coverage=best['coverage'] if best else 0,
            saving_cents=best.get('saving_cents') if best else None,total_minutes=best.get('total_minutes') if best else None))
    chosen=[]
    for p in plans:
        if not any(len(v['stores'])==len(p['stores']) for v in chosen):chosen.append(p)
    result.update(frontier=frontier,baseline_id=baseline['id'] if baseline else None,mobility=m,
        traffic_available=any(p.get('route',{}).get('traffic') in ('live','historic') for p in plans if p.get('route')))
    # Preserve a representative of every stop count before adding alternatives.
    selected={p['id'] for p in chosen}
    for p in plans:
        if len(chosen)>=12:break
        if p['id'] not in selected:chosen.append(p);selected.add(p['id'])
    chosen.sort(key=lambda p:plans.index(p))
    result['plans']=chosen
    return result
