"""Attributed public vehicle and fuel data, with bounded persistent caches."""
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

AGENT='Despensa/0.6 (+https://github.com/hubertdungen/Despensa)'
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
        # the current generation of a model. EPA is explicitly a US alternative.
        rows,_=cached(folder,'epa-'+str(year)+'-'+__import__('hashlib').sha256(query.casefold().encode()).hexdigest()[:20],lambda:epa_search(query,int(year)),86400,7*86400)
        return dict(vehicles=rows,status='ok' if rows else 'no_verified_year',source='EPA · EUA')
    data,stale=vehicle_catalog(folder);wanted=fold(query).split()
    rows=[v for v in data['vehicles'] if all(w in fold(' '.join(str(v.get(k,'')) for k in ('label','engine_cc','transmission','power_kw'))) for w in wanted)]
    rows.sort(key=lambda v:(v['label'],v['fuel'],v['engine_cc'] or 0,v['consumption']))
    return dict(vehicles=rows[:40],total=len(rows),status='ok',stale=stale,updated_at=data['updated_at'])


def get_vehicle(folder,identifier):
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
