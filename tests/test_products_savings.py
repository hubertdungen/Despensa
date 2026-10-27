import json
from datetime import date, datetime, timezone
from app import create_app, default_profile
from products import family, comparisons
from planner import make_plan
from routing import distance_for
from nearby import chain_for, haversine


def milk(oid,store,price=100,**extra):
    return dict(id=oid,store=store,country='PT',name='Leite UHT meio gordo',size=1,unit='l',price_cents=price,
        condition='public',observed_at=datetime.now(timezone.utc).isoformat(),vat_included=True,
        pack='1 l',source_url='https://example.test/milk',source_kind='manual',**extra)


def test_comparisons_preserve_unit_and_milk_variants():
    normal=milk('one','continente')
    lactose=dict(normal,id='free',name='Leite UHT meio gordo sem lactose')
    fresh=dict(normal,id='fresh',name='Leite fresco meio gordo')
    magro=dict(normal,id='skim',name='Leite UHT magro')
    assert len({family(o)['key'] for o in [normal,lactose,fresh,magro]})==4
    groups=comparisons([normal,milk('two','auchan',90)],default_profile())
    assert len(groups)==1 and groups[0]['store_count']==2
    assert groups[0]['best_id']=='two'
    assert groups[0]['saving_per_unit_cents']==10
    assert comparisons([normal,dict(milk('two','auchan',90),condition='unknown')],default_profile())[0]['store_count']==1


def test_family_selection_matches_multiple_stores_but_not_lactose_variant():
    from planner import match
    base=milk('a','continente')
    item=dict(name='Leite',query='leite',quantity=2,unit='l',family=family(base)['key'])
    assert match(item,milk('b','auchan'))
    assert not match(item,dict(milk('c','auchan'),name='Leite UHT meio gordo sem lactose'))


def test_recorded_savings_are_monthly_private_frozen_and_not_counted_twice(tmp_path):
    app=create_app(tmp_path,testing=True);a=app.test_client();b=app.test_client()
    for c,name in [(a,'alice'),(b,'bob')]:
        c.post('/api/auth/register',json={'username':name,'password':'temporary-password'})
    a.put('/api/profile',json={'reference_store':'continente'})
    with app.database() as db:
        for o in [milk('one','continente',100),milk('two','auchan',90)]:
            db.execute('INSERT INTO offers VALUES(?,?,?,?)',(o['id'],'',o['store'],json.dumps(o)))
    item=a.post('/api/items',json=dict(name='Leite',query='leite meio gordo',quantity=2,unit='l')).json['item']
    data=dict(id='a'*32,item_id=item['id'],store='auchan',paid='1.80',purchased_on=date.today().isoformat())
    assert a.post('/api/purchases',json=data).status_code==201
    assert a.post('/api/purchases',json=data).status_code==200
    assert a.post('/api/purchases',json=dict(data,id='b'*32)).status_code==409
    summary=a.get('/api/savings').json['savings']
    assert summary['product_savings_cents']==20 and summary['spent_cents']==180
    assert summary['net_savings_cents'] is None
    assert b.get('/api/savings').json['savings']['purchase_count']==0
    # Market prices changing later cannot rewrite the saved purchase benchmark.
    with app.database() as db:
        o=milk('one','continente',999)
        db.execute('UPDATE offers SET data=? WHERE id=?',(json.dumps(o),'one'))
    assert a.get('/api/savings').json['savings']['product_savings_cents']==20
    a.post('/api/trips',json=dict(id='c'*32,day=date.today().isoformat(),cost='0.10'))
    assert a.get('/api/savings').json['savings']['net_savings_cents']==10
    assert b.delete('/api/purchases/'+'a'*32,json={}).status_code==200
    assert a.get('/api/savings').json['savings']['purchase_count']==1
    a.delete('/api/purchases/'+'a'*32,json={})
    assert not a.get('/api/items').json['items'][0]['checked']


def test_no_reference_means_no_claimed_savings(tmp_path):
    app=create_app(tmp_path,testing=True);c=app.test_client()
    c.post('/api/auth/register',json={'username':'alice','password':'temporary-password'})
    item=c.post('/api/items',json=dict(name='Leite',unit='l')).json['item']
    r=c.post('/api/purchases',json=dict(id='a'*32,item_id=item['id'],store='auchan',paid='2.00'))
    assert r.status_code==201
    assert r.json['purchase']['reference_cents'] is None
    assert c.get('/api/savings').json['savings']['product_savings_cents'] is None
    assert c.get('/api/savings?month=2025-01').json['savings']['purchase_count']==0


def test_routes_choose_physical_branch_and_do_not_use_manual_km():
    matrix=dict(ids={'continente':[2,3]},distances=[[0,0,10000,1000],[0,0,10000,1000],[10000,10000,0,9000],[1000,1000,9000,0]],
        durations=[[0,0,1000,100],[0,0,1000,100],[1000,1000,0,900],[100,100,900,0]],
        places={2:{'name':'Far'},3:{'name':'Near'}},base='home')
    r=distance_for(['continente'],matrix)
    assert r['km']==2 and r['stops'][0]['name']=='Near'
    p=default_profile();p['stores']['continente']['extra_km']=99
    item=dict(id='item',name='Leite',query='leite',quantity=1,unit='l',checked=False)
    assert make_plan([item],[milk('m','continente')],p,date.today().isoformat())['plans'][0]['extra_km'] is None


def test_chain_country_is_preserved():
    assert chain_for({'name':'Mercadona'},'PT')=='mercadona-pt'
    assert chain_for({'name':'Mercadona'},'ES')=='mercadona-es'
    assert 0<haversine([-9.1,38.7],[-9.11,38.71])<2


def test_discovery_keeps_nearest_stores_for_both_origins(monkeypatch):
    import nearby
    nearby._cache.clear()
    stores=[]
    for i in range(15):
        for anchor,lon in [('home',0),('work',1)]:
            stores.append(dict(id=f'{anchor}-{i}',store='continente',country='PT',name=f'{anchor}-{i}',
                coords=[lon+.0001*i,0],address='',source='official'))
    monkeypatch.setattr(nearby,'official_locations',lambda:stores)
    monkeypatch.setattr(nearby.requests,'get',lambda *a,**k: (_ for _ in ()).throw(ConnectionError('Offline maps')))
    def matrix(points):
        distances=[[haversine(a,b)*1000 for b in points] for a in points]
        return dict(distances=distances,durations=[[d/10 for d in row] for row in distances])
    monkeypatch.setattr(nearby,'table',matrix)
    p=default_profile();p.update(home_coords=[0,0],work_coords=[1,0])
    result=nearby.discover(p)
    assert result['distance_method']=='road'
    assert result['near_home'][0]=='home-0'
    assert result['near_work'][0]=='work-0'
    assert len(result['stores'])==24


def test_images_never_fetch_arbitrary_urls(monkeypatch):
    import images
    monkeypatch.setattr(images.requests,'get',lambda *a,**k: (_ for _ in ()).throw(AssertionError('Network must not be used')))
    for url in ['http://127.0.0.1/private','https://www.auchan.pt.evil.test/dw/image/a.jpg','https://www.auchan.pt/private']:
        assert images.thumbnail(dict(source_kind='automatic',image_url=url)) is None


def test_fruit_varieties_and_meat_cuts_remain_separate():
    from products import family
    def product(name,**extra):
        return dict(id=name,name=name,size=1,unit='kg',**extra)
    assert family(product('Maçã Gala'))['key']==family(product('Maçãs Gala'))['key']
    assert family(product('Maçã Gala'))['key']!=family(product('Maçã Golden'))['key']
    assert family(product('Peito de frango',category='Talho'))['key']==family(product('Peito de frango fresco'))['key']
    assert family(product('Peito de frango fresco'))['key']!=family(product('Peito de frango congelado'))['key']
    assert family(product('Bifes de porco'))['key']!=family(product('Bifes de peru'))['key']
    assert family(product('Ração gato frango'))['key'].startswith('reference:')
    assert family(dict(product('Leite meio gordo proteína'),unit='l'))['label'].endswith('proteína')
