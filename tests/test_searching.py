import json
import time
from datetime import datetime,timezone
from urllib import robotparser

from app import create_app
from searching import find,rank
import research


def offer(oid,name='Leite UHT meio gordo',store='continente',price=100,**extra):
    data=dict(id=oid,name=name,brand='Mimosa',store=store,country='ES' if store=='dia' else 'PT',
        size=1,unit='l',pack='1 l',price_cents=price,condition='public',vat_included=True,
        source_kind='automatic',observed_at=datetime.now(timezone.utc).isoformat())
    data.update(extra)
    return data


def client(tmp_path):
    app=create_app(tmp_path,testing=True);c=app.test_client()
    c.post('/api/auth/register',json=dict(username='tester',password='temporary-password'))
    return app,c


def save(app,rows):
    with app.database() as db:
        for o in rows:db.execute('INSERT INTO offers VALUES(?,?,?,?)',(o['id'],'',o['store'],json.dumps(o)))


def test_search_includes_brand_plurals_prefixes_and_formats():
    rows=[offer('milk'),offer('soap','Detergente máquina de roupa',brand='Skip')]
    assert find(rows,'Mimosa')[0][0]['id']=='milk'
    assert find(rows,'detergentes')[0][0]['id']=='soap'
    assert find(rows,'deterg')[0][0]['id']=='soap'
    assert find(rows,'máquina da roupa')[0][0]['id']=='soap'
    assert find(rows,'1l')[0]
    assert not find(rows,'sem lactose')[0]
    assert rank('leite magro','Leite meio gordo')==0


def test_typo_fallback_is_marked_and_never_overrides_exact_matches():
    result,approximate=find([offer('a')],'mimsoa')
    assert result[0]['id']=='a' and approximate
    result,approximate=find([offer('a')],'mimosa')
    assert result and not approximate


def test_all_offers_participate_before_comparison_pagination(tmp_path):
    app,c=client(tmp_path)
    save(app,[offer(f'c{i}',price=100+i) for i in range(350)]+[offer('a',store='auchan',price=999)])
    result=c.get('/api/offers?q=leite&investigate=false').json
    assert result['total']==351 and result['group_total']==1
    assert len(result['comparisons'][0]['offers'])==351
    assert result['comparisons'][0]['store_count']==2
    assert any(o['id']=='a' for o in result['offers'])


def test_more_results_and_explicit_iberian_scope(tmp_path):
    app,c=client(tmp_path)
    save(app,[offer(str(i),name=f'Produto teste {i}') for i in range(45)]+[offer('es','Leche semidesnatada',store='dia')])
    first=c.get('/api/offers?q=produto&investigate=false').json
    second=c.get('/api/offers?q=produto&offset=30&investigate=false').json
    assert first['has_more'] and len(first['comparisons'])==30
    assert not second['has_more'] and len(second['comparisons'])==15
    assert not ({g['key'] for g in first['comparisons']}&{g['key'] for g in second['comparisons']})
    assert c.get('/api/offers?q=leite&country=ES&investigate=false').json['offers'][0]['id']=='es'
    assert not c.get('/api/offers?q=leite&country=PT&investigate=false').json['offers']


def test_search_priority_bypasses_catalogue_cooldown_and_fetches_only_matching_pages(tmp_path,monkeypatch):
    app,_=client(tmp_path)
    rules=robotparser.RobotFileParser();rules.parse(['User-agent: *','Allow: /'])
    monkeypatch.setattr(research,'robots',lambda root:rules)
    fetched=[]
    def read(url,limit=0):
        fetched.append(url)
        data={'@type':'Product','sku':'soap','name':'Detergente roupa 1 l','offers':{'price':2.99,'priceCurrency':'EUR'}}
        return ('<script type="application/ld+json">'+json.dumps(data)+'</script>').encode()
    monkeypatch.setattr(research,'read',read)
    with app.database() as db:
        for name in ['leite','detergente']:
            db.execute('INSERT INTO research_urls(store,url,kind) VALUES(?,?,?)',('auchan',f'https://www.auchan.pt/pt/{name}.html','product'))
        db.execute('INSERT INTO research_sources VALUES(?,?)',('auchan',json.dumps(dict(status='ok',retry_at=time.time()+86400,indexed=2))))
    result=research.search_store(app,dict(store='auchan',query='detergentes',requested=time.time()))
    assert result['found']>=1 and result['status']=='done'
    assert 'https://www.auchan.pt/pt/detergente.html' in fetched
    assert not any('leite.html' in url for url in fetched)
    with app.database() as db:assert db.execute('SELECT COUNT(*) FROM offers').fetchone()[0]==1


def test_product_format_is_optional_in_frontier_but_required_in_final_results(tmp_path,monkeypatch):
    app,_=client(tmp_path)
    rules=robotparser.RobotFileParser();rules.parse(['User-agent: *','Allow: /'])
    monkeypatch.setattr(research,'robots',lambda _:rules)
    data={'@type':'Product','sku':'water','name':'Água sem gás Luso','description':'garrafão 7 L','offers':{'price':1.99}}
    monkeypatch.setattr(research,'read',lambda *args:('<script type="application/ld+json">'+json.dumps(data)+'</script>').encode())
    with app.database() as db:
        db.execute('INSERT INTO research_urls(store,url,kind) VALUES(?,?,?)',
            ('continente','https://www.continente.pt/produto/agua-sem-gas-luso-123.html','product'))
    result=research.search_store(app,dict(query='agua luso 7l',store='continente',requested=time.time()))
    assert result['found']==1
    with app.database() as db:row=json.loads(db.execute('SELECT data FROM offers').fetchone()[0])
    assert find([row],'agua luso 7l')[0] and not find([row],'agua luso 5l')[0]


def test_direct_grocery_matches_precede_flavoured_products_and_books():
    rows=[offer('flavour','Iogurte sabor banana'),offer('book','Diário de um Banana',category='Livros'),
          offer('fresh','Banana Continente',size=1,unit='kg')]
    assert find(rows,'banana')[0][0]['id']=='fresh'


def test_transient_source_error_does_not_block_another_interactive_product(tmp_path,monkeypatch):
    app,_=client(tmp_path)
    rules=robotparser.RobotFileParser();rules.parse(['User-agent: *','Allow: /'])
    monkeypatch.setattr(research,'robots',lambda _:rules)
    with app.database() as db:
        db.execute('INSERT INTO research_sources VALUES(?,?)',('lidl-pt',json.dumps(dict(status='unavailable',errors=['source_unavailable'],retry_at=time.time()+86400))))
    result=research.search_store(app,dict(query='banana',store='lidl-pt',requested=time.time()-2000))
    assert result['status']=='done' and result['error']=='no_candidates'


def test_empty_pass_reschedules_without_spinning_or_discarding_prices(tmp_path,monkeypatch):
    app,_=client(tmp_path)
    rules=robotparser.RobotFileParser();rules.parse(['User-agent: *','Allow: /'])
    monkeypatch.setattr(research,'robots',lambda root:rules)
    with app.database() as db:
        db.execute('INSERT INTO research_urls(store,url,kind,checked,next_check) VALUES(?,?,?,?,?)',
            ('auchan','https://www.auchan.pt/pt/leite.html','product',time.time(),time.time()+21600))
        for s in research.CATEGORY_SOURCES:
            if s['store']=='auchan':db.execute('INSERT INTO research_urls(store,url,kind,checked,next_check) VALUES(?,?,?,?,?)',
                ('auchan',s['url'],'category',time.time(),time.time()+21600))
        db.execute('INSERT INTO research_sources VALUES(?,?)',('auchan',json.dumps(dict(store='auchan',status='ok',retry_at=0,remaining=0))))
    reports=[]
    monkeypatch.setattr(research,'read',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Already fresh')))
    research.run_research(app,reports.append,stores=['auchan'])
    assert reports[-1]['cached'] and reports[-1]['retry_at']>time.time()+21000


def test_search_tasks_are_scoped_coalesced_and_query_progress_is_private(tmp_path):
    app,c=client(tmp_path)
    data=c.get('/api/offers?q=detergente&country=ES&store=dia').json
    assert data['research']['total']==1 and data['research']['pending']==1
    c.get('/api/offers?q=detergente&country=ES&store=dia')
    with app.database() as db:
        assert db.execute('SELECT COUNT(*) FROM research_tasks').fetchone()[0]==1
    other=c.get('/api/offers?q=cafe&country=ES&store=dia&investigate=false').json
    assert other['research']['total']==0
    b=app.test_client();b.post('/api/auth/register',json=dict(username='bob',password='temporary-password'))
    assert b.get('/api/offers?q=detergente&country=ES&store=dia&investigate=false').json['research']['total']==0


def test_priority_worker_runs_even_when_general_research_is_busy(tmp_path,monkeypatch):
    import threading
    app,_=client(tmp_path)
    with app.database() as db:
        research.request_query(db,'detergente',stores=['auchan'])
        db.execute("UPDATE research_tasks SET status='running',updated=0")
        db.execute('INSERT INTO jobs VALUES(?,?,?,?,?)',('general','running',datetime.now(timezone.utc).isoformat(),None,'{}'))
    stop=threading.Event()
    def searched(app,task):
        stop.set()
        return dict(status='done',found=3,error='',next_check=0)
    monkeypatch.setattr(research,'search_store',searched)
    research.priority_worker(app,stop)
    with app.database() as db:
        assert db.execute('SELECT status,found FROM research_tasks').fetchone()[:]==('done',3)
        assert db.execute("SELECT status FROM jobs WHERE id='general'").fetchone()[0]=='running'


def test_pingo_category_reads_many_prices_and_keeps_card_conditions():
    meta=json.dumps({'items':[{'item_id':'soap','item_name':'Detergente loiça','item_brand':'Demo','price':.01}]})
    html=f'''<div class="product-tile-pd" data-gtm-info='{meta}'>
        <a href="/home/produtos/detergente.html">Detergente</a><div class="product-unit">1.25 L | 3,99 €/L</div>
        <div class="product-price"><span class="sales">4,99 €</span><del>6,29 €</del></div>
        <img class="product-tile-promo-label" alt="Preço com Cartão"/></div>'''
    rows,methods=research.parse_page(html,'pingo-doce','https://www.pingodoce.pt/home/produtos/limpeza')
    assert methods==['retailer_tiles'] and rows[0]['price_cents']==499
    assert rows[0]['size']==1.25 and rows[0]['unit']=='l' and rows[0]['condition']=='unknown'


def test_valid_barcode_groups_other_product_types_without_guessing_names():
    from products import family,valid_gtin,comparisons
    from app import default_profile
    assert valid_gtin('5601049132995') and not valid_gtin('0000000000000')
    a=offer('a','Detergente loiça',ean='5601049132995')
    b=offer('b','Outro nome publicado',store='auchan',ean='5601049132995')
    assert family(a)['key']==family(b)['key']
    assert family(dict(b,ean='05601049132995'))['key']==family(a)['key']
    assert family(dict(b,size=2))['key']!=family(a)['key']
    group=comparisons([a,b],default_profile())[0]
    assert group['store_count']==2 and group['exact_reference'] and not group['same_reference']


def test_cereal_category_words_match_without_changing_brand_or_dietary_constraints():
    from searching import discovery_query
    fitness=offer('fitness','Cereais Trigo e Aveia Integral',brand='Fitness',category='Cereais Linha e Fibra',pack='625 g',size=.625,unit='kg')
    national=offer('other','Cereais +Linha',brand='Nacional',category='Cereais Linha e Fibra')
    found,approximate=find([fitness,national],'Cereais Linha e Fibra Fitness')
    assert [o['id'] for o in found]==['fitness'] and not approximate
    found,approximate=find([dict(fitness,category='')],'Cereais Linha e Fibra Fitness')
    assert found and approximate
    assert not find([fitness],'Cereais Linha e Fibra Fitness sem açúcar')[0]
    assert discovery_query('Cereais Linha e Fibra Fitness')=='cereal fitnes'
    assert 'fibra' in discovery_query('Leite com fibra')


def test_specific_suggestions_fill_published_pack_and_keep_brand(tmp_path):
    app,c=client(tmp_path)
    save(app,[offer('coffee','Café em Grão Gold',brand='Delta',pack='500 g',size=.5,unit='kg'),
        offer('capsule','Cápsulas Café Delta Q',brand='Delta',pack='10 un',size=10,unit='un')])
    result=c.get('/api/offers?q=Café Delta&investigate=false').json
    assert len(result['comparisons'])==2
    details={g['details']['offer_id']:g['details'] for g in result['comparisons']}
    assert details['coffee']['quantity']==.5 and details['coffee']['unit']=='kg'
    assert 'Delta' in details['coffee']['query']
    assert details['capsule']['quantity']==10 and details['capsule']['unit']=='un'
    assert all(d['category']=='Mercearia' for d in details.values())


def test_category_hits_do_not_hide_original_and_articles_do_not_block_search():
    original=offer('original','Cereais Nestlé Fitness Original',brand='Nestlé',category='',pack='625 g',size=.625,unit='kg')
    fibre=offer('fibre','Cereais Fitness Mel Fibra',brand='Fitness',category='Cereais Linha e Fibra',pack='310 g',size=.31,unit='kg')
    wrong=offer('other','Cereais Linha Fibra',brand='Nacional',category='Cereais Linha e Fibra')
    for query in ('Cereais Linha e Fibra Fitness','Os Cereais Linha e Fibra Fitness'):
        rows,related=find([original,fibre,wrong],query)
        assert {o['id'] for o in rows}=={'original','fibre'} and related
    assert not find([original,fibre],'Os Cereais Linha e Fibra Fitness sem açúcar')[0]
    assert not find([original,fibre],'Os Cereais Linha e Fibra Fitness sem glúten')[0]
    assert not find([original,fibre],'Os Cereais Linha e Fibra Fitness 500g')[0]


def test_cereal_search_and_plan_cover_one_package_instead_of_requiring_one_kg(tmp_path):
    app,c=client(tmp_path)
    row=offer('original','Cereais Fitness Original',brand='Fitness',pack='625 g',size=.625,unit='kg')
    save(app,[row])
    item=dict(name='Cereais Linha e Fibra Fitness',query='Cereais Linha e Fibra Fitness',quantity=1,unit='un')
    assert c.post('/api/items',json=item).status_code==201
    plan=c.get('/api/plan').json['plans'][0]
    assert plan['complete'] and not plan['missing']
    selection=plan['selections'][0]
    assert selection['packs']==1 and selection['cost_cents']==row['price_cents']
    assert selection['quantity_basis']=='packages'
    assert c.get('/api/offers?q=Os+Cereais+Linha+e+Fibra+Fitness&investigate=false').json['total']==1
