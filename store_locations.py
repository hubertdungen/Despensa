"""Bounded official Portuguese store locators, independent of map-provider availability."""
import json
import time
import threading
from urllib import robotparser
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from catalog import get

_lock=threading.Lock()
_cache=None


def parse_locations(html,store):
    soup=BeautifulSoup(html,'html.parser')
    results=[]
    if store=='continente':
        for element in soup.select('[data-lat][data-lng][data-name]'):
            try:
                results.append(dict(id='official:continente:'+element['data-name'],store=store,country='PT',
                    name=element['data-name'],coords=[float(element['data-lng']),float(element['data-lat'])],
                    address=element.get_text(' ',strip=True),opening_hours='',source='official'))
            except (ValueError,KeyError):
                continue
    else:
        for element in soup.select('[data-locations]'):
            try:
                records=json.loads(element['data-locations'])
            except (ValueError,TypeError):
                continue
            for record in records:
                if 'auchan' not in record.get('name','').casefold() or 'gasolineira' in record.get('name','').casefold():
                    continue
                try:
                    detail=BeautifulSoup(record.get('infoWindowHtml',''),'html.parser')
                    address=detail.find('address')
                    results.append(dict(id='official:auchan:'+record['name'],store=store,country='PT',name=record['name'],
                        coords=[float(record['longitude']),float(record['latitude'])],
                        address=address.get_text(' ',strip=True) if address else '',opening_hours='',source='official'))
                except (ValueError,KeyError,TypeError):
                    continue
    return list({r['id']:r for r in results}.values())


def official_locations():
    global _cache
    with _lock:
        if _cache and time.monotonic()-_cache[0]<86400:
            return _cache[1]
        results=[]
        for store,url in [('continente','https://feed.continente.pt/lojas'),('auchan','https://www.auchan.pt/pt/lojas')]:
            try:
                rules=robotparser.RobotFileParser()
                rules.parse(get('https://'+urlsplit(url).netloc+'/robots.txt').text.splitlines())
                if not rules.can_fetch('Despensa',url):
                    continue
                results.extend(parse_locations(get(url).text,store))
            except Exception:
                continue
        _cache=(time.monotonic(),results)
        return results
