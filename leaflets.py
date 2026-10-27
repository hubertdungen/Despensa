"""Structured prices from the official public Recheio digital leaflets."""
import json
import re
from datetime import date
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from catalog import fold,pack_size

RECHEIO_URL='https://folhetos.recheio.pt/recheio-cash-carry/recheio/folheto-digital-bons-negocios/'
MONTHS={name:i+1 for i,name in enumerate(('janeiro','fevereiro','marco','abril','maio','junho',
    'julho','agosto','setembro','outubro','novembro','dezembro'))}


def settings(html):
    soup=BeautifulSoup(html,'html.parser')
    for script in soup.select('script:not([src])'):
        match=re.search(r'\bwindow\.staticSettings\s*=\s*(\{)',script.get_text())
        if match:
            result,_=json.JSONDecoder().raw_decode(script.get_text()[match.start(1):])
            return result
    raise ValueError('Missing public leaflet settings')


def dates(text):
    # Require the explicit year; never derive a promotion's year from today's date.
    pattern=r'(\d{1,2}) de (\w+) a (\d{1,2}) de (\w+) de (\d{4})'
    for match in re.finditer(pattern,fold(text)):
        d1,m1,d2,m2,year=match.groups()
        if m1 not in MONTHS or m2 not in MONTHS:
            continue
        end=date(int(year),MONTHS[m2],int(d2))
        start=date(int(year)-(MONTHS[m1]>MONTHS[m2]),MONTHS[m1],int(d1))
        if 0<=(end-start).days<=90:
            return start.isoformat(),end.isoformat()
    raise ValueError('Unconfirmed leaflet validity')


def public_asset(url,paper):
    target=urlsplit(url)
    return (target.scheme=='https' and target.hostname=='cdn.ipaper.io' and target.port in (None,443)
        and not target.username and not target.password and len(url)<2500
        and bool(re.fullmatch(r'/iPaper/Papers/[a-f0-9-]{36}/Enrichments/v1/[^/]+/[^/]+/Page\d+-\d+\.json',target.path))
        and url.startswith(paper.get('aws',{}).get('url','invalid')+'Enrichments/'))


def collect(html,read,asset_allowed):
    paper=settings(html)
    source=paper.get('paperCompleteUrl','')
    # Restrict this adapter to the retailer-owned publication, never a user URL.
    if not source.startswith('https://folhetos.recheio.pt/recheio-cash-carry/recheio/'):
        raise ValueError('Unexpected leaflet publisher')
    start,end=dates((paper.get('pageTexts') or [''])[0])
    # This publication explicitly states Cash prices excluding VAT. Without that
    # statement, do not guess the tax basis from a prominent price or icon.
    if not re.search(r'precos cash sem iv\s*a',fold(paper['pageTexts'][0])):
        raise ValueError('Unconfirmed leaflet VAT basis')
    chunks=list(dict.fromkeys(paper.get('enrichments',{}).get('chunkUrls',{}).values()))
    if not 0<len(chunks)<=8:
        raise ValueError('Unexpected leaflet size')
    products=[]
    for url in chunks:
        if not public_asset(url,paper) or not asset_allowed(url):
            raise ValueError('Leaflet asset not permitted')
        products.extend(json.loads(read(url)).get('enrichments',[]))
    return dict(kind='recheio_leaflet',source=source,valid_from=start,valid_to=end,products=products,
        pages=paper.get('pageTexts',[]),publication=paper.get('name','Folheto Recheio'))


def records(data,make_offer):
    found={}
    for product in data.get('products',[]):
        if product.get('type')!=13 or not product.get('productId') or not product.get('name') or not product.get('price'):
            continue
        page=product.get('pageIndex')
        if type(page) is not int or page<0 or page>=len(data.get('pages',[])):
            continue
        name=product['name'];source=data['source']+'?page='+str(page+1)
        oid=f"leaflet:{product['productId']}:{data['valid_from']}:{page+1}"
        try:
            o=make_offer('recheio',oid,name,product['price'],name,source)
        except (ValueError,TypeError):
            continue
        words=fold(name).split()
        if words and words[-1]=='kg' and not pack_size(name)[0]:
            o.update(size=1,unit='kg',pack='1 kg · venda a peso',variable_weight=True)
        # Abbreviated LT/ML without a quantity is not enough to infer a pack.
        o.update(condition='professional',vat_included=False,channel='store',
            valid_from=data['valid_from'],valid_to=data['valid_to'],location='Portugal Continental · folheto Cash',
            publication=data.get('publication',''),reference=product['productId'],
            conditions_note='Preço Cash sem IVA; Cartão Recheio e códigos de atividade 1, 2, 3 ou 7. Confirmar mínimos e condições no folheto.')
        # Keep repeated references with different page conditions separate; a
        # volume-tier price is never silently selected as a regular unit price.
        page_text=fold(data['pages'][page])
        if 'a partir' in page_text or 'leve mais' in page_text:
            o['condition']='unknown'
        found[o['id']]=o
    return list(found.values())
