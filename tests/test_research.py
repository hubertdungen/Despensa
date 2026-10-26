"""Regression tests for public-page fallbacks, automatic requests and retry bounds."""
import json
import time
from datetime import datetime, timezone
from research import parse_page, discover_urls, request_query, variants, retry_delay, public_url
from app import create_app, default_profile
from products import family
from planner import match


def test_embedded_aldi_catalogue_supplies_price_pack_and_dates_without_jsonld():
    data = [['PRODUCT_DETAIL_GET', {'res': {'products': [dict(objectID='123', name='Leche semidesnatada',
        salesUnit='6 x 1 l', brandName='Demo', isAvailable=True, assets=[dict(type='primary',url='https://example.test/photo.png')],
        currentPrice=dict(priceValue=5.40,validFrom=1767222000,validUntil=1798757999))]}}]]
    html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(dict(props=dict(pageProps=dict(apiData=json.dumps(data))))) + '</script>'
    rows, methods = parse_page(html,'aldi-es','https://www.aldi.es/producto/leche-123.html')
    assert methods == ['embedded_catalogue']
    assert rows[0]['price_cents'] == 540 and rows[0]['size'] == 6 and rows[0]['unit']=='l'
    assert rows[0]['valid_from']=='2026-01-01' and rows[0]['valid_to']=='2026-12-31'


def test_pingo_price_uses_visible_product_price_not_minicart_or_fake_offer():
    data = dict(**{'@type':'Product'},sku='42',name='Leite meio gordo',brand={'name':'Demo'})
    html = '<div class="minicart-total-price">0,00 €</div><script type="application/ld+json">'+json.dumps(data)+'</script>'
    html += '<div class="product-detail" data-gtm-info="{}"><span>1 L | 0,99 €/L</span><div class="prices"><span class="price-container">0,99 €</span></div>Adicionar</div>'
    rows,methods=parse_page(html,'pingo-doce','https://www.pingodoce.pt/home/produtos/leite.html')
    assert rows[0]['price_cents']==99 and rows[0]['size']==1
    assert methods==['product_jsonld_displayed_price']


def test_jsonld_failure_falls_back_to_independent_microdata():
    html='<script type="application/ld+json">{invalid}</script><section itemtype="https://schema.org/Product"><span itemprop="name">Arroz 1 kg</span><meta itemprop="price" content="1.20"></section>'
    rows,methods=parse_page(html,'dia','https://www.dia.es/arroz/p/123')
    assert methods==['product_microdata'] and rows[0]['price_cents']==120
    assert rows[0]['size']==1 and rows[0]['unit']=='kg'


def test_native_parser_failure_does_not_disable_the_structured_fallback(monkeypatch):
    import research
    monkeypatch.setattr(research,'parse_retailer',lambda *a: (_ for _ in ()).throw(AttributeError('Changed tile schema')))
    data={'@type':'Product','sku':'1','name':'Arroz 1 kg','offers':{'price':1.20,'priceCurrency':'EUR'}}
    rows,methods=research.parse_page('<script type="application/ld+json">'+json.dumps(data)+'</script>','continente','https://www.continente.pt/produto/arroz.html')
    assert rows[0]['price_cents']==120 and methods==['product_jsonld']


def test_sitemap_discovery_stays_with_the_official_retailer():
    xml=b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.lidl.pt/p/leite/p123</loc></url><url><loc>http://127.0.0.1/private</loc></url><url><loc>https://www.lidl.pt.evil.test/secret</loc></url></urlset>'
    assert discover_urls(xml,'https://www.lidl.pt/static/sitemap.xml','lidl-pt')==[('https://www.lidl.pt/p/leite/p123','product')]
    assert not public_url('https://user@www.lidl.pt/p/123','https://www.lidl.pt')


def test_product_requests_are_automatic_and_coalesced(tmp_path):
    app=create_app(tmp_path,testing=True);c=app.test_client()
    c.post('/api/auth/register',json=dict(username='alice',password='temporary-password'))
    c.post('/api/items',json=dict(name='Leite'))
    c.get('/api/offers?q=Leite')
    with app.database() as db:
        rows=db.execute('SELECT * FROM research_queries').fetchall()
        assert len(rows)==1 and rows[0]['query']=='leite'
        before=rows[0]['requested']
        request_query(db,'leite')
        assert db.execute('SELECT requested FROM research_queries').fetchone()[0]==before
    assert c.get('/api/research').status_code==200
    assert any(s['store']=='pingo-doce' and s['status']=='pending' for s in c.get('/api/research').json['sources'])


def test_iberian_words_match_across_country_and_preserve_milk_variants():
    base=dict(id='x',name='Leche semidesnatada sin lactosa',unit='l',size=1)
    pt=dict(base,id='y',name='Leite meio gordo sem lactose')
    assert family(base)['key']==family(pt)['key']
    assert match(dict(query='leite meio gordo',unit='l'),base)
    assert {'leite','leche'}<=variants('leite')
    assert [retry_delay(n) for n in [1,2,3,20]]==[900,1800,3600,86400]
    from catalog import product_text
    assert 'azeite' in product_text('Aceite de oliva virgen extra')
    assert 'azeite' not in product_text('Aceite de girasol')
    assert not match(dict(query='azeite',unit='l'),dict(base,name='Aceite de girasol'))
    assert not match(dict(query='arroz',unit='kg'),dict(base,name='Arroz con leche',unit='kg'))
    assert family(dict(base,name='Leite meio gordo com cálcio'))['key']!=family(dict(base,name='Leite meio gordo'))['key']


def test_upgrade_preserves_profile_and_adds_new_retailers(tmp_path):
    app=create_app(tmp_path,testing=True);c=app.test_client()
    c.post('/api/auth/register',json=dict(username='alice',password='temporary-password'))
    uid=c.get('/api/me').json['user']['id']
    old=default_profile();old['stores'].pop('aldi-es');old['budget']=123
    old['stores']['auchan']['enabled']=False
    with app.database() as db:
        db.execute('UPDATE profiles SET data=? WHERE user_id=?',(json.dumps(old),uid))
    updated=c.get('/api/me').json['profile']
    assert updated['budget']==123 and updated['stores']['auchan']['enabled'] is False
    assert 'aldi-es' in updated['stores']


def test_discovery_reaches_product_prices_and_keeps_progress(tmp_path, monkeypatch):
    import research
    from urllib import robotparser
    app=create_app(tmp_path,testing=True)
    rules=robotparser.RobotFileParser();rules.parse(['User-agent: *','Allow: /'])
    monkeypatch.setattr(research,'robots',lambda root:rules)
    def read(url,limit=0):
        if '.xml' in url:
            return b'<urlset><url><loc>https://www.aldi.es/producto/leche-1.html</loc></url><url><loc>https://www.aldi.es/producto/arroz-2.html</loc></url></urlset>'
        pid='1' if 'leche' in url else '2'
        record=dict(objectID=pid,name='Leche 1 l' if pid=='1' else 'Arroz 1 kg',salesUnit='1 l' if pid=='1' else '1 kg',currentPrice=dict(priceValue=.99),isAvailable=True)
        data=dict(props=dict(pageProps=dict(apiData=[['PRODUCT_DETAIL_GET',dict(res=dict(products=[record]))]])))
        return ('<script id="__NEXT_DATA__">'+json.dumps(data)+'</script>').encode()
    monkeypatch.setattr(research,'read',read)
    reports=[]
    research.run_research(app,reports.append,queries=['leite','arroz'],per_store=3,stores=['aldi-es'])
    assert reports[-1]['status']=='ok' and reports[-1]['count']==2
    assert set(reports[-1]['methods'])=={'official_sitemap','embedded_catalogue'}
    with app.database() as db:
        assert db.execute('SELECT COUNT(*) FROM offers').fetchone()[0]==2
        assert db.execute('SELECT COUNT(*) FROM research_urls WHERE checked>0').fetchone()[0]==3
    # A second pass respects the retailer's scheduled cooldown.
    monkeypatch.setattr(research,'read',lambda *a,**k: (_ for _ in ()).throw(AssertionError('No repeat request')))
    reports=[]
    research.run_research(app,reports.append,stores=['aldi-es'])
    assert reports[-1]['cached']


def test_failed_source_is_retried_with_backoff_without_removing_old_prices(tmp_path,monkeypatch):
    import research
    app=create_app(tmp_path,testing=True)
    with app.database() as db:
        db.execute('INSERT INTO offers VALUES(?,?,?,?)',('kept','','aldi-es','{}'))
    calls=[]
    def unavailable(root):
        calls.append(root)
        raise ConnectionError('Source is temporarily offline')
    monkeypatch.setattr(research,'robots',unavailable)
    reports=[]
    before=time.time()
    research.run_research(app,reports.append,stores=['aldi-es'])
    assert reports[-1]['status']=='unavailable' and reports[-1]['retry_at']>=before+900
    research.run_research(app,reports.append,stores=['aldi-es'])
    assert len(calls)==1 and reports[-1]['cached']
    with app.database() as db:
        assert db.execute('SELECT COUNT(*) FROM offers').fetchone()[0]==1
