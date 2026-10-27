"""Read public retailer JSON. No script execution, credentials or inferred VAT."""
import json
import re
from datetime import datetime
from urllib.parse import urljoin, quote
from zoneinfo import ZoneInfo


def decode_nuxt(raw):
    """Nuxt/devalue's indexed JSON graph, restricted to plain data and wrappers."""
    values=json.loads(raw)
    if not isinstance(values,list) or len(values)>50000:
        raise ValueError('Invalid public page data')
    cache,active={},set()
    def resolve(index,depth=0):
        if type(index) is not int or index<0:
            return None
        if index>=len(values) or depth>80 or index in active:
            raise ValueError('Invalid graph reference')
        if index in cache:
            return cache[index]
        active.add(index)
        value=values[index]
        if isinstance(value,dict):
            result={k:resolve(v,depth+1) for k,v in value.items()}
        elif isinstance(value,list):
            if value and isinstance(value[0],str):
                result=resolve(value[1],depth+1) if value[0] in ('Reactive','ShallowReactive','Ref','ShallowRef') and len(value)==2 else None
            else:
                result=[resolve(v,depth+1) for v in value]
        else:
            result=value
        active.remove(index);cache[index]=result
        return result
    return resolve(0)


def lidl_records(soup,store,url,make_offer):
    script=soup.select_one('#__NUXT_DATA__')
    if not script:
        return []
    root=decode_nuxt(script.get_text())
    rows=[]
    for product in (root.get('data') or {}).values():
        if not isinstance(product,dict) or not product.get('itemId') or not product.get('keyfacts'):
            continue
        name=product['keyfacts'].get('fullTitle') or product['keyfacts'].get('title')
        if not name:
            continue
        regions=product.get('regionsV2',{})
        selected=next((r.get('regionPriceId') for r in regions.values() if r.get('isDefault')),None)
        regional=product.get('regionsPrices',{}).get(str(selected),{}) if selected is not None else {}
        public=regional.get('currentPrice') or product.get('price') or {}
        card=regional.get('currentLidlPlusPrice')
        if card is None:
            card=next(iter(product.get('lidlPlus') or []),{})
        prices=[('public',public),('card',card.get('price') or {})]
        image=next(iter(product.get('media',{}).get('imageMap',{}).values()),{}).get('smallUrl','')
        brand=product.get('info',{}).get('brand',{}).get('name','')
        zone=ZoneInfo('Europe/Lisbon' if store.endswith('-pt') else 'Europe/Madrid')
        for condition,price in prices:
            if not price.get('price') or price.get('currencyCode','EUR')!='EUR':
                continue
            pack=price.get('packaging',{}).get('text','')
            o=make_offer(store,str(product['itemId'])+(':card' if condition=='card' else ''),name,
                price['price'],pack,url,image,brand)
            if re.search(r'(?:ao|al|por|/|per)\s*kg\b',pack,re.I):
                o.update(size=1,unit='kg',pack='1 kg · venda a peso',variable_weight=True)
            o.update(condition=condition,channel='store',ean=next(iter(product.get('eans') or []),''),
                category=product['keyfacts'].get('wonCategoryPrimary',''))
            if condition=='card' and (price.get('discount',{}).get('showFrom') or
                    re.search(r'cup[aã]o|cup[oó]n|ativ|activ',card.get('lidlPlusText',''),re.I)):
                o['condition']='unknown'
            # Use dates attached to this exact price, never a different future campaign.
            for key,source in [('valid_from','startDate'),('valid_to','endDate')]:
                if price.get(source):
                    o[key]=datetime.fromisoformat(price[source].replace('Z','+00:00')).astimezone(zone).date().isoformat()
            o['conditions_note']='Preço com Lidl Plus; confirmar condições e loja' if condition=='card' else 'Preço público publicado; confirmar loja'
            rows.append(o)
    return rows


def makro_records(data,store,url,make_offer):
    """Anonymous Makro ES catalogue; explicitly use gross price at the named centre."""
    country='PT' if store=='makro-pt' else 'ES'
    root='https://produtos.makro.pt' if country=='PT' else 'https://tienda.makro.es'
    centre_name='Makro Alfragide' if country=='PT' else 'Makro Barajas'
    rows=[]
    for article in data.get('result',{}).values():
        for variant in article.get('variants',{}).values():
            for bundle in variant.get('bundles',{}).values():
                if not bundle.get('anonymousVisible') or not bundle.get('anonymousSearchable'):
                    continue
                centre=bundle.get('stores',{}).get('00001',{})
                delivery=centre.get('possibleDeliveryModes',{}).get('STORE',{})
                fulfillment=delivery.get('possibleFulfillmentTypes',{}).get('STORE',{})
                price=fulfillment.get('sellingPriceInfo') or {}
                # No volume discounts, personal negotiated prices or ex-VAT fallback.
                if not price.get('valid') or price.get('priceHiddenReason') or price.get('currency')!='EUR' or not price.get('grossPrice'):
                    continue
                identity=bundle['bundleId'];oid=identity['bettyBundleId']
                name=bundle.get('description') or variant.get('description')
                if not name:
                    continue
                weight=bundle.get('isWeightArticle')=='WEIGHT'
                content=bundle.get('contentData',{})
                unit=content.get('netContentVolume') or content.get('netPieceWeight') or {}
                # Explicit netPieceWeight describes the sold unit. A multi-pack's
                # bundleSize multiplies it; a weight article's grossPrice is €/kg.
                count=float(bundle.get('bundleSize') or 1)
                measure={'GRAM':'g','KG':'kg','LITER':'l','MILLILITER':'ml','ML':'ml','L':'l'}.get(unit.get('uom'))
                pack=f"{float(unit['value'])*count:g} {measure}" if measure and unit.get('value') else name
                if re.search(r'\bhuevos\b',name,re.I) and re.search(r'contiene\s+\d+\s+huevos',name,re.I):
                    pack=f'{count:g} un'
                if weight:
                    pack='1 kg'
                path='/shop/pv/{articleNumber}/{variantNumber}/{bundleNumber}/'.format(**identity)+quote(name.replace(' ','-'))
                source=urljoin(root,path)
                o=make_offer(store,oid,name,price['grossPrice'],pack,source,
                    bundle.get('imageUrlS',''),bundle.get('brandName',''))
                o.update(condition='professional',vat_included=True,channel='store',variable_weight=weight,
                    available=fulfillment.get('availability')=='AVAILABLE' and not centre.get('delisted'),
                    location=centre_name+' · centro 00001',requires_location_confirmation=True,
                    conditions_note=f'Preço com IVA do centro {centre_name} (00001); requer acesso profissional e confirmação da loja',
                    category=' / '.join(c.get('name','') for c in bundle.get('categories',[])))
                if weight:
                    # The source exposes the average sellable piece separately.
                    piece=bundle.get('contentData',{}).get('weightPerPiece',{})
                    if piece.get('uom')=='KG' and piece.get('value'):
                        o['nominal_pack']=f"{piece['value']} kg · peso médio publicado"
                    o['pack']='1 kg · venda a peso'
                rows.append(o)
    return rows
