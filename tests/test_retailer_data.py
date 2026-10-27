import json
from datetime import datetime,timezone
from urllib import robotparser

from app import default_profile
from catalog import parse_retailer
from planner import purchase_cost,eligible,make_plan
from products import family
from research import parse_page,discover_urls,read_product
from retailer_data import decode_nuxt


def nuxt_page(product):
    # A test fixture encoder: all array/object members reference graph entries.
    graph=[]
    def encode(value):
        index=len(graph);graph.append(None)
        graph[index]={k:encode(v) for k,v in value.items()} if isinstance(value,dict) else [encode(v) for v in value] if isinstance(value,list) else value
        return index
    encode({'data':{'&erp42':product}})
    return '<script id="__NUXT_DATA__">'+json.dumps(graph)+'</script>'


def test_fresh_produce_and_meat_prices_per_kg_are_not_discarded_or_mispriced():
    meta=json.dumps(dict(id='42',name='Banana Continente',category='Frutas e Legumes',brand='Continente',price=.01))
    html=f'''<div data-product-tile-impression='{meta}'><a href="/produto/banana-42.html">Banana</a>
        <span class="pwc-tile--price-primary">1 ,19€/kg</span>
        <span class="pwc-tile--quantity">Quant. Mínima = 600 gr (3 un)</span></div>'''
    row=parse_retailer(html,'continente')[0]
    assert row['variable_weight'] and row['price_cents']==119 and row['size']==1 and row['unit']=='kg'
    assert purchase_cost(row,.6)==(.6,71)
    assert purchase_cost(row,.2)==(.6,71)
    assert purchase_cost(dict(row,variable_weight=False,size=.6),.7)==(2,238)
    row.update(country='PT',condition='public',observed_at=datetime.now(timezone.utc).isoformat())
    item=dict(id='i',name='Banana',query='banana',unit='kg',quantity=.6,checked=False)
    plan=make_plan([item],[row],default_profile(),datetime.now().date().isoformat())
    assert plan['plans'][0]['basket_cents']==71 and plan['plans'][0]['selections'][0]['estimated']
    auchan=json.dumps(dict(id='234229',name='BANANA DEL MONTE KG',price=.01))
    html=f'''<div data-gtm='{auchan}'><div class="pdp-link"><a href="/pt/banana/234229.html">Banana</a></div>
        <div class="sales"><span class="value" content="1.19">1,19 €<span class="auc-avgWeight">/Kg</span></span></div>
        <span class="auc-measures--avg-weight">Quant. Mínima = 200g (1 un)</span></div>'''
    row=parse_retailer(html,'auchan')[0]
    assert row['variable_weight'] and row['price_cents']==119 and row['minimum_quantity']==.2
    assert purchase_cost(row,.6)==(.6,71)


def test_lidl_reads_card_price_dates_and_per_kg_without_fabricating_public_price():
    product=dict(itemId=42,keyfacts={'fullTitle':'Banana Rainforest Alliance'},eans=['4304493274099'],
        price={'currencyCode':'EUR'},regionsV2={'91':{'isDefault':True,'regionPriceId':'1'}},
        regionsPrices={'1':{'currentLidlPlusPrice':{'price':dict(price=.99,oldPrice=1.11,packaging={'text':'Vendido ao kg'},
            currencyCode='EUR',startDate='2026-10-22T09:00:00Z',endDate='2026-11-01T23:59:59Z')}}})
    rows,methods=parse_page(nuxt_page(product),'lidl-pt','https://www.lidl.pt/p/banana/p42')
    assert len(rows)==1 and rows[0]['condition']=='card' and rows[0]['price_cents']==99
    assert rows[0]['variable_weight'] and rows[0]['size']==1 and rows[0]['valid_to']=='2026-11-01'
    assert methods==['embedded_catalogue']


def test_lidl_keeps_public_and_card_prices_separate_and_ignores_other_regions():
    product=dict(itemId=42,keyfacts={'fullTitle':'Leite meio gordo'},price={'price':1.1,'packaging':{'text':'1 L'}},
        regionsV2={'91':{'isDefault':True,'regionPriceId':'1'}},
        regionsPrices={'1':{'currentPrice':{'price':1.05,'packaging':{'text':'1 L'}},
            'currentLidlPlusPrice':{'price':{'price':.9,'packaging':{'text':'1 L'}}}},
            '2':{'currentPrice':{'price':.01,'packaging':{'text':'1 L'}}}})
    rows,_=parse_page(nuxt_page(product),'lidl-pt','https://www.lidl.pt/p/leite/p42')
    assert {(r['condition'],r['price_cents']) for r in rows}=={('public',105),('card',90)}
    assert len({r['id'] for r in rows})==2


def test_nuxt_graph_never_executes_tags_and_rejects_cycles():
    import pytest
    assert decode_nuxt('[ ["Function", 1], "alert(1)" ]') is None
    with pytest.raises(ValueError):decode_nuxt('[{"self":0}]')


def test_makro_uses_anonymous_gross_price_and_requires_centre_confirmation():
    price=dict(valid=True,currency='EUR',grossPrice=12.09,netPrice=10.99)
    bundle=dict(anonymousVisible=True,anonymousSearchable=True,description='Carrillada cerdo vacío',
        bundleId=dict(bettyBundleId='BTY-X12300320021',articleNumber='BTY-X123',variantNumber='0032',bundleNumber='0021'),
        isWeightArticle='WEIGHT',stores={'00001':{'possibleDeliveryModes':{'STORE':{'possibleFulfillmentTypes':{
            'STORE':{'sellingPriceInfo':price,'availability':'AVAILABLE'}}}}}})
    data={'result':{'a':{'variants':{'0032':{'bundles':{'0021':bundle}}}}}}
    rows,methods=parse_page(json.dumps(data),'makro-es','https://tienda.makro.es/shop/pv/BTY-X123/0032/0021/meat')
    row=rows[0]
    assert methods==['public_catalogue_api'] and row['vat_included'] and row['price_cents']==1209
    assert row['condition']=='professional' and row['location']=='Makro Barajas · centro 00001'
    p=default_profile();p['countries']=['ES'];p['stores']['makro-es'].update(enabled=True,access=True)
    row['observed_at']=datetime.now(timezone.utc).isoformat()
    assert not eligible(row,p,datetime.now().date().isoformat())
    del price['grossPrice']
    assert not parse_page(json.dumps(data),'makro-es','https://tienda.makro.es/')[0]
    price['grossPrice']=9
    bundle.update(description='Leche semidesnatada 1,5 L contiene 6 unidades',isWeightArticle='NON_WEIGHT',bundleSize='6',
        contentData={'netPieceWeight':{'value':1545,'uom':'GRAM'},'netContentVolume':{'value':1500,'uom':'ML'}})
    milk=parse_page(json.dumps(data),'makro-es','https://tienda.makro.es/')[0][0]
    assert milk['size']==9 and milk['unit']=='l' and milk['price_cents']/milk['size']==100


def test_makro_fallback_uses_verified_official_alias_and_robots_permitted_public_data(monkeypatch):
    import research
    xml=b'<urlset><url><loc>https://distribucion-hosteleria.makro.es/shop/pv/BTY-X123/0032/0021/Banana</loc></url></urlset>'
    urls=discover_urls(xml,'https://tienda.makro.es/sitemap','makro-es')
    assert urls[0][0].startswith('https://tienda.makro.es/')
    rules=robotparser.RobotFileParser();rules.parse(['User-agent: *','Allow: /'])
    called=[]
    monkeypatch.setattr(research,'read',lambda url:called.append(url) or b'{}')
    read_product(urls[0][0],'makro-es',rules)
    assert 'ids=BTY-X1230032&country=ES&locale=es-ES' in called[0]
    assert not discover_urls(xml,'https://www.makro.pt/sitemap','makro-pt')


def test_fresh_banana_groups_preserve_origin_bio_and_processed_boundaries():
    a=dict(id='a',name='Banana Continente',unit='kg',size=1)
    assert family(a)['key']==family(dict(a,id='b',name='Banana Rainforest Alliance'))['key']
    assert family(a)['key']!=family(dict(a,name='Banana da Madeira'))['key']
    assert family(a)['key']!=family(dict(a,name='Banana biológica'))['key']
    assert family(dict(a,name='Iogurte de banana'))['key'].startswith('reference:')
    assert family(dict(a,name='Banana desidratada'))['key'].startswith('reference:')


def test_aldi_category_hydration_is_an_independent_catalogue_source():
    product=dict(objectID='banana',name='Banana',salesUnit='kg - 1000 g',currentPrice={'priceValue':.95})
    page={'props':{'pageProps':{'apiData':[],'algoliaState':{'initialResults':{'products':{'results':[{'hits':[product]}]}}}}}}
    rows,_=parse_page('<script id="__NEXT_DATA__">'+json.dumps(page)+'</script>','aldi-pt','https://www.aldi.pt/category.html')
    assert rows[0]['price_cents']==95 and rows[0]['variable_weight']


def test_adapter_upgrade_requeues_missed_prices_once_and_preserves_access_blocks(tmp_path):
    from app import create_app
    from research import upgrade_adapters
    import time
    app=create_app(tmp_path,testing=True)
    with app.database() as db:
        db.execute("DELETE FROM meta WHERE key='research_adapter_revision'")
        for sid in ['lidl-pt','makro-es','auchan']:
            db.execute('INSERT INTO research_sources VALUES(?,?)',(sid,json.dumps(dict(status='unavailable',errors=[
                'source_unavailable' if sid=='lidl-pt' else 'access_restricted'],retry_at=time.time()+86400))))
        upgrade_adapters(db)
        states={r['store']:json.loads(r['data']) for r in db.execute('SELECT * FROM research_sources')}
        assert states['lidl-pt']['retry_at']==states['makro-es']['retry_at']==0
        assert states['auchan']['retry_at']>time.time()
        db.execute("UPDATE research_sources SET data=? WHERE store='lidl-pt'",(json.dumps({'retry_at':42}),))
        upgrade_adapters(db)
        assert json.loads(db.execute("SELECT data FROM research_sources WHERE store='lidl-pt'").fetchone()[0])['retry_at']==42
