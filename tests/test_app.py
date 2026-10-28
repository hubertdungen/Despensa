import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
import pytest
from app import create_app, default_profile
from catalog import cents, pack_size, parse_retailer
from planner import make_plan, match
from routing import distance_for


@pytest.fixture
def app(tmp_path):
    return create_app(tmp_path, testing=True)


def register(client, username='tester'):
    r=client.post('/api/auth/register', json=dict(username=username, password='a-good-password-123'))
    assert r.status_code==200
    return r.json


def test_auth_required_and_cross_site_rejected(app):
    c=app.test_client()
    assert c.get('/api/items').status_code==401
    assert c.post('/api/auth/register',json={},headers={'Origin':'https://attacker.example'}).status_code==403
    assert c.post('/api/items',data='hello').status_code==415


def test_private_data_and_idempotent_offline_sync(app):
    a,b=app.test_client(),app.test_client()
    register(a,'alice');register(b,'bob')
    payload=dict(name='Leite',quantity=2,unit='l',client_id='a'*32,month='2026-10')
    one=a.post('/api/items',json=payload)
    assert one.status_code==201
    assert a.post('/api/items',json=payload).status_code==200
    assert len(a.get('/api/items?month=2026-10').json['items'])==1
    assert b.get('/api/items?month=2026-10').json['items']==[]
    assert b.patch('/api/items/'+'a'*32,json={'checked':True}).status_code==404
    assert a.patch('/api/items/'+'a'*32,json={'checked':True}).json['item']['checked'] is True


def test_manual_offers_private_and_url_validation(app):
    a,b=app.test_client(),app.test_client();register(a,'alice');register(b,'bob')
    d=dict(name='Arroz',store='auchan',price='1.25',size=1,unit='kg',condition='card',vat_included=True)
    assert a.post('/api/offers/manual',json=dict(d,source_url='javascript:alert(1)')).status_code==400
    assert a.post('/api/offers/manual',json=d).status_code==201
    assert a.get('/api/offers').json['total']==1
    assert b.get('/api/offers').json['total']==0
    assert a.post('/api/offers/manual',json=dict(d,condition='coupon')).status_code==400


def test_copy_month_resets_checks_and_deduplicates(app):
    c=app.test_client();register(c)
    c.post('/api/items',json=dict(name='Leite',quantity=2,unit='l',month='2026-09',checked=True))
    assert c.post('/api/items/copy',json={'source':'2026-09','target':'2026-10'}).json['copied']==1
    assert c.post('/api/items/copy',json={'source':'2026-09','target':'2026-10'}).json['copied']==0
    assert c.get('/api/items?month=2026-10').json['items'][0]['checked'] is False


def test_profile_validations(app):
    c=app.test_client();register(c)
    for d in [{'countries':[]},{'interval_hours':0},{'cost_per_km':float('nan')},{'home_coords':[200,0]}]:
        assert c.put('/api/profile',json=d).status_code==400
    assert c.put('/api/profile',json={'locale':'es-ES','countries':['PT','ES']}).json['profile']['locale']=='es-ES'


def test_export_contains_only_own_data(app):
    c=app.test_client();register(c)
    assert c.get('/api/export').json['version']==1
    assert 'password' not in c.get('/api/export').get_data(as_text=True)
    assert c.get('/.env').status_code==404
    assert c.get('/static/../app.py').status_code==404


def offer(id='a',store='continente',price=100,condition='public',size=1,**kwargs):
    return dict(id=id,store=store,country='PT',name='Arroz carolino',price_cents=price,condition=condition,
        size=size,unit='kg',observed_at='2026-10-25T12:00:00+00:00',vat_included=True,**kwargs)


NOW=datetime(2026,10,25,15,tzinfo=timezone.utc)
ITEM=dict(id='i1',name='Arroz',query='arroz carolino',quantity=1.5,unit='kg',checked=False)


def test_whole_packs_not_unit_price_illusion():
    p=default_profile()
    result=make_plan([ITEM],[offer(price=120),offer('b',price=500,size=5)],p,'2026-10-25',NOW)
    chosen=result['plans'][0]['selections'][0]
    assert chosen['cost_cents']==240 and chosen['packs']==2


@pytest.mark.parametrize('condition',['card','subscription','coupon','professional','unknown'])
def test_ineligible_discounts_are_never_cheapest(condition):
    p=default_profile()
    result=make_plan([ITEM],[offer('a',price=100),offer('b',price=10,condition=condition)],p,'2026-10-25',NOW)
    assert result['plans'][0]['selections'][0]['offer']['id']=='a'


def test_card_and_balance_do_not_fake_payable_price():
    p=default_profile();p['stores']['continente']['card']=True
    result=make_plan([ITEM],[offer(price=100,condition='card',balance_cents=90)],p,'2026-10-25',NOW)
    assert result['plans'][0]['basket_cents']==200
    assert result['plans'][0]['balance_cents']==180


def test_stale_unknown_vat_and_future_prices_excluded():
    p=default_profile()
    stale=offer();stale['observed_at']='2026-10-20T00:00:00+00:00'
    no_vat=offer('b');no_vat['vat_included']=False
    assert make_plan([ITEM],[stale,no_vat],p,'2026-10-25',NOW)['plans']==[]
    assert make_plan([ITEM],[offer()],p,'2026-10-26',NOW)['plans']==[]
    valid=offer(valid_from='2026-10-25',valid_to='2026-10-29')
    assert make_plan([ITEM],[valid],p,'2026-10-26',NOW)['plans']


def test_partial_basket_never_wins_by_omitting_items():
    p=default_profile();p['max_stops']=1
    items=[ITEM,dict(ITEM,id='i2',name='Azeite',query='azeite')]
    oil=offer('oil',store='auchan',price=600);oil['name']='Azeite'
    r=make_plan(items,[offer('cheap',price=1),offer('other',store='auchan',price=200),oil],p,'2026-10-25',NOW)
    assert r['plans'][0]['coverage']==2
    assert r['plans'][1]['coverage']==1


def test_language_country_isolation_and_exact_reference():
    p=default_profile()
    es=offer();es['country']='ES'
    assert not make_plan([ITEM],[es],p,'2026-10-25',NOW)['plans']
    assert not make_plan([dict(ITEM,offer_id='different')],[offer()],p,'2026-10-25',NOW)['plans']


def test_cents_and_ambiguous_formats():
    assert cents('1,29 €')==129
    assert pack_size('6 x 200 ml')==(1.2,'l')
    assert pack_size('12 un')==(12.0,'un')
    assert pack_size('pack familiar')==(None,None)
    for value in ['NaN','-1','Infinity']:
        with pytest.raises(ValueError):cents(value)


def test_family_exclusions_prevent_misleading_generic_substitutions():
    item=dict(ITEM,query='ovos',unit='un')
    egg=offer();egg.update(unit='un',name='Ovos de codorniz')
    assert not match(item,egg)
    assert match(dict(item,query='ovos codorniz'),egg)
    rice=offer();rice['name']='Farinha de arroz'
    assert not match(dict(ITEM,query='arroz'),rice)


def test_parser_uses_displayed_price_over_analytics():
    html='''<div data-product-tile-impression='{"id":"1","name":"Arroz","price":9,"brand":"X"}'>
    <a href="/produto/arroz.html">Arroz</a><p class="pwc-tile--quantity">emb. 1 kg</p>
    <span class="pwc-tile--price-primary">1<span>,29€</span></span></div>'''
    parsed=parse_retailer(html,'continente')[0]
    assert parsed['price_cents']==129 and parsed['unit']=='kg'
    conditional=parse_retailer(html.replace('</div>','<span>Com cartão</span></div>'),'continente')[0]
    assert conditional['condition']=='unknown'


def test_asymmetric_road_route_and_commute_baseline():
    matrix=dict(ids={'a':2,'b':3},distances=[[0,10000,5000,8000],[10000,0,6000,3000],[5000,6000,0,2000],[8000,3000,9000,0]],
        durations=[[0,600,300,480],[600,0,360,180],[300,360,0,120],[480,180,540,0]],base='work')
    result=distance_for(['a','b'],matrix)
    assert result['order']==['a','b']
    assert result['km']==0 and result['extra_minutes']==0
    assert result['total_km']==10 and result['base_km']==10 and result['total_minutes']==10
    assert distance_for(['unknown'],matrix) is None


def test_locations_partial_save_preserves_other_origin_and_invalidates_changed_address(app):
    c=app.test_client();register(c)
    c.put('/api/profile',json={'home':'Casa confirmada','home_coords':[-9.1,38.7]})
    p=c.put('/api/profile',json={'work':'Trabalho confirmado','work_coords':[-9.2,38.8]}).json['profile']
    assert p['home']=='Casa confirmada' and p['home_coords']==[-9.1,38.7]
    assert p['work_coords']==[-9.2,38.8]
    p=c.put('/api/profile',json={'home':'Nova casa'}).json['profile']
    assert p['home_coords'] is None and p['work_coords']==[-9.2,38.8]


def test_plan_explains_missing_home_instead_of_silent_null_distance(app,monkeypatch):
    import nearby
    c=app.test_client();register(c)
    c.post('/api/items',json=dict(name='Arroz',query='arroz',quantity=1,unit='kg'))
    c.post('/api/offers/manual',json=dict(name='Arroz',store='auchan',price='1.25',size=1,unit='kg',condition='public',vat_included=True))
    monkeypatch.setattr(nearby,'discover',lambda p:(_ for _ in ()).throw(AssertionError('No origin')))
    plans=c.get('/api/plan?roads=true').json['plans']
    assert plans and plans[0]['distance_reason']=='missing_home'
    assert plans[0]['travel_cents'] is None


def test_partial_plans_report_the_products_missing_from_each_basket():
    p=default_profile()
    a=dict(ITEM,id='a',name='Arroz',query='arroz',quantity=1)
    b=dict(ITEM,id='b',name='Azeite',query='azeite',quantity=1,unit='l')
    rice=offer()
    oil=dict(offer('oil',store='auchan'),name='Azeite',unit='l')
    plans=make_plan([a,b],[rice,oil],p,'2026-10-25',NOW)['plans']
    assert plans[0]['complete'] and plans[0]['missing']==[]
    assert all(plan['missing'] for plan in plans[1:])
    assert {tuple(plan['missing']) for plan in plans[1:]}=={('Arroz',),('Azeite',)}


def test_packages_keep_their_cost_and_loose_produce_requires_weight():
    from planner import purchase_cost
    cereal=dict(offer('cereal',size=.625),name='Cereais Fitness',brand='Fitness',pack='625 g')
    item=dict(ITEM,query='Cereais Linha e Fibra Fitness',unit='un',quantity=1)
    assert match(item,cereal)
    assert purchase_cost(cereal,1,'un')==(1,100)
    assert purchase_cost(cereal,2,'un')==(2,200)
    assert purchase_cost(cereal,1,'kg')==(2,200)
    assert not match(dict(item,query='banana'),dict(cereal,name='Banana',variable_weight=True))


def test_zero_additional_km_still_reports_total_trip_and_selects_fastest_tied_route():
    matrix=dict(ids={'a':[2,3]},base='work',distances=[[0,10000,5000,4000],[10000,0,1,1],[1,5000,0,1],[1,4000,1,0]],
        durations=[[0,600,400,200],[600,0,1,1],[1,400,0,1],[1,200,1,0]],places={2:{'name':'Slow'},3:{'name':'Fast'}})
    result=distance_for(['a'],matrix)
    assert result['km']==0 and result['total_km']==8 and result['base_km']==10
    assert result['stops'][0]['name']=='Fast'


def test_unknown_travel_cost_cannot_undercut_same_coverage_with_a_known_route():
    matrix=dict(ids={'continente':2},base='home',distances=[[0,0,1000],[0,0,1000],[1000,1000,0]],
        durations=[[0,0,60],[0,0,60],[60,60,0]])
    plans=make_plan([ITEM],[offer('known',price=100),offer('unknown',store='pingo-doce',price=1)],
        default_profile(),'2026-10-25',NOW,road=matrix)['plans']
    assert plans[0]['stores']==['continente'] and plans[0]['travel_cents'] is not None
    assert plans[1]['stores']==['pingo-doce'] and plans[1]['travel_cents'] is None
