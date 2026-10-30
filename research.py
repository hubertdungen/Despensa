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
from urllib.parse import unquote, urljoin, urlsplit, quote
from urllib import robotparser
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup
from catalog import STORE_MAP, CATEGORY_SOURCES, cents, fold, product_text, pack_size, parse_retailer

AGENT = 'Despensa/0.4 (+https://github.com/hubertdungen/Despensa; automatic grocery research)'
ROOTS = {
    'continente': 'https://www.continente.pt', 'auchan': 'https://www.auchan.pt',
    'pingo-doce': 'https://www.pingodoce.pt', 'lidl-pt': 'https://www.lidl.pt',
    'aldi-pt': 'https://www.aldi.pt', 'intermarche': 'https://www.intermarche.pt',
    'mercadona-pt': 'https://www.mercadona.pt', 'makro-pt': 'https://produtos.makro.pt',
    'recheio': 'https://folhetos.recheio.pt', 'mercadona-es': 'https://tienda.mercadona.es',
    'carrefour': 'https://www.carrefour.es', 'dia': 'https://www.dia.es',
    'eroski': 'https://supermercado.eroski.es', 'alcampo': 'https://www.compraonline.alcampo.es',
    'lidl-es': 'https://www.lidl.es', 'makro-es': 'https://tienda.makro.es',
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
    'recheio': ['https://folhetos.recheio.pt/recheio-cash-carry/recheio/folheto-digital-bons-negocios/'],
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
_leaflet_lock=threading.Lock()
_leaflet_cache={}


def setup(db):
    db.executescript(SCHEMA)


def upgrade_adapters(db):
    """Revisit pages missed by old parsers once, without resetting access blocks."""
    revision=db.execute("SELECT value FROM meta WHERE key='research_adapter_revision'").fetchone()
    if revision and json.loads(revision[0])>=7:
        return
    for store in ('continente','auchan','lidl-pt','lidl-es','aldi-pt','aldi-es','makro-es','makro-pt','recheio'):
        row=db.execute('SELECT data FROM research_sources WHERE store=?',(store,)).fetchone()
        source=json.loads(row[0]) if row else {}
        if store not in ('makro-es','makro-pt','recheio') and any(e in ('access_restricted','robots_restricted') for e in source.get('errors',[])):
            continue
        if row:
            source.update(retry_at=0,failures=0,status='discovering',errors=[])
            db.execute('UPDATE research_sources SET data=? WHERE store=?',(json.dumps(source),store))
        if store in ('makro-pt','recheio'):
            db.execute('DELETE FROM research_urls WHERE store=? AND url NOT LIKE ?',(store,ROOTS[store]+'/%'))
        db.execute('UPDATE research_urls SET next_check=0 WHERE store=?',(store,))
        db.execute("UPDATE research_tasks SET status='queued',next_check=0,found=0,error='' WHERE store=? AND requested>?",(store,time.time()-86400))
    db.execute("INSERT OR REPLACE INTO meta VALUES('research_adapter_revision','7')")


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
        task=db.execute('SELECT status,updated,requested FROM research_tasks WHERE query=? AND store=?',(query,store)).fetchone()
        if task and task[0]=='queued' and now-task[2]>30:
            db.execute("UPDATE research_tasks SET requested=? WHERE query=? AND store=?",(now,query,store))
        if task and (task[0] in ('queued','running') or now-task[1]<(60 if force else 900)):
            continue
        db.execute("INSERT OR REPLACE INTO research_tasks(query,store,requested) VALUES(?,?,?)",(query,store,now))
    db.execute("DELETE FROM research_tasks WHERE query NOT IN (SELECT query FROM research_queries)")
    db.execute("DELETE FROM research_watchers WHERE query NOT IN (SELECT query FROM research_queries)")


def variants(query):
    pairs = [('leite','leche'), ('azeite','aceite'), ('ovos','huevos'), ('frango','pollo'),
             ('cafe','cafe'), ('manteiga','mantequilla'), ('queijo','queso'), ('atum','atun'),
             ('acucar','azucar'), ('massa','pasta'), ('batata','patata'), ('agua','agua'),
             ('banana','platano'), ('maca','manzana'), ('morango','fresa'), ('laranja','naranja'),
             ('porco','cerdo'), ('vaca','vacuno'), ('peru','pavo'), ('carne','carne')]
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


class AccessBlocked(ValueError):
    """The source answers with a bot/captcha wall instead of its content."""


def access_blocked(error):
    return isinstance(error, AccessBlocked) or (isinstance(error, requests.HTTPError) and error.response is not None
        and error.response.status_code in (401, 403, 429))


def robots(root):
    hit = _rules.get(root)
    if hit and time.time() - hit[0] < 21600:
        return hit[1]
    content = read(root + '/robots.txt', 1_000_000).decode('utf-8-sig', 'replace')
    if '<html' in content.casefold() or '<!doctype' in content.casefold():
        raise AccessBlocked('A fonte exige verificação de acesso')
    parser = SourceRules()
    parser.parse(content.splitlines())
    _rules[root] = (time.time(), parser)
    return parser


class SourceRules(robotparser.RobotFileParser):
    """Apply wildcard paths and longest-match Allow precedence from RFC 9309."""
    def can_fetch(self, agent, url):
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        name=agent.casefold().split('/',1)[0]
        entries=[e for e in self.entries if any(a.casefold() in name for a in e.useragents)]
        if entries:
            longest=max(len(a) for e in entries for a in e.useragents if a.casefold() in name)
            entries=[e for e in entries if any(len(a)==longest and a.casefold() in name for a in e.useragents)]
        elif self.default_entry:
            entries=[self.default_entry]
        target=urlsplit(url);path=unquote(target.path or '/')+('?' + unquote(target.query) if target.query else '')
        matches=[]
        for entry in entries:
            for rule in entry.rulelines:
                pattern=unquote(rule.path)
                end=pattern.endswith('$');pattern=pattern[:-1] if end else pattern
                expression='^'+re.escape(pattern).replace(r'\*','.*')+('$' if end else '')
                if re.search(expression,path):
                    matches.append((len(pattern.replace('*','')),rule.allowance))
        return max(matches,default=(0,True))[1]


def leaflet_asset_allowed(url):
    """Only public signed assets referenced by the retailer's own publication."""
    root='https://cdn.ipaper.io'
    try:
        rules=robots(root)
    except requests.HTTPError as error:
        # This CDN has no public robots resource (403). RFC 9309 §2.3.1.3
        # permits access when that resource returns 4xx; actual asset failures
        # are still respected. Network errors/5xx never permit a request.
        if error.response.status_code not in (403,404):
            raise
        rules=SourceRules();rules.parse(['User-agent: *','Allow: /'])
        _rules[root]=(time.time(),rules)
    return rules.can_fetch('Despensa',url)


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
    result=dict(id=f'{store}:{oid}', store=store, country=STORE_MAP[store]['country'], name=name[:240],
        brand=brand, pack=f'{amount:g} {unit}' if amount else pack[:160], size=amount, unit=unit, price_cents=cents(price),
        condition='professional' if STORE_MAP[store]['professional'] else 'public', coupon='', balance_cents=0, source_url=url, image_url=image,
        channel='online', location='Preço publicado · disponibilidade local por confirmar',
        valid_from='', valid_to='', source_kind='automatic', vat_included=not STORE_MAP[store]['professional'],
        conditions_note='Preço publicado pela loja; confirmar disponibilidade e condições locais')
    result.update(extra)
    return result


def parse_page(html, store, url):
    """Independent parsers can rescue the same page when one representation changes."""
    from retailer_data import lidl_records,makro_records
    if store in ('makro-es','makro-pt','recheio') and html.lstrip().startswith(b'{' if isinstance(html,bytes) else '{'):
        data=json.loads(html)
        if store=='recheio' and data.get('kind')=='recheio_leaflet':
            from leaflets import records
            rows=records(data,base_offer)
            return rows,['official_leaflet'] if rows else []
        rows=makro_records(data,store,url,base_offer)
        return rows,['public_catalogue_api'] if rows else ['public_catalogue_metadata'] if data.get('result') else []
    soup = BeautifulSoup(html, 'html.parser')
    found, methods = {}, []
    if store.startswith('lidl-'):
        try:
            rows=lidl_records(soup,store,url,base_offer)
            found.update((o['id'],o) for o in rows)
            if rows:
                methods.append('embedded_catalogue')
        except (ValueError,TypeError,KeyError,AttributeError,RecursionError):
            pass
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
                props=json.loads(script.get_text())['props']['pageProps']
                data=props.get('apiData',[])
                data=[json.loads(data) if isinstance(data,str) else data,props.get('algoliaState',{})]
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
                    if re.match(r'^kg\s*[-–]',product.get('salesUnit',''),re.I):
                        o.update(variable_weight=True,size=1,unit='kg',pack='1 kg · venda a peso')
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
            # Continente's JSON-LD omits the pack and €/kg basis. Read them from
            # the matching main product, never from recommendation cards.
            heading=soup.select_one('h1') if store=='continente' else None
            continent_detail=soup.select_one('.product-name-details--wrapper') if heading and fold(heading.get_text(' ',strip=True))==fold(name) else None
            price_node = detail.select_one('.prices .price-container') if detail else None
            if not valid and price_node:
                valid = [dict(price=price_node.get_text('', strip=True))]
            if not valid:
                continue
            price = valid[0]
            pack = name + ' ' + str(product.get('description', ''))[:400]
            if continent_detail:
                unit_node=continent_detail.select_one('.ct-pdp--unit')
                if unit_node:
                    pack=unit_node.get_text(' ',strip=True)
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
            if continent_detail:
                primary=continent_detail.select_one('.pwc-tile--price-primary')
                displayed=primary.get_text('',strip=True) if primary else ''
                if re.search(r'€\s*/\s*kg\b',displayed,re.I):
                    amount,_=pack_size(pack)
                    o.update(price_cents=cents(re.sub(r'€\s*/\s*kg\b','',displayed,flags=re.I)),
                        variable_weight=True,size=1,unit='kg',pack='1 kg · venda a peso',nominal_pack=pack,
                        minimum_quantity=amount if 'minima' in fold(pack) else None,
                        weight_step=amount if 'emb' in fold(pack).split() else None)
                o['category']=' / '.join(dict.fromkeys(e.get_text(' ',strip=True) for e in soup.select('.breadcrumb-item, .breadcrumb a, [aria-label="breadcrumb"] a, [itemprop="breadcrumb"] a')))
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
            # A missing public price with a Lidl Plus-only embedded offer must
            # never be reconstructed from a generic structured-data fallback.
            if not (store.startswith('lidl-') and o['id']+':card' in found and o['id'] not in found):
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
            if loc and store=='makro-es' and loc.startswith('https://distribucion-hosteleria.makro.es/'):
                loc=loc.replace('https://distribucion-hosteleria.makro.es/','https://tienda.makro.es/',1)
            if loc and public_url(loc,root):
                result.append((loc,'sitemap' if index else 'product'))
        if store in ('makro-es','makro-pt') and index:
            # The official index separates categories (part 1) and products
            # (part 2); spend the bounded discovery budget on product prices.
            result.sort(key=lambda entry:'/part/2' not in entry[0])
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


def read_product(url,store,rules):
    """The official Makro SPA exposes the same anonymous data as its web shop."""
    if store=='recheio':
        from leaflets import collect
        with _leaflet_lock:
            hit=_leaflet_cache.get(url)
            if hit and time.monotonic()-hit[0]<60:
                return hit[1]
            content=json.dumps(collect(read(url),read,leaflet_asset_allowed)).encode()
            _leaflet_cache.clear()
            _leaflet_cache[url]=(time.monotonic(),content)
            return content
    if store in ('makro-es','makro-pt'):
        match=re.search(r'/shop/pv/(BTY-[A-Z]\d+)/(\d+)/(\d+)/',url)
        if match:
            country=STORE_MAP[store]['country'];locale='pt-PT' if country=='PT' else 'es-ES'
            target=ROOTS[store]+'/evaluate.article.v1/betty-variants?storeIds=00001&ids='+match[1]+match[2]+'&country='+country+'&locale='+locale
            if not rules.can_fetch('Despensa',target):
                raise ValueError('robots_restricted')
            return read(target)
    return read(url)


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
                        kind='sitemap' if '.xml' in url or '/sitemap' in url else 'category'
                        db.execute('INSERT OR IGNORE INTO research_urls(store,url,kind) VALUES(?,?,?)',(store,url,kind))
                # Release the write lock before the (large) frontier scan below:
                # holding it here stalled the priority workers into "database is locked".
                db.commit()
                pending=[dict(r) for r in db.execute('SELECT * FROM research_urls WHERE store=? AND next_check<=? LIMIT 200000',(store,now)) if public_url(r['url'],root)]
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
                    content=read(url,32_000_000) if entry['kind']=='sitemap' else read_product(url,store,rules)
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
                    if new_urls:
                        pending.sort(key=prioritise)
                except Exception as error:
                    failures=entry.get('failures',0)+1
                    # A delisted product (404/410) is gone: park it for a month instead of retrying daily.
                    gone=isinstance(error,requests.HTTPError) and error.response is not None and error.response.status_code in (404,410)
                    with app.database() as db:
                        db.execute('UPDATE research_urls SET checked=?,next_check=?,failures=? WHERE store=? AND url=?',(time.time(),time.time()+(30*86400 if gone else retry_delay(failures)),failures,store,url))
                    if gone:
                        report(dict(state));continue
                    blocked=access_blocked(error)
                    state['errors'].append('access_restricted' if blocked else 'robots_restricted' if str(error)=='robots_restricted' else 'source_unavailable')
                    if blocked:
                        break  # No retry storm or identity rotation against access blocks.
                report(dict(state))
            if not state['count'] and pages_read:
                # This pass found nothing new, but earlier passes may have: judge the catalogue, not the pass.
                with app.database() as db:
                    stored=db.execute("SELECT COUNT(*) FROM offers WHERE store=? AND user_id=''",(store,)).fetchone()[0]
            else:
                stored=0
            state['status']='ok' if state['count'] or stored else 'discovering' if pages_read else 'unavailable'
            if store=='makro-pt' and not state['count'] and 'public_catalogue_metadata' in state['methods']:
                state.update(status='unavailable',errors=['authentication_required'])
            if state['errors'] and state['count']:
                state['status']='partial'
        except Exception as error:
            state['status']='unavailable'
            state['errors'].append('access_restricted' if access_blocked(error) else 'source_unavailable')
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
    from searching import rank, STOPWORDS, discovery_query, intent_bonus, product_query
    store,query=task['store'],task['query']
    now=time.time()
    with app.database() as db:
        row=db.execute('SELECT data FROM research_sources WHERE store=?',(store,)).fetchone()
        source=json.loads(row[0]) if row else {}
    if source.get('status')=='unavailable' and source.get('retry_at',0)>now and any(e in ('access_restricted','robots_restricted','authentication_required') for e in source.get('errors',[])):
        return dict(status='unavailable',found=0,error=source['errors'][0],next_check=source['retry_at'])
    try:
        root=ROOTS[store];rules=robots(root)
        discovery=discovery_query(query) or query
        hints=sorted({part for w in variants(discovery) if len(w)>=3 and w not in STOPWORDS for part in (w[:3],w[-3:])})
        clause=' AND ('+' OR '.join('url LIKE ?' for _ in hints)+')' if hints else ''
        with app.database() as db:
            entries=[dict(r) for r in db.execute("SELECT * FROM research_urls WHERE store=? AND kind!='sitemap' AND next_check<=?"+clause,
                (store,now,*('%'+w+'%' for w in hints)))]
        choices=[]
        for entry in entries:
            if not public_url(entry['url'],root):
                continue
            parts=unquote(urlsplit(entry['url']).path).strip('/').split('/')
            # Auchan ends its product URLs with a numeric ID after the name.
            leaf=parts[-2] if len(parts)>1 and re.fullmatch(r'\d+\.html',parts[-1]) else parts[-1]
            leaf=re.sub(r'(?:-\d+)?\.html$','',leaf).replace('-',' ')
            label=' '.join(parts).replace('-',' ')
            relevance=10*rank(discovery,leaf)+rank(discovery,label)
            if relevance:
                relevance+=intent_bonus(discovery,leaf,label)
                choices.append((relevance,entry))
        if not choices:
            for entry in entries:
                if not public_url(entry['url'],root):
                    continue
                label=unquote(urlsplit(entry['url']).path).replace('-',' ')
                relevance=rank(discovery,label,fuzzy=True)
                if relevance:
                    choices.append((relevance,entry))
        choices.sort(key=lambda r:(-r[0],r[1]['checked']))
        # The public Auchan search is robots-permitted and supplies current tiles,
        # including products whose sitemap URL has no brand/format information.
        # Other retailers' blocked search routes are never used as substitutes.
        if store=='auchan':
            public_query=' '.join(w for w in product_query(query).split() if w not in STOPWORDS)
            url=root+'/pt/pesquisa?q='+quote(public_query)
            if rules.can_fetch('Despensa',url):
                with app.database() as db:
                    db.execute('INSERT OR IGNORE INTO research_urls(store,url,kind) VALUES(?,?,?)',(store,url,'search'))
                    entry=dict(db.execute('SELECT * FROM research_urls WHERE store=? AND url=?',(store,url)).fetchone())
                if entry['next_check']<=now:
                    choices.insert(0,(10000,entry))
        if store=='recheio':
            with app.database() as db:
                for url in SEEDS[store]:
                    db.execute('INSERT OR IGNORE INTO research_urls(store,url,kind) VALUES(?,?,?)',(store,url,'leaflet'))
                    entry=dict(db.execute('SELECT * FROM research_urls WHERE store=? AND url=?',(store,url)).fetchone())
                    if entry['next_check']<=now:
                        choices.insert(0,(10000,entry))
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
                content=read_product(url,store,rules)
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
                blocked=access_blocked(error)
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
        if store=='makro-pt' and not found and not errors and 'public_catalogue_metadata' in methods:
            # The official public catalogue explicitly requires an authenticated
            # Makro account to reveal prices. Authelia is not a retailer session.
            with app.database() as db:
                source.update(store=store,status='unavailable',errors=['authentication_required'],retry_at=time.time()+21600)
                db.execute('INSERT OR REPLACE INTO research_sources VALUES(?,?)',(store,json.dumps(source)))
            return dict(status='unavailable',found=0,error='authentication_required',next_check=source['retry_at'])
        if 'access_restricted' in errors and not found:
            with app.database() as db:
                source.update(store=store,status='unavailable',errors=errors,retry_at=time.time()+900)
                db.execute('INSERT OR REPLACE INTO research_sources VALUES(?,?)',(store,json.dumps(source)))
        return dict(status='partial' if found and errors else 'done' if found or not errors else 'unavailable',
                    found=found,error=errors[0] if errors else '',next_check=time.time()+900 if errors else 0)
    except Exception as error:
        blocked=access_blocked(error)
        kind='access_restricted' if blocked else 'source_unavailable'
        if blocked:
            with app.database() as db:
                source.update(store=store,status='unavailable',errors=[kind],retry_at=time.time()+900)
                db.execute('INSERT OR REPLACE INTO research_sources VALUES(?,?)',(store,json.dumps(source)))
        return dict(status='unavailable',found=0,error=kind,next_check=time.time()+900)


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
