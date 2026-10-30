"""Attributed public vehicle and fuel data, with bounded persistent caches."""
import hashlib
import json
import math
import os
import re
import threading
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from catalog import fold

AGENT='Despensa/0.7 (+https://github.com/hubertdungen/Despensa)'
ADEME='https://data.ademe.fr/data-fair/api/v1/datasets/ademe-car-labelling'
DGEG='https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb'
ES_FUEL='https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/'
_locks=defaultdict(threading.Lock)


def read_json(url,params=None,limit=16_000_000):
    with requests.get(url,params=params,headers={'User-Agent':AGENT,'Accept':'application/json'},timeout=(4,15),stream=True) as r:
        r.raise_for_status();body=bytearray()
        for chunk in r.iter_content(65536):
            body.extend(chunk)
            if len(body)>limit:raise ValueError('Fonte demasiado grande')
        return json.loads(body)


def cached(folder,key,loader,ttl=21600,max_age=604800):
    root=Path(folder)/'public-sources';root.mkdir(exist_ok=True,parents=True)
    path=root/(key+'.json')
    with _locks[key]:
        old=None
        try:old=json.loads(path.read_text())
        except (OSError,ValueError):pass
        age=time.time()-old['fetched'] if old else float('inf')
        if 0<=age<ttl:return old['data'],False
        try:
            data=loader();temp=path.with_suffix('.tmp')
            temp.write_text(json.dumps({'fetched':time.time(),'data':data},ensure_ascii=False));temp.replace(path)
            return data,False
        except (requests.RequestException,ValueError,KeyError,TypeError,OSError):
            if old and 0<=age<max_age:return old['data'],True
            raise ValueError('Fonte pública temporariamente indisponível') from None


def number(value):
    value=float(str(value).replace('€','').replace(' ','').replace(',','.'))
    if not math.isfinite(value):raise ValueError('Valor não finito')
    return value


def ademe_vehicle(row):
    energy=row.get('Energie','')
    # Rechargeable hybrids need both battery and fuel state; don't disguise the
    # weighted homologation figure as petrol-only real-world consumption.
    if energy not in ('ESSENCE','GAZOLE','ESS+ELEC HNR','GAZ+ELEC HNR'):return None
    low=row.get('Conso_vitesse_mixte_Min');high=row.get('Conso_vitesse_mixte_Max')
    if not high or not 0<number(high)<50:return None
    fuel='diesel' if energy in ('GAZOLE','GAZ+ELEC HNR') else 'petrol95'
    label=' '.join(dict.fromkeys([row.get('Marque',''),row.get('Description_Commerciale') or row.get('Modèle','')])).strip()
    return dict(id='ademe:'+row['_id'],label=label,make=row.get('Marque',''),model=row.get('Modèle',''),year=None,
        engine_cc=row.get('Cylindrée'),power_kw=row.get('Puissance_maximale'),transmission=row.get('Type_de_boite',''),
        gears=row.get('Nombre_rapports'),fuel=fuel,consumption=round(number(high),3),consumption_min=low,
        consumption_max=high,unit='L/100 km',basis='published_upper_mixed',source='ADEME · homologação · mercado francês',
        source_url='https://data.ademe.fr/datasets/ademe-car-labelling',year_note='Ano não indicado pela fonte')


def vehicle_catalog(folder):
    def load():
        data=read_json(ADEME+'/lines',{'size':10000})
        if len(data.get('results',[]))<data.get('total',0):raise ValueError('Catálogo parcial')
        rows=[ademe_vehicle(r) for r in data['results']]
        meta=read_json(ADEME,limit=100000)
        return {'vehicles':[r for r in rows if r],'updated_at':meta.get('dataUpdatedAt','')}
    return cached(folder,'vehicles-ademe',load,86400,30*86400)


def epa_search(query,year):
    parts=query.strip().split(maxsplit=1)
    if len(parts)<2:return []
    root='https://www.fueleconomy.gov/ws/rest/vehicle'
    data=read_json(root+'/menu/options',dict(year=year,make=parts[0],model=parts[1]),limit=100000)
    rows=data.get('menuItem',[]);rows=[rows] if isinstance(rows,dict) else rows
    return [dict(id='epa:'+str(r['value']),label=f'{parts[0]} {parts[1]} {year} · {r["text"]}',source='EPA · mercado dos EUA',year=year,lookup_required=True) for r in rows[:20]]


def search_vehicles(folder,query,year=None):
    query=str(query).strip()[:100]
    if len(query)<2:return dict(vehicles=[],status='query_required')
    if year:
        if not 1984<=int(year)<=date.today().year+1:raise ValueError('Ano inválido')
        # ADEME does not identify model years: never silently match an old car to
        # the current generation of a model. The EEA lists what was registered in
        # the EU that year; EPA is explicitly a US fallback.
        if 2010<=int(year)<=2025:
            try:
                rows=search_eea(folder,query,int(year))
                if rows:return dict(vehicles=rows,status='ok',source='EEA · UE')
            except ValueError:pass
        rows,_=cached(folder,'epa-'+str(year)+'-'+hashlib.sha256(query.casefold().encode()).hexdigest()[:20],lambda:epa_search(query,int(year)),86400,7*86400)
        return dict(vehicles=rows,status='ok' if rows else 'no_verified_year',source='EPA · EUA')
    data,stale=vehicle_catalog(folder);wanted=fold(query).split()
    rows=[v for v in data['vehicles'] if all(w in fold(' '.join(str(v.get(k,'')) for k in ('label','engine_cc','transmission','power_kw'))) for w in wanted)]
    rows.sort(key=lambda v:(v['label'],v['fuel'],v['engine_cc'] or 0,v['consumption']))
    return dict(vehicles=rows[:40],total=len(rows),status='ok',stale=stale,updated_at=data['updated_at'])


def get_vehicle(folder,identifier):
    if re.fullmatch(r'eea:[0-9a-f]{20}:\d{1,3}',identifier):
        _,key,index=identifier.split(':')
        try:rows=json.loads((Path(folder)/'public-sources'/f'eea-{key}.json').read_text())['data']
        except (OSError,ValueError,KeyError):raise ValueError('Pesquise o carro novamente') from None
        if int(index)>=len(rows):raise ValueError('Motorização já não consta do catálogo')
        return dict(rows[int(index)],id=identifier,stale=False)
    if re.fullmatch(r'ademe:[A-Za-z0-9_-]{1,80}',identifier):
        data,stale=vehicle_catalog(folder)
        found=next((v for v in data['vehicles'] if v['id']==identifier),None)
        if not found:raise ValueError('Motorização já não consta do catálogo')
        return dict(found,source_updated_at=data['updated_at'],stale=stale)
    if re.fullmatch(r'epa:\d{1,8}',identifier):
        def load():
            r=read_json('https://www.fueleconomy.gov/ws/rest/vehicle/'+identifier.split(':')[1],limit=100000)
            fuel=r.get('fuelType1','');electric=fuel=='Electricity'
            if str(r.get('phevBlended','false')).lower()=='true' or r.get('atvType')=='Plug-in Hybrid':raise ValueError('Use o consumo real para um híbrido recarregável')
            rate=number(r['combE'])/1.609344 if electric else 235.214583/number(r['comb08'])
            return dict(id=identifier,label=f'{r["make"]} {r["model"]} {r["year"]} · {r.get("trany","")}',
                year=int(r['year']),fuel='electric' if electric else 'diesel' if fuel=='Diesel' else 'petrol98' if fuel=='Premium Gasoline' else 'petrol95',
                consumption=round(rate,3),unit='kWh/100 km' if electric else 'L/100 km',basis='EPA_mixed',
                source='FuelEconomy.gov · EPA · mercado dos EUA',source_url='https://www.fueleconomy.gov/feg/noframes/'+identifier.split(':')[1]+'.shtml',source_updated_at=r.get('modifiedOn',''))
        result,stale=cached(folder,identifier.replace(':','-'),load,86400,30*86400)
        return dict(result,stale=stale)
    raise ValueError('Identificador de carro inválido')


FUEL_NAMES={'Gasolina simples 95':'petrol95','Gasolina 98':'petrol98','Gasóleo simples':'diesel','GPL Auto':'lpg'}


def parse_pt_prices(data,today=None):
    today=today or date.today();found={}
    for row in data.get('resultado') or []:
        fuel=FUEL_NAMES.get(row.get('TipoCombustivel'))
        if not fuel or row.get('UnidadeMedida')!='litro':continue
        try:day=date.fromisoformat(row['Data']);price=number(row.get('PrecoMedioC4') or row['PrecoMedio'])
        except (ValueError,KeyError,TypeError):continue
        if not 0<price<10 or not 0<=(today-day).days<=7:continue
        if fuel not in found or day.isoformat()>found[fuel]['observed_on']:
            found[fuel]=dict(fuel=fuel,unit_price=price,unit='L',country='PT',observed_on=day.isoformat(),
                source='DGEG · preço médio diário ponderado · Portugal Continental',source_url='https://precoscombustiveis.dgeg.gov.pt/estatistica/preco-medio-diario')
    if not found:raise ValueError('Sem preços recentes DGEG')
    return found


def parse_es_prices(data,today=None):
    today=today or date.today();day=datetime.strptime(data['Fecha'],'%d/%m/%Y %H:%M:%S').date()
    if not 0<=(today-day).days<=7:raise ValueError('Preços espanhóis desatualizados')
    fields={'petrol95':'Precio Gasolina 95 E5','petrol98':'Precio Gasolina 98 E5','diesel':'Precio Gasoleo A','lpg':'Precio Gases licuados del petróleo'}
    values=defaultdict(list)
    for row in data.get('ListaEESSPrecio',[]):
        for fuel,field in fields.items():
            try:price=number(row.get(field,''))
            except (ValueError,TypeError):continue
            if 0<price<10:values[fuel].append(price)
    if not values:raise ValueError('Sem preços espanhóis')
    return {fuel:dict(fuel=fuel,unit_price=round(sum(v)/len(v),4),unit='L',country='ES',observed_on=day.isoformat(),
        station_count=len(v),source='MITECO · média simples dos preços comunicados pelos postos de Espanha',
        source_url='https://geoportalgasolineras.es/') for fuel,v in values.items()}


def fuel_prices(folder,country):
    if country=='PT':
        def load():
            types=read_json(DGEG+'/GetTiposCombustiveis',limit=100000)
            ids=','.join(str(r['Id']) for r in types['resultado'] if r['Descritivo'] in FUEL_NAMES)
            today=date.today();data=read_json(DGEG+'/PMD',dict(idsTiposComb=ids,dataIni=(today-timedelta(days=7)).isoformat(),dataFim=today.isoformat(),qtdPorPagina=7,pagina=1,orderDesc=1),limit=500000)
            return parse_pt_prices(data)
    elif country=='ES':
        def load():return parse_es_prices(read_json(ES_FUEL,limit=20_000_000))
    else:raise ValueError('País inválido')
    data,stale=cached(folder,'fuel-'+country,load,21600,3*86400)
    # Never use an old quote solely because an HTTP response was cached recently.
    data={k:v for k,v in data.items() if 0<=(date.today()-date.fromisoformat(v['observed_on'])).days<=7}
    if not data:raise ValueError('Preços de combustível desatualizados')
    return dict(prices=data,stale=stale,country=country)


EEA_SQL='https://discodata.eea.europa.eu/sql'
# EEA CO2 monitoring: one row per registered variant. 2010–2022 live in one
# table, newer years in per-year views (F = final, P = provisional).
EEA_TABLES={2023:'co2cars_2023Fv28',2024:'co2cars_2024Fv30',2025:'co2cars_2025Pv31'}
# grams of CO2 per litre burnt / 100: g/km ÷ factor = L/100 km
EEA_FUELS={'petrol':('petrol95',23.3),'diesel':('diesel',26.5),'lpg':('lpg',16.5)}
# Road consumption exceeds the lab figure: ICCT measured ~39 % over NEDC and
# ~18 % over WLTP for combustion cars. ponytail: fleet averages; the refuel log
# replaces them with the car's own figure.
REAL_WORLD={'nedc':1.39,'wltp':1.18}
MAKES={'VW':'VOLKSWAGEN','MERCEDES':'MERCEDES-BENZ','MERCEDESBENZ':'MERCEDES-BENZ','ALFA':'ALFA ROMEO','LAND':'LAND ROVER'}


def eea_post(query):
    # The EEA gateway rejects SQL sent by GET; its own UI posts a form.
    r=requests.post(EEA_SQL,files={'query':(None,query),'p':(None,'1'),'nrOfHits':(None,'500')},
        headers={'User-Agent':AGENT,'Accept':'application/json'},timeout=(5,40))
    r.raise_for_status();data=r.json()
    if 'results' not in data:raise ValueError('Resposta EEA inválida')
    return data['results']


def eea_search(make,model,year):
    """Variants registered in the EU for one make/model/year, from the EEA CO2 monitoring data."""
    # The query is built from text, so only letters, digits, spaces and dashes get through.
    make,model=(re.sub(r'[^A-Z0-9 -]','',fold(x).upper()).strip() for x in (make,model))
    make=MAKES.get(make.replace(' ','').replace('-',''),make)
    if not 2<=len(make)<=30 or not 1<=len(model)<=40 or not 2010<=year<=2025:raise ValueError('Pesquisa EEA inválida')
    table=EEA_TABLES.get(year,'co2cars')
    weighted=lambda col,alias:f'SUM(c.[{col}]*1.0*c.R)/NULLIF(SUM(CASE WHEN c.[{col}] IS NULL THEN 0 ELSE c.R END),0) {alias}'
    columns=[weighted('Ewltp (g/km)','wltp')]+([weighted('Enedc (g/km)','nedc'),weighted('E (g/km)','e')] if year<=2022 else [])
    rows=eea_post(f"SELECT c.Mk mk, c.Cn cn, c.Ft ft, c.Fm fm, c.[Ec (cm3)] cc, c.[Ep (KW)] kw, {', '.join(columns)}, SUM(c.R) n "
        f"FROM [CO2Emission].[latest].[{table}] c WHERE c.Mk LIKE '{make}%' AND c.Cn LIKE '%{model}%' AND c.[Year]={year} "
        "GROUP BY c.Mk, c.Cn, c.Ft, c.Fm, c.[Ec (cm3)], c.[Ep (KW)]")
    found=[]
    for row in rows:
        fuel=EEA_FUELS.get(str(row.get('ft') or '').strip().lower())
        if not fuel or (row.get('n') or 0)<50:continue  # PHEV/electric need real figures; tiny counts are noise
        basis,co2=('wltp',row.get('wltp')) if row.get('wltp') else ('nedc',row.get('nedc') or row.get('e'))
        if not co2 or not 30<co2<500:continue
        lab=co2/fuel[1];real=lab*REAL_WORLD[basis]
        hybrid=str(row.get('fm') or '').strip().upper()=='H'
        # Spellings vary between registrations (e.g. "VOLKSWAGEN VW"): label with the searched names.
        label=f"{make.title()} {model.title()} {year} · {row['cc'] or '?'} cm³ · {row['kw'] or '?'} kW · "+{'petrol95':'gasolina','diesel':'gasóleo','lpg':'GPL'}[fuel[0]]+(' híbrido' if hybrid else '')
        found.append(dict(label=label,make=str(row['mk']).strip(),model=str(row['cn']).strip(),year=year,engine_cc=row['cc'],power_kw=row['kw'],
            fuel=fuel[0],hybrid=hybrid,consumption=round(real,2),consumption_lab=round(lab,2),basis=basis,registrations=row['n'],
            unit='L/100 km',source=f'EEA · registos na UE em {year} · {basis.upper()} {round(lab,1)} L/100 km + desvio real médio',
            source_url='https://www.eea.europa.eu/en/datahub/datahubitem-view/fa8b1229-3db6-495d-b18e-9c9b3267c02b'))
    # Same label can come back with tiny CO2 differences between type approvals: keep the most registered.
    unique={}
    for v in sorted(found,key=lambda v:-v['registrations']):unique.setdefault((v['label'],v['fuel']),v)
    return list(unique.values())[:40]


def search_eea(folder,query,year):
    parts=str(query).split()
    if len(parts)<2:return []
    key='eea-'+hashlib.sha256(f'{fold(query)}|{year}'.encode()).hexdigest()[:20]
    rows,_=cached(folder,key,lambda:eea_search(parts[0],parts[1],year),30*86400,180*86400)
    return [dict(r,id=f'eea:{key[4:]}:{i}') for i,r in enumerate(rows)]


PT_FORMATS=[  # (pattern, first month, last month, letter pair used for interpolation)
    (r'[A-Z]{2}\d{4}',(1937,1),(1992,2),None),
    (r'\d{4}[A-Z]{2}',(1992,3),(2005,5),4),
    (r'\d{2}[A-Z]{2}\d{2}',(2005,5),(2020,2),2),
    (r'[A-Z]{2}\d{2}[A-Z]{2}',(2020,3),None,None)]
ES_LETTERS='BCDFGHJKLMNPRSTVWXYZ'
ES_STARTS={'B':date(2000,9,18),'C':date(2002,10,11),'D':date(2004,9,22),'F':date(2006,5,31),'G':date(2008,2,15),
    'H':date(2010,12,22),'J':date(2014,11,4),'K':date(2017,6,20),'L':date(2019,9,6),'M':date(2022,9,2),'N':date(2025,4,14)}


def plate_year(text,today=None):
    """Approximate first registration from a PT/ES plate sequence. No owner or model lookup exists for free."""
    today=today or date.today()
    plate=re.sub(r'[^A-Z0-9]','',fold(str(text)).upper())
    m=re.fullmatch(r'(\d{4})([BCDFGHJKLMNPRSTVWXYZ]{3})',plate)
    if m:
        letters=m.group(2);keys=sorted(ES_STARTS)
        if letters[0] not in ES_STARTS:raise ValueError('Sequência de matrícula espanhola ainda não emitida')
        i=keys.index(letters[0]);start=ES_STARTS[letters[0]]
        end=ES_STARTS[keys[i+1]] if i+1<len(keys) else start+(start-ES_STARTS[keys[i-1]])
        share=(ES_LETTERS.index(letters[1])*20+ES_LETTERS.index(letters[2])+int(m.group(1))/10000)/400
        when=min(today,start+(end-start)*share)
        return dict(country='ES',plate=plate,year=when.year,year_from=when.year,year_to=when.year,estimate=when.isoformat()[:7],
            precision='month',source='Sequência nacional espanhola (desde 2000)')
    for pattern,first,last,position in PT_FORMATS:
        if not re.fullmatch(pattern,plate):continue
        last=last or (today.year,today.month)
        result=dict(country='PT',plate=plate,year=None,year_from=first[0],year_to=last[0],estimate=None,precision='range',
            source='Formato da matrícula portuguesa',hint='Entre 1998 e 2020 o ano e o mês estão impressos na faixa amarela.')
        if position is not None:
            pair=(ord(plate[position])-65)*26+ord(plate[position+1])-65
            months=(last[0]-first[0])*12+last[1]-first[1]
            # ponytail: linear across letter pairs; issuance is uneven, so ±1–2 years
            total=first[0]*12+first[1]-1+round(months*pair/675)
            result.update(year=total//12,estimate=f'{total//12}-{total%12+1:02d}',precision='approximate')
        return result
    raise ValueError('Matrícula não reconhecida (Portugal, ou Espanha desde 2000)')
