"""Conservative product-family suggestions, with explicit unit and variant boundaries."""
from datetime import datetime, timezone
from catalog import fold, product_text


def valid_gtin(value):
    value=str(value)
    if not value.isascii() or not value.isdigit() or len(value) not in (8,12,13,14) or not int(value):
        return False
    total=sum(int(char)*(3 if i%2==0 else 1) for i,char in enumerate(reversed(value[:-1])))
    return (10-total%10)%10==int(value[-1])


def family(offer):
    text = ' ' + product_text(offer['name']) + ' '
    words = set(text.split())
    unit = offer.get('unit')
    extra = []
    if words & {'biologico', 'biologica', 'bio', 'ecologico', 'ecologica'}:
        extra.append('bio')
    for variant, tokens in [('proteina',{'proteina','proteinas','protein'}),('calcio',{'calcio'}),
                            ('vitaminas',{'vitaminas'}),('cabra',{'cabra'}),('ovelha',{'ovelha','oveja'})]:
        if words & tokens:
            extra.append(variant)
    key = label = query = None
    if 'leite' in words and unit == 'l' and not words & {'po', 'condensado', 'infantil', 'crescimento', 'lactentes', 'chocolate', 'creme'}:
        fat = 'meio gordo' if ' meio gordo ' in text or ' semidesnatada ' in text else 'magro' if 'magro' in words else 'gordo' if 'gordo' in words else None
        if fat:
            kind = 'fresco' if words & {'fresco', 'pasteurizado', 'refrigerado'} else 'uht'
            lactose = 'sem lactose' if ' sem lactose ' in text else ''
            key = 'milk:' + fat + ':' + kind + ':' + lactose
            label = f'Leite {kind.upper() if kind == "uht" else kind} {fat} {lactose}'.strip()
            query = f'leite {fat} {lactose}'.strip()
    elif 'arroz' in words and unit == 'kg' and not words & {'farinha', 'bebida', 'papa', 'tortitas', 'bolachas', 'vinagre', 'barras'}:
        kind = next((k for k in ('carolino', 'basmati', 'agulha', 'vaporizado', 'risotto') if k in words), None)
        if kind:
            integral = 'integral' if 'integral' in words else ''
            key, label, query = 'rice:' + kind + integral, f'Arroz {kind} {integral}'.strip(), f'arroz {kind} {integral}'.strip()
    elif 'azeite' in words and unit == 'l' and not words & {'oleo', 'spray', 'aromatizado'}:
        kind = 'virgem extra' if 'virgem' in words and 'extra' in words else 'virgem' if 'virgem' in words else 'refinado'
        key, label, query = 'oil:' + kind, 'Azeite ' + kind, 'azeite' + (' ' + kind if kind != 'refinado' else '')
    elif 'ovos' in words and unit == 'un' and not words & {'codorniz', 'chocolate', 'claras', 'gemas', 'liquidos'}:
        grade = next((k for k in ('xl', 'l', 'm', 's') if k in words), 'sem classe indicada')
        origin = 'ar livre' if ' ar livre ' in text else 'solo' if 'solo' in words else 'nao especificada'
        key, label, query = 'eggs:' + grade + ':' + origin, 'Ovos de galinha · ' + grade, 'ovos'
    elif unit == 'kg' and words & {'massa', 'esparguete', 'espaguetis', 'penne', 'fusilli'}:
        kind = next((k for k in ('esparguete', 'espaguetis', 'penne', 'fusilli', 'macarrao') if k in words), None)
        if kind:
            integral = 'integral' if 'integral' in words else ''
            key, label, query = 'pasta:' + kind + integral, f'Massa {kind} {integral}'.strip(), f'{kind} {integral}'.strip()
    if not key:
        gtin=offer.get('ean','')
        if valid_gtin(gtin) and offer.get('size') and unit:
            gtin=str(gtin).zfill(14)
            return dict(key=f'gtin:{gtin}:{offer["size"]:g}:{unit}',label=offer['name'],query=offer['name'],unit=unit)
        return dict(key='reference:' + offer['id'], label=offer['name'], query=offer['name'], unit=unit)
    return dict(key=key + ':' + ','.join(extra) + ':' + unit, label=label + (' · biológico' if extra else ''), query=query, unit=unit)


def comparisons(offers, profile, day=None):
    from planner import eligible
    day = day or datetime.now(timezone.utc).date().isoformat()
    groups = {}
    for offer in offers:
        group = family(offer)
        entry = groups.setdefault(group['key'], dict(group, offers=[]))
        row = dict(offer, eligible=eligible(offer, profile, day),
            unit_price_cents=round(offer['price_cents'] / offer['size'], 4) if offer.get('size') else None)
        entry['offers'].append(row)
    for group in groups.values():
        group['offers'].sort(key=lambda o: (not o['eligible'], o['unit_price_cents'] if o['unit_price_cents'] is not None else 1e12, o['price_cents']))
        valid = [o for o in group['offers'] if o['eligible'] and o['unit_price_cents'] is not None]
        group['store_count'] = len({o['store'] for o in valid})
        group['best_id'] = valid[0]['id'] if valid else None
        group['saving_per_unit_cents'] = round(max(o['unit_price_cents'] for o in valid) - min(o['unit_price_cents'] for o in valid), 4) if valid else 0
        group['saving_percent'] = round(100 * group['saving_per_unit_cents'] / max(o['unit_price_cents'] for o in valid), 1) if valid else 0
        group['same_reference'] = group['key'].startswith('reference:')
        group['exact_reference'] = group['key'].startswith('gtin:')
    return sorted(groups.values(), key=lambda g: (-g['store_count'], -g['saving_percent'], g['label']))
