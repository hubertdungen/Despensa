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
    first=text.strip().split()[0] if words else ''
    if unit=='kg' and first in ('banana','bananas') and not words & {'desidratada','desidratadas','seca','secas','congelada','congeladas','chips','pure','pao','pan','frita','fritas'}:
        origin='madeira' if 'madeira' in words else 'canarias' if 'canarias' in words else 'comum'
        special=next((w for w in ('rosa','vermelha','prata','ouro','maca') if w in words),None)
        if special:
            origin=special
        key,label,query='fruit:banana:'+origin,'Banana'+(' da Madeira' if origin=='madeira' else ' das Canárias' if origin=='canarias' else ''),'banana'
        if special:
            label+=' '+special
    elif unit=='kg' and first in ('maca','macas','pera','peras','laranja','laranjas','morango','morangos','uva','uvas','abacate','abacates','kiwi','kiwis') and not words & {
            'bebida','pure','polpa','cortada','fatiada','desidratada','seca','congelado','congelada','congelados','congeladas','calda','iogurte'} and not any(k in product_text(offer.get('category','')) for k in ('congel','bebida','sumos')):
        fruit=first[:-1] if first.endswith('s') else first
        names={'maca':'Maçã','pera':'Pera','laranja':'Laranja','morango':'Morango','uva':'Uva','abacate':'Abacate','kiwi':'Kiwi'}
        varieties={'maca':('granny smith','pink lady','bravo esmolfe','gala','golden','fuji','reineta'),
            'pera':('rocha','conference','williams'), 'laranja':('sumo','mesa','navel'),
            'uva':('red globe','branca','brancas','preta','pretas','rosada','rosadas'),
            'kiwi':('amarelo','verde'),'abacate':('hass',)}
        variety=next((v for v in varieties.get(fruit,()) if ' '+v+' ' in text),'nao indicada')
        seedless='sem grainha' if ' sem grainha ' in text or ' sem semente ' in text else 'nao indicado'
        key=f'fruit:{fruit}:{variety}:{seedless if fruit=="uva" else ""}'
        label=names[fruit]+(' · '+variety if variety!='nao indicada' else '')
        query=fruit+(' '+variety if variety!='nao indicada' else '')
    elif unit=='kg' and words & {'frango','porco','vaca','vitela','novilho','peru'} and not words & {
            'alimento','racao','gato','gatos','cao','caes','sabor','caldo','sopa','panado','panados','fiambre',
            'cozido','cozinhado','assado','fumado','salsicha','salsichas','nuggets','refeicao','caril','hamburguer','hamburgueres'}:
        species=next(k for k in ('frango','porco','vitela','novilho','vaca','peru') if k in words)
        cuts=[k for k in ('lombinhos','peito','costeletas','entremeada','secretos','lombo','coxas','pernas','perna','asas','bifes','moelas','bochechas','cachaco','entrecosto') if k in words]
        cut=cuts[0] if len(cuts)==1 and len(words & {'frango','porco','vaca','vitela','novilho','peru'})==1 else None
        if not cuts and len(words & {'frango','porco','vaca','vitela','novilho','peru'})==1 and words & {'inteiro','inteira','completo'}:
            cut='inteiro'
        if cut:
            state='congelado' if any(w.startswith('congelad') for w in words) or 'congel' in product_text(offer.get('category','')) else 'fresco' if 'fresco' in words or any(x in product_text(offer.get('category','')) for x in ('talho','frescos','produtos frescos')) else 'estado nao indicado'
            bone='sem osso' if ' sem osso ' in text else 'com osso' if ' com osso ' in text else 'osso nao indicado'
            skin='sem pele' if ' sem pele ' in text else 'pele nao indicada'
            seasoned='temperado' if words & {'temperado','temperada','marinado','marinada'} else ''
            minced='picado' if words & {'picado','picada'} else ''
            key=f'meat:{species}:{cut}:{state}:{bone}:{skin}:{seasoned}:{minced}'
            label=f'{cut.capitalize()} de {species}'+(' · congelado' if state=='congelado' else '')+(' · '+seasoned if seasoned else '')
            query=f'{cut} {species}'
    elif unit=='l' and first=='agua' and not words & {'sabores','sabor','fruta','limao','vermelhos','melancia','vitaminas','tonica','coco'}:
        kind='com gas' if ' com gas ' in text or ' con gas ' in text else 'sem gas' if any(x in text for x in (' sem gas ',' sin gas ',' mineral ',' nascente ')) else None
        if kind:
            key,label,query='water:'+kind,'Água '+kind,'agua '+kind
    elif 'leite' in words and unit == 'l' and not words & {'po', 'condensado', 'infantil', 'crescimento', 'lactentes', 'chocolate', 'creme'}:
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
    labels={'bio':'biológico','proteina':'proteína','calcio':'cálcio','vitaminas':'vitaminas','cabra':'cabra','ovelha':'ovelha'}
    return dict(key=key + ':' + ','.join(extra) + ':' + unit,
        label=label+(' · '+', '.join(labels[e] for e in extra) if extra else ''),query=query,unit=unit)


def comparisons(offers, profile, day=None):
    from planner import ineligible_reason
    day = day or datetime.now(timezone.utc).date().isoformat()
    groups = {}
    for offer in offers:
        group = family(offer)
        entry = groups.setdefault(group['key'], dict(group, offers=[]))
        reason=ineligible_reason(offer,profile,day)
        row = dict(offer, eligible=reason is None,ineligible_reason=reason,
            unit_price_cents=round(offer['price_cents'] / offer['size'], 4) if offer.get('size') else None)
        row['details']=item_details(offer)
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
        group['details']=item_details(group['offers'][0],group)
    return sorted(groups.values(), key=lambda g: (-g['store_count'], -g['saving_percent'], g['label']))


def item_details(offer, group=None):
    """Defaults from published product metadata; ambiguous formats stay unspecified."""
    text=set(product_text(offer['name']+' '+offer.get('category','')).split())
    category='Laticínios' if text & {'leite','iogurte','queijo','manteiga','kefir'} else 'Frescos' if text & {'fruta','frutas','banana','maca','pera','laranja','kiwi','abacate','talho','peixaria','frango','porco','novilho','vitela'} else 'Casa e limpeza' if text & {'detergente','lixivia','limpeza','amaciador','desinfetante'} else 'Mercearia'
    specific=not group or group.get('same_reference') or group.get('exact_reference')
    name=offer['name'] if specific else group['label']
    query=name if specific else group['query']
    if specific and offer.get('brand') and not set(product_text(offer['brand']).split()) <= set(product_text(query).split()):
        query+=' '+offer['brand']
    return dict(name=name,query=query[:120],category=category,unit=offer.get('unit') if specific else group['unit'],
        quantity=offer.get('size') or 1 if specific else 1,offer_id=offer['id'] if specific and not (group and group.get('exact_reference')) else '',
        family=group['key'] if group and not group.get('same_reference') else '')
