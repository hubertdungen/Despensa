"""Small, bounded adapters for public catalogues. Never bypass authentication or blocks."""
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

STORES = [
    ('continente', 'Continente', 'PT', '#d83e3e', True, False),
    ('auchan', 'Auchan', 'PT', '#da493b', True, False),
    ('pingo-doce', 'Pingo Doce', 'PT', '#257950', False, False),
    ('lidl-pt', 'Lidl', 'PT', '#2766a5', False, False),
    ('aldi-pt', 'Aldi', 'PT', '#1f568d', False, False),
    ('intermarche', 'Intermarché', 'PT', '#bd3434', False, False),
    ('mercadona-pt', 'Mercadona', 'PT', '#278459', False, False),
    ('makro-pt', 'Makro', 'PT', '#255698', False, True),
    ('recheio', 'Recheio', 'PT', '#bd3536', False, True),
    ('mercadona-es', 'Mercadona', 'ES', '#278459', False, False),
    ('carrefour', 'Carrefour', 'ES', '#255e9b', False, False),
    ('dia', 'DIA', 'ES', '#bd3536', False, False),
    ('eroski', 'Eroski', 'ES', '#bd3536', False, False),
    ('alcampo', 'Alcampo', 'ES', '#da493b', False, False),
    ('lidl-es', 'Lidl', 'ES', '#2766a5', False, False),
    ('makro-es', 'Makro', 'ES', '#255698', False, True),
    ('aldi-es', 'Aldi', 'ES', '#1f568d', False, False),
]
STORE_MAP = {s[0]: dict(id=s[0], name=s[1], country=s[2], color=s[3], automatic=s[4], professional=s[5]) for s in STORES}
LOYALTY = {
    'continente': 'Cartão Continente', 'auchan': 'Clube Auchan', 'pingo-doce': 'Poupa Mais',
    'lidl-pt': 'Lidl Plus', 'lidl-es': 'Lidl Plus', 'intermarche': 'Cartão Poupança',
    'carrefour': 'El Club Carrefour', 'dia': 'Club DIA', 'eroski': 'EROSKI club', 'alcampo': 'Club Alcampo',
}
for sid, store in STORE_MAP.items():
    store['automatic'] = True
    store['loyalty'] = LOYALTY.get(sid)
    store['subscription'] = None
STORE_MAP['continente']['subscription'] = dict(name='EntregaZero', kind='delivery',
    source='https://www.continente.pt/servicos/entrega-zero/')


def fold(value):
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in unicodedata.normalize('NFKD', str(value).lower()) if not unicodedata.combining(c))).strip()


def product_text(value):
    """Shared Iberian product vocabulary; unknown words are retained verbatim."""
    text = ' ' + fold(value) + ' '
    for es, pt in [('aceite de oliva','azeite'),('aceite oliva','azeite'),
                   ('sin lactosa','sem lactose'),('semidesnatada','meio gordo'),
                   ('desnatada','magro'),('entera','gordo'),('virgen extra','virgem extra'),
                   ('virgen','virgem'),('aire libre','ar livre'),('leche','leite'),
                   ('huevos','ovos'),('aceite','oleo'),('pollo','frango'),('fresca','fresco'),
                   ('queso','queijo'),('mantequilla','manteiga'),('azucar','acucar'),
                   ('atun','atum'),('patatas','batatas'),('patata','batata'),
                   ('manzanas','macas'),('manzana','maca'),('yogur','iogurte'),
                   ('yogures','iogurtes'),('harina','farinha'),('espaguetis','esparguete')]:
        text = text.replace(' ' + es + ' ', ' ' + pt + ' ')
    return text.strip()


def cents(value):
    try:
        d = Decimal(str(value).replace('€', '').replace(' ', '').replace(',', '.'))
        if not d.is_finite() or d <= 0 or d > 100000:
            raise ValueError('Preço inválido')
        return int((d * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, TypeError):
        raise ValueError('Preço inválido')


def pack_size(text):
    """Only unambiguous mass/volume or explicitly counted units; unknown packs stay unknown."""
    text = str(text).lower().replace(',', '.')
    m = re.search(r'(?:(\d+)\s*[x×]\s*)?(\d+(?:\.\d+)?)\s*(kg|gr|g|ml|cl|lt|l)\b', text)
    if m:
        count, size, unit = m.groups()
        factor = {'g': .001, 'gr': .001, 'ml': .001, 'cl': .01}.get(unit, 1)
        return round(int(count or 1) * float(size) * factor, 6), 'kg' if unit in ('g', 'gr', 'kg') else 'l'
    m = re.search(r'(\d+)\s*(?:un(?:id(?:ades)?)?|uds|unidades)\b', text)
    return (float(m.group(1)), 'un') if m else (None, None)


def get(url, params=None):
    # One catalogue page per query, no retries on blocks, no login/cookie harvesting.
    response = requests.get(url, params=params, timeout=(8, 22), headers={
        'User-Agent': 'Despensa/0.2 (+https://github.com/hubertdungen/Despensa; personal grocery planner)',
        'Accept-Language': 'pt-PT,es;q=0.8',
    })
    response.raise_for_status()
    if len(response.content) > 8_000_000:
        raise ValueError('Resposta demasiado grande')
    return response


def parse_retailer(html, store):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    selector = '[data-product-tile-impression]' if store == 'continente' else '[data-gtm]'
    for tile in soup.select(selector):
        try:
            meta = json.loads(tile.get('data-product-tile-impression') or tile['data-gtm'])
            name = meta.get('name', '').strip()
            if not name or not meta.get('id'):
                continue
            price_node = tile.select_one('.pwc-tile--price-primary') if store == 'continente' else tile.select_one('.sales .value[content]')
            # The displayed sale price takes precedence over analytics metadata.
            price = cents(price_node.get('content') or price_node.get_text('', strip=True)) if price_node else cents(meta['price'])
            link = tile.select_one('a[href*="/produto/"]') if store == 'continente' else tile.select_one('.pdp-link a')
            if not link:
                continue
            size_node = tile.select_one('.pwc-tile--quantity')
            pack = size_node.get_text(' ', strip=True) if size_node else name
            amount, unit = pack_size(pack)
            image_node = tile.select_one('img.ct-tile-image, img.tile-image')
            image_url = (image_node.get('data-src') or image_node.get('src') or '').strip() if image_node else ''
            text = fold(tile.get_text(' ', strip=True))
            # Conditional promotions are withheld from optimisation until verified.
            conditional = any(word in text for word in ('em cartao', 'com cartao', 'cupao', 'clube auchan'))
            results.append(dict(id=f'{store}:{meta["id"]}', store=store, country='PT', name=name,
                brand=meta.get('brand', ''), pack=pack, size=amount, unit=unit, price_cents=price,
                condition='unknown' if conditional else 'public', coupon='', balance_cents=0,
                source_url=urljoin('https://www.continente.pt' if store == 'continente' else 'https://www.auchan.pt', link['href']),
                channel='online', location='Catálogo online · localização por confirmar', valid_from='', valid_to='',
                source_kind='automatic', conditions_note='Ver condições na fonte' if conditional else 'Preço público observado; confirmar na loja',
                vat_included=True, image_url=image_url))
        except (ValueError, KeyError, TypeError):
            continue
    return results


# Deliberately bounded coverage: first public page of each category, no query scraping.
CATEGORY_SOURCES = [
    dict(store='continente', name='Arroz', url='https://www.continente.pt/supermercado/mercearia/arroz-massa-e-farinha/arroz/'),
    dict(store='continente', name='Massa', url='https://www.continente.pt/supermercado/mercearia/arroz-massa-e-farinha/massa/'),
    dict(store='continente', name='Leite', url='https://www.continente.pt/supermercado/laticinios-e-ovos/leites/'),
    dict(store='continente', name='Azeite', url='https://www.continente.pt/supermercado/mercearia/azeite-oleo-e-vinagre/azeite/'),
    dict(store='continente', name='Ovos', url='https://www.continente.pt/supermercado/laticinios-e-ovos/ovos/'),
    dict(store='auchan', name='Arroz', url='https://www.auchan.pt/pt/alimentacao/mercearia/arroz-e-massa/arroz/'),
    dict(store='auchan', name='Azeite', url='https://www.auchan.pt/pt/alimentacao/mercearia/azeite-oleo-e-vinagre/azeite/'),
    dict(store='auchan', name='Leite', url='https://www.auchan.pt/pt/alimentacao/produtos-lacteos/leites/'),
]
_ROBOTS = {}


def fetch_category(source):
    import time
    from urllib import robotparser
    from urllib.parse import urlsplit
    host = urlsplit(source['url']).netloc
    cached = _ROBOTS.get(host)
    if not cached or time.time() - cached[0] > 21600:
        response = get('https://' + host + '/robots.txt')
        rules = robotparser.RobotFileParser()
        rules.parse(response.text.splitlines())
        _ROBOTS[host] = (time.time(), rules)
    if not _ROBOTS[host][1].can_fetch('Despensa', source['url']):
        raise ValueError('A fonte restringe esta recolha em robots.txt')
    results = parse_retailer(get(source['url']).text, source['store'])
    if not results:
        raise ValueError('A categoria não devolveu produtos legíveis')
    return results[:36]
