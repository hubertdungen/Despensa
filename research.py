"""Automatic multi-method retailer research, persistent discovery and retry state.

Only public, robots-permitted pages are read. Each adapter can parse retail tiles,
JSON-LD, embedded catalogue JSON and product microdata independently. Official
sitemaps provide another discovery route when category pages change or fail.
"""
import gzip
import hashlib
import io
import json
import re
import time
import threading
from collections import Counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import unquote, urljoin, urlsplit
from urllib import robotparser
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup
from catalog import STORE_MAP, CATEGORY_SOURCES, cents, fold, product_text, pack_size, parse_retailer

AGENT = 'Despensa/0.3 (+https://github.com/hubertdungen/Despensa; automatic grocery research)'
ROOTS = {
    'continente': 'https://www.continente.pt', 'auchan': 'https://www.auchan.pt',
    'pingo-doce': 'https://www.pingodoce.pt', 'lidl-pt': 'https://www.lidl.pt',
    'aldi-pt': 'https://www.aldi.pt', 'intermarche': 'https://www.intermarche.pt',
    'mercadona-pt': 'https://www.mercadona.pt', 'makro-pt': 'https://www.makro.pt',
    'recheio': 'https://www.recheio.pt', 'mercadona-es': 'https://tienda.mercadona.es',
    'carrefour': 'https://www.carrefour.es', 'dia': 'https://www.dia.es',
    'eroski': 'https://supermercado.eroski.es', 'alcampo': 'https://www.compraonline.alcampo.es',
    'lidl-es': 'https://www.lidl.es', 'makro-es': 'https://www.makro.es',
    'aldi-es': 'https://www.aldi.es',
}
SEEDS = {
    'pingo-doce': ['https://www.pingodoce.pt/home/sitemap_index.xml'],
    'lidl-pt': ['https://www.lidl.pt/static/sitemap.xml'],
    'lidl-es': ['https://www.lidl.es/static/sitemap.xml'],
    'aldi-pt': ['https://www.aldi.pt/.aldi-nord-sitemap.xml'],
    'aldi-es': ['https://www.aldi.es/.aldi-nord-sitemap.xml'],
    'carrefour': ['https://www.carrefour.es/supermercado/la-despensa/lacteos/leche/cat20093/c'],
    'alcampo': ['https://www.compraonline.alcampo.es/categories/Leche-Huevos-L%C3%A1cteos-Yogures-y-Bebidas-vegetales/Leche/OC1603'],
    'recheio': ['https://www.recheio.pt/portal/sitemap.xml'],
}
SCHEMA = '''
CREATE TABLE IF NOT EXISTS research_urls(store TEXT NOT NULL,url TEXT NOT NULL,kind TEXT NOT NULL,
    checked REAL NOT NULL DEFAULT 0,next_check REAL NOT NULL DEFAULT 0,failures INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(store,url));
CREATE TABLE IF NOT EXISTS research_sources(store TEXT PRIMARY KEY,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS research_queries(query TEXT PRIMARY KEY,requested REAL NOT NULL);
CREATE TABLE IF NOT EXISTS research_tasks(query TEXT NOT NULL,store TEXT NOT NULL,requested REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',updated REAL NOT NULL DEFAULT 0,next_check REAL NOT NULL DEFAULT 0,
    found INTEGER NOT NULL DEFAULT 0,error TEXT NOT NULL DEFAULT '',PRIMARY KEY(query,store));
CREATE INDEX IF NOT EXISTS research_tasks_pending ON research_tasks(status,next_check,requested);
CREATE TABLE IF NOT EXISTS research_watchers(user_id TEXT NOT NULL,query TEXT NOT NULL,store TEXT NOT NULL,
    PRIMARY KEY(user_id,query,store));
'''
_rules = {}
_last = {}
_rate_lock = threading.Lock()


def setup(db):
    db.executescript(SCHEMA)


def request_query(db, query, stores=None, force=False, owner=None):
    query = fold(query)[:120]
    if len(query) < 3:
        return
    now = time.time()
    row = db.execute('SELECT requested FROM research_queries WHERE query=?', (query,)).fetchone()
    # A bounded shared catalogue queue contains product terms, never account IDs,
    # addresses, notes or full shopping lists. It is not returned to other accounts.
    if not row and db.execute('SELECT COUNT(*) FROM research_queries').fetchone()[0] >= 300:
        db.execute('DELETE FROM research_queries WHERE query=(SELECT query FROM research_queries ORDER BY requested LIMIT 1)')
    if not row or now-row[0]>=21600:
        db.execute('INSERT OR REPLACE INTO research_queries VALUES(?,?)', (query, now))
    for store in (stores if stores is not None else ROOTS):
        if store not in ROOTS:
            continue
        if owner:
            db.execute('INSERT OR IGNORE INTO research_watchers VALUES(?,?,?)',(owner,query,store))
        task=db.execute('SELECT status,updated FROM research_tasks WHERE query=? AND store=?',(query,store)).fetchone()
        if task and (task[0] in ('queued','running') or now-task[1]<(60 if force else 900)):
            continue
        db.execute("INSERT OR REPLACE INTO research_tasks(query,store,requested) VALUES(?,?,?)",(query,store,now))
    db.execute("DELETE FROM research_tasks WHERE query NOT IN (SELECT query FROM research_queries)")
    db.execute("DELETE FROM research_watchers WHERE query NOT IN (SELECT query FROM research_queries)")


def variants(query):
    pairs = [('leite','leche'), ('azeite','aceite'), ('ovos','huevos'), ('frango','pollo'),
             ('cafe','cafe'), ('manteiga','mantequilla'), ('queijo','queso'), ('atum','atun'),
             ('acucar','azucar'), ('massa','pasta'), ('batata','patata'), ('agua','agua')]
    result = set(fold(query).split())
    for pt, es in pairs:
        if pt in result or es in result:
            result.update((pt, es))
    return result


def score(url, queries):
    words = set(fold(unquote(urlsplit(url).path.rsplit('/', 1)[-1])).split())
    return sum(len(variants(q) & words) for q in queries)


def public_url(url, root):
    p, r = urlsplit(url), urlsplit(root)
    return (p.scheme == 'https' and p.hostname in {r.hostname, r.hostname.removeprefix('www.'), 'www.' + r.hostname.removeprefix('www.')}
            and p.port in (None, 443) and not p.username and not p.password and len(url) <= 1600)


def wait_for_slot(url):
    host = urlsplit(url).netloc
    while True:
        with _rate_lock:
            delay=2-(time.monotonic()-_last.get(host,0))
            if delay<=0:
                _last[host]=time.monotonic()
                break
        time.sleep(delay)


def read(url, limit=8_000_000):
    wait_for_slot(url)
    host=urlsplit(url).netloc
    with requests.get(url, headers={'User-Agent': AGENT, 'Accept-Language': 'pt-PT,es;q=0.9'},
                      timeout=(5, 18), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            target = urljoin(url, r.headers.get('Location', ''))
            if target == url or not public_url(target, 'https://' + host):
                raise ValueError('Redirecionamento da fonte não permitido')
            return read_redirect(target, limit)
        content = bytearray()
        for chunk in r.iter_content(65536):
            content.extend(chunk)
            if len(content) > limit:
                raise ValueError('Resposta da fonte demasiado grande')
        if content[:2] == b'\x1f\x8b':
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as archive:
                content = archive.read(limit + 1)
            if len(content) > limit:
                raise ValueError('Mapa da fonte demasiado grande')
        return bytes(content)


def read_redirect(url, limit):
    # One canonical same-retailer redirect, no chains or open URL fetches.
    wait_for_slot(url)
    with requests.get(url, headers={'User-Agent': AGENT}, timeout=(5,18), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('Demasiados redirecionamentos')
        content = bytearray()
        for chunk in r.iter_content(65536):
            content.extend(chunk)
            if len(content) > limit:
                raise ValueError('Resposta demasiado grande')
        return bytes(content)


def robots(root):
    hit = _rules.get(root)
    if hit and time.time() - hit[0] < 21600:
        return hit[1]
    content = read(root + '/robots.txt', 1_000_000).decode('utf-8', 'replace')
    if '<html' in content.casefold() or '<!doctype' in content.casefold():
        raise ValueError('A fonte exige verificação de acesso')
    parser = robotparser.RobotFileParser()
    parser.parse(content.splitlines())
    _rules[root] = (time.time(), parser)
    return parser


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def base_offer(store, oid, name, price, pack, url, image='', brand='', **extra):
    amount, unit = pack_size(pack)
    return dict(id=f'{store}:{oid}', store=store, country=STORE_MAP[store]['country'], name=name[:240],
        brand=brand, pack=f'{amount:g} {unit}' if amount else pack[:160], size=amount, unit=unit, price_cents=cents(price),
        condition='public', coupon='', balance_cents=0, source_url=url, image_url=image,
        channel='online', location='Preço publicado · disponibilidade local por confirmar',
        valid_from='', valid_to='', source_kind='automatic', vat_included=True,
        conditions_note='Preço publicado pela loja; confirmar disponibilidade e condições locais', **extra)


def parse_page(html, store, url):
    """Independent parsers can rescue the same page when one representation changes."""
    soup = BeautifulSoup(html, 'html.parser')
    found, methods = {}, []
    if store in ('continente', 'auchan'):
        try:
            rows = parse_retailer(html, store)
        except (ValueError, TypeError, KeyError, AttributeError):
            rows = []
        if rows:
            found.update((o['id'], o) for o in rows)
            methods.append('retailer_tiles')
    if store=='pingo-doce':
        for tile in soup.select('.product-tile-pd[data-gtm-info]'):
            try:
                meta=json.loads(tile['data-gtm-info'])['items'][0]
                price=tile.select_one('.product-price .sales')
                pack=tile.select_one('.product-unit')
                link=tile.select_one('a[href*="/home/produtos/"]')
                image=tile.select_one('img.product-tile-component-image')
                if not price or not pack or not link:
                    continue
                o=base_offer(store,meta['item_id'],meta['item_name'],price.get_text('',strip=True),pack.get_text(' ',strip=True),
                    urljoin(ROOTS[store],link['href']),image.get('src','') if image else '',meta.get('item_brand',''))
                badges=' '.join(e.get_text(' ',strip=True)+' '+e.get('alt','')+' '+e.get('title','')
                    for e in tile.select('[class*="promo"],[class*="badge"],[class*="discount"]'))
                if any(word in fold(badges) for word in ('cartao','poupa mais','cupao','so na app')):
                    o['condition']='unknown'
                found[o['id']]=o
                methods.append('retailer_tiles')
            except (ValueError,TypeError,KeyError,IndexError):
                continue
    # ALDI renders catalogue records in public Next.js page data, including prices,
    # dates, packs and primary images even when the visible page is client rendered.
    if store.startswith('aldi-'):
        script = soup.select_one('#__NEXT_DATA__')
        if script:
            try:
                data = json.loads(script.get_text())['props']['pageProps']['apiData']
                data = json.loads(data) if isinstance(data, str) else data
                for product in walk(data):
                    if not all(k in product for k in ('objectID', 'name', 'currentPrice')):
                        continue
                    current = product['currentPrice']
                    if not current.get('priceValue') or product.get('isRecall'):
                        continue
                    image = next((a['url'] for a in product.get('assets', []) if a.get('type') == 'primary'), '')
                    o = base_offer(store, product['objectID'], product['name'], current['priceValue'],
                        product.get('salesUnit', ''), url, image, product.get('brandName', ''))
                    for field, key in [('valid_from','validFrom'), ('valid_to','validUntil')]:
                        if current.get(key):
                            zone=ZoneInfo('Europe/Lisbon' if STORE_MAP[store]['country']=='PT' else 'Europe/Madrid')
                            o[field] = datetime.fromtimestamp(current[key], zone).date().isoformat()
                    o['available'] = bool(product.get('isAvailable', True))
                    o['channel'] = 'store'
                    found[o['id']] = o
                    methods.append('embedded_catalogue')
            except (ValueError, KeyError, TypeError, OverflowError):
                pass
    # Public product structured data: also used by discovery on ordinary product URLs.
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.get_text())
        except (ValueError, TypeError):
            continue
        for product in walk(data):
            kind = product.get('@type', '')
            if not (kind == 'Product' or isinstance(kind, list) and 'Product' in kind):
                continue
            name = product.get('name', '')
            if not name:
                continue
            offers = product.get('offers', [])
            offers = offers if isinstance(offers, list) else [offers]
            valid = [o for o in offers if isinstance(o, dict) and o.get('price') is not None and o.get('priceCurrency', 'EUR') == 'EUR']
            # Pingo Doce publishes the price in the product-specific displayed price
            # and analytics record; its Product JSON-LD deliberately has no offers.
            detail = soup.select_one('.product-detail[data-gtm-info]') if store == 'pingo-doce' else None
            price_node = detail.select_one('.prices .price-container') if detail else None
            if not valid and price_node:
                valid = [dict(price=price_node.get_text('', strip=True))]
            if not valid:
                continue
            price = valid[0]
            pack = name + ' ' + str(product.get('description', ''))[:400]
            if detail:
                # Contains the explicit pack label (e.g. 1 L), not the €/L price.
                pack = detail.get_text(' ', strip=True).split('Adicionar', 1)[0]
            footer = soup.select_one('.ods-price__footer') if store.startswith('lidl-') else None
            if footer:
                pack = footer.get_text(' ', strip=True)
            image = product.get('image', '')
            image = image[0] if isinstance(image, list) and image else image
            image = image.get('url','') if isinstance(image, dict) else image
            brand = product.get('brand', '')
            brand = brand.get('name', '') if isinstance(brand, dict) else brand
            oid = product.get('sku') or product.get('mpn') or hashlib.sha256(url.encode()).hexdigest()[:20]
            try:
                o = base_offer(store, oid, name, price['price'], pack, url, image, brand)
            except (ValueError, TypeError):
                continue
            excluded=('Discontinued','SoldOut') if store.startswith('lidl-') else ('Discontinued','SoldOut','OutOfStock')
            o['available'] = not str(price.get('availability','')).endswith(excluded)
            # In-store retailers use OutOfStock for the unavailable online channel;
            # never infer physical stock from that field.
            o['channel'] = 'store' if store.startswith('lidl-') else 'online'
            o['online_availability'] = price.get('availability','')
            gtin = product.get('gtin13') or product.get('gtin') or ''
            o['ean'] = gtin[0] if isinstance(gtin,list) and gtin else gtin
            if price.get('priceValidUntil'):
                o['valid_to'] = str(price['priceValidUntil'])[:10]
            if detail:
                badges=' '.join(e.get_text(' ',strip=True) for e in detail.select('[class*="promo"],[class*="badge"],[class*="discount"]'))
                conditional = fold(detail.select_one('.prices').get_text(' ',strip=True)+' '+badges)
                if any(s in conditional for s in ('cartao','poupa mais','cupao')):
                    o['condition'] = 'unknown'
            found.setdefault(o['id'], o)
            methods.append('product_jsonld' if not detail else 'product_jsonld_displayed_price')
    # Standard product microdata is independent of the JSON-LD representation.
    for product in soup.select('[itemtype$="/Product"]'):
        name, price = product.select_one('[itemprop="name"]'), product.select_one('[itemprop="price"]')
        if not name or not price:
            continue
        currency=product.select_one('[itemprop="priceCurrency"]')
        if currency and (currency.get('content') or currency.get_text('',strip=True))!='EUR':
            continue
        try:
            oid = hashlib.sha256(url.encode()).hexdigest()[:20]
            o = base_offer(store,oid,name.get('content') or name.get_text(' ',strip=True),
                price.get('content') or price.get_text('',strip=True),product.get_text(' ',strip=True)[:500],url)
            found.setdefault(o['id'],o)
            methods.append('product_microdata')
        except (ValueError,TypeError):
            pass
    return list(found.values()), sorted(set(methods))


def retry_delay(failures):
    return min(86400, 900 * 2 ** min(failures - 1, 7))


def discover_urls(content, url, store):
    root = ROOTS[store]
    result = []
    try:
        tree = ET.fromstring(content)
        index = tree.tag.endswith('sitemapindex')
        for element in tree:
            loc = next((e.text for e in element if e.tag.endswith('loc')), None)
            if loc and public_url(loc,root):
                result.append((loc,'sitemap' if index else 'product'))
        return result[:60000]
    except ET.ParseError:
        pass
    soup=BeautifulSoup(content,'html.parser')
    for a in soup.select('a[href]'):
        target=urljoin(url,a['href']).split('#')[0]
        if not public_url(target,root) or urlsplit(target).query:
            continue
        path=urlsplit(target).path
        if any(k in path for k in ('/produto/','/produtos/','/producto/','/producto-','/produto-','/product/','/p/')):
            result.append((target,'product'))
    return list(dict.fromkeys(result))[:400]


def run_research(app, report, queries=None, per_store=12, stores=None):
    """Incremental crawler: at most a small page budget per chain per pass.

    A persistent frontier rotates through the catalogue; product words move matching
    URLs to the front. Failures have exponential backoff per source and URL.
    """
    with app.database() as db:
        setup(db)
        queries = queries or [r[0] for r in db.execute('SELECT query FROM research_queries ORDER BY requested DESC LIMIT 50')]
        # Learn category requests from active lists without exposing their contents.
        for row in db.execute('SELECT data FROM items ORDER BY rowid DESC LIMIT 1000'):
            item=json.loads(row[0])
            if not item.get('checked'):
                queries.append(item.get('query') or item['name'])
        queries=list(dict.fromkeys(queries))[:80] or ['leite','arroz','azeite','ovos','massa','cafe']
    weights=Counter(word for query in queries for word in variants(query))
    def prioritise(entry):
        if 'priority' not in entry:
            words=set(product_text(unquote(urlsplit(entry['url']).path.rsplit('/',1)[-1])).split())
            entry['words']=words
            entry['priority']=sum(weights[word] for word in words)
        product_map=entry['kind']=='sitemap' and 'product' in entry['url'].lower()
        return (entry['kind']!='sitemap',-entry['priority']-20*product_map,entry['checked'])
    for store, root in ROOTS.items():
        if stores is not None and store not in stores:
            continue
        now=time.time()
        with app.database() as db:
            old=db.execute('SELECT data FROM research_sources WHERE store=?',(store,)).fetchone()
            old=json.loads(old[0]) if old else {}
            if old.get('retry_at',0)>now:
                report(dict(old, store=store, cached=True))
                continue
        state=dict(store=store,status='researching',checked_at=datetime.now(timezone.utc).isoformat(),
                   count=0,methods=[],failures=old.get('failures',0),retry_at=0,errors=[],query_cursor=old.get('query_cursor',0))
        pages_read=0
        try:
            rules=robots(root)
            seeds=[s['url'] for s in CATEGORY_SOURCES if s['store']==store]+SEEDS.get(store,[])
            seeds+=rules.site_maps() or []
            if not seeds:
                seeds=[root]
            with app.database() as db:
                for url in seeds:
                    if public_url(url,root):
                        kind='sitemap' if '.xml' in url else 'category'
                        db.execute('INSERT OR IGNORE INTO research_urls(store,url,kind) VALUES(?,?,?)',(store,url,kind))
                pending=[dict(r) for r in db.execute('SELECT * FROM research_urls WHERE store=? AND next_check<=? LIMIT 200000',(store,now))]
            if not pending:
                with app.database() as db:
                    next_due=db.execute('SELECT MIN(next_check) FROM research_urls WHERE store=?',(store,)).fetchone()[0]
                    old.update(store=store,status=old.get('status','discovering'),retry_at=max(now+900,next_due or now+86400))
                    db.execute('INSERT OR REPLACE INTO research_sources VALUES(?,?)',(store,json.dumps(old)))
                report(dict(old,cached=True))
                continue
            pending.sort(key=prioritise)
            visited=set()
            sitemap_reads=0
            for _ in range(per_store):
                choices=[r for r in pending if r['url'] not in visited and (r['kind']!='sitemap' or sitemap_reads<2)]
                if not choices:
                    break
                entry=choices[0]
                if entry['kind']!='sitemap':
                    # Share the page budget across requested products so a popular
                    # keyword cannot indefinitely starve the rest of a list.
                    target=variants(queries[state['query_cursor']%len(queries)])
                    candidate=max(choices,key=lambda r:len(r.get('words',set()) & target))
                    if candidate.get('words',set()) & target:
                        entry=candidate
                    state['query_cursor']+=1
                url=entry['url'];visited.add(url)
                if entry['kind']=='sitemap':
                    sitemap_reads+=1
                try:
                    if not rules.can_fetch('Despensa',url):
                        raise ValueError('robots_restricted')
                    content=read(url,32_000_000 if entry['kind']=='sitemap' else 8_000_000)
                    pages_read+=1
                    new_urls=discover_urls(content,url,store)
                    offers,methods=([],['official_sitemap']) if entry['kind']=='sitemap' else parse_page(content,store,url)
                    state['methods']=sorted(set(state['methods']+methods))
                    observed=datetime.now(timezone.utc).isoformat()
                    with app.database() as db:
                        indexed=db.execute('SELECT COUNT(*) FROM research_urls WHERE store=?',(store,)).fetchone()[0]
                        for target,kind in new_urls:
                            if indexed>=200000:
                                break
                            cursor=db.execute('INSERT OR IGNORE INTO research_urls(store,url,kind) VALUES(?,?,?)',(store,target,kind))
                            if cursor.rowcount:
                                indexed+=1
                                pending.append(dict(url=target,kind=kind,checked=0,failures=0))
                        for o in offers:
                            o['observed_at']=observed
                            db.execute('INSERT OR REPLACE INTO offers VALUES(?,?,?,?)',(o['id'],'',store,json.dumps(o)))
                            db.execute('INSERT OR REPLACE INTO history VALUES(?,?,?)',(o['id'],observed,o['price_cents']))
                        interval=86400 if entry['kind']=='sitemap' else 21600
                        db.execute('UPDATE research_urls SET checked=?,next_check=?,failures=0 WHERE store=? AND url=?',(time.time(),time.time()+interval,store,url))
                    state['count']+=len(offers)
                    pending.sort(key=prioritise)
                except Exception as error:
                    failures=entry.get('failures',0)+1
                    with app.database() as db:
                        db.execute('UPDATE research_urls SET checked=?,next_check=?,failures=? WHERE store=? AND url=?',(time.time(),time.time()+retry_delay(failures),failures,store,url))
                    blocked=isinstance(error,requests.HTTPError) and error.response.status_code in (401,403,429)
                    state['errors'].append('access_restricted' if blocked else 'robots_restricted' if str(error)=='robots_restricted' else 'source_unavailable')
                    if blocked:
                        break  # No retry storm or identity rotation against access blocks.
                report(dict(state))
            state['status']='ok' if state['count'] else 'discovering' if pages_read else 'unavailable'
            if state['errors'] and state['count']:
                state['status']='partial'
        except Exception as error:
            state['status']='unavailable'
            state['errors'].append('access_restricted' if isinstance(error,requests.HTTPError) and error.response.status_code in (401,403,429) else 'source_unavailable')
        if state['status']=='unavailable':
            state['failures']+=1
            state['retry_at']=time.time()+retry_delay(state['failures'])
        else:
            state['failures']=0
            state['retry_at']=time.time()+900
        with app.database() as db:
            state['indexed']=db.execute('SELECT COUNT(*) FROM research_urls WHERE store=?',(store,)).fetchone()[0]
            state['remaining']=db.execute('SELECT COUNT(*) FROM research_urls WHERE store=? AND checked=0',(store,)).fetchone()[0]
            state['catalogue_count']=db.execute("SELECT COUNT(*) FROM offers WHERE store=? AND user_id=''",(store,)).fetchone()[0]
            db.execute('INSERT OR REPLACE INTO research_sources VALUES(?,?)',(store,json.dumps(state)))
        report(state)


def query_progress(db, query, stores, owner):
    """Only the requested query's public source status is returned to the caller."""
    query=fold(query)[:120]
    rows=[dict(r) for r in db.execute('''SELECT t.store,t.status,t.found,t.error,t.next_check FROM research_tasks t
        JOIN research_watchers w ON w.query=t.query AND w.store=t.store WHERE t.query=? AND w.user_id=?''',(query,owner)) if r['store'] in stores]
    return dict(sources=rows,pending=sum(r['status'] in ('queued','running','waiting') for r in rows),
                finished=sum(r['status'] in ('done','partial','unavailable') for r in rows),total=len(rows))


def search_store(app, task, page_limit=6):
    """Give an explicit search its own bounded work, independent of catalogue sweeps."""
    from searching import rank, STOPWORDS
    store,query=task['store'],task['query']
    now=time.time()
    with app.database() as db:
        row=db.execute('SELECT data FROM research_sources WHERE store=?',(store,)).fetchone()
        source=json.loads(row[0]) if row else {}
    if source.get('status')=='unavailable' and source.get('retry_at',0)>now and source.get('errors'):
        return dict(status='unavailable',found=0,error=source['errors'][0],next_check=source['retry_at'])
    try:
        root=ROOTS[store];rules=robots(root)
        hints=sorted({part for w in variants(query) if len(w)>=3 and w not in STOPWORDS for part in (w[:3],w[-3:])})
        clause=' AND ('+' OR '.join('url LIKE ?' for _ in hints)+')' if hints else ''
        with app.database() as db:
            entries=[dict(r) for r in db.execute("SELECT * FROM research_urls WHERE store=? AND kind!='sitemap' AND next_check<=?"+clause,
                (store,now,*('%'+w+'%' for w in hints)))]
        choices=[]
        for entry in entries:
            label=unquote(urlsplit(entry['url']).path).replace('-',' ')
            leaf=label.rsplit('/',1)[-1]
            relevance=10*rank(query,leaf)+rank(query,label)
            if relevance:
                choices.append((relevance,entry))
        if not choices:
            for entry in entries:
                label=unquote(urlsplit(entry['url']).path).replace('-',' ')
                relevance=rank(query,label,fuzzy=True)
                if relevance:
                    choices.append((relevance,entry))
        choices.sort(key=lambda r:(-r[0],r[1]['checked']))
        if not choices:
            # Discovery may still be running for a new installation or retailer.
            waiting=not source.get('indexed') and now-task['requested']<1800
            return dict(status='waiting' if waiting else 'done',found=0,
                        error='indexing' if waiting else 'no_candidates',next_check=now+300 if waiting else 0)
        found=0;errors=[];methods=set()
        for _,entry in choices[:page_limit]:
            url=entry['url']
            if not rules.can_fetch('Despensa',url):
                errors.append('robots_restricted')
                continue
            try:
                content=read(url)
                offers,used=parse_page(content,store,url)
                methods.update(used)
                observed=datetime.now(timezone.utc).isoformat()
                with app.database() as db:
                    for o in offers:
                        o['observed_at']=observed
                        db.execute('INSERT OR REPLACE INTO offers VALUES(?,?,?,?)',(o['id'],'',store,json.dumps(o)))
                        db.execute('INSERT OR REPLACE INTO history VALUES(?,?,?)',(o['id'],observed,o['price_cents']))
                    db.execute('UPDATE research_urls SET checked=?,next_check=?,failures=0 WHERE store=? AND url=?',(time.time(),time.time()+21600,store,url))
                found+=len(offers)
            except Exception as error:
                blocked=isinstance(error,requests.HTTPError) and error.response.status_code in (401,403,429)
                errors.append('access_restricted' if blocked else 'source_unavailable')
                with app.database() as db:
                    failures=entry['failures']+1
                    db.execute('UPDATE research_urls SET checked=?,next_check=?,failures=? WHERE store=? AND url=?',
                        (time.time(),time.time()+retry_delay(failures),failures,store,url))
                if blocked:
                    break
        if found:
            with app.database() as db:
                latest=db.execute('SELECT data FROM research_sources WHERE store=?',(store,)).fetchone()
                source=json.loads(latest[0]) if latest else source
                source.update(store=store,status='partial' if errors else 'ok',failures=0,
                    checked_at=datetime.now(timezone.utc).isoformat(),methods=sorted(set(source.get('methods',[]))|methods),
                    catalogue_count=db.execute("SELECT COUNT(*) FROM offers WHERE store=? AND user_id=''",(store,)).fetchone()[0])
                db.execute('INSERT OR REPLACE INTO research_sources VALUES(?,?)',(store,json.dumps(source)))
        return dict(status='partial' if found and errors else 'done' if found or not errors else 'unavailable',
                    found=found,error=errors[0] if errors else '',next_check=time.time()+900 if errors else 0)
    except Exception:
        return dict(status='unavailable',found=0,error='source_unavailable',next_check=time.time()+900)


def priority_worker(app, stop=None):
    """Two small independent workers make interactive searches progress promptly."""
    stop=stop or threading.Event()
    while not stop.is_set():
        try:
            with app.database() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute("UPDATE research_tasks SET status='queued' WHERE status='running' AND updated<?",(time.time()-300,))
                row=db.execute("SELECT * FROM research_tasks WHERE status IN ('queued','waiting') AND next_check<=? ORDER BY requested DESC,store LIMIT 1",(time.time(),)).fetchone()
                task=dict(row) if row else None
                if task:
                    db.execute("UPDATE research_tasks SET status='running',updated=? WHERE query=? AND store=?",(time.time(),task['query'],task['store']))
            if not task:
                stop.wait(2)
                continue
            result=search_store(app,task)
            with app.database() as db:
                db.execute('UPDATE research_tasks SET status=?,updated=?,next_check=?,found=?,error=? WHERE query=? AND store=?',
                    (result['status'],time.time(),result['next_check'],result['found'],result['error'],task['query'],task['store']))
        except Exception:
            import logging
            logging.exception('Priority research failed')
            stop.wait(5)
