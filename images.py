"""Fetch only catalogue-provided retailer thumbnails; no arbitrary image URL endpoint."""
import hashlib
import threading
import time
from urllib.parse import urlsplit
import requests

_cache = {}
_lock = threading.Lock()
HOSTS = {'www.continente.pt','www.auchan.pt'}
IMAGE_PATHS = {
    'www.continente.pt': ('/dw/image/',),
    'www.auchan.pt': ('/dw/image/', '/on/demandware.static/-/Sites-auchan-pt-master-catalog/'),
    'static.pingodoce.pt': ('/dw/image/',), 'www.lidl.pt': ('/assets/',),
    'www.lidl.es': ('/assets/',), 'prd.an-pcm.com': ('/dam/products/',),
    's7g10.scene7.com': ('/is/image/aldinord/',),
    'cdn.metro-group.com': ('/es/',),
}


def thumbnail(offer):
    url=offer.get('image_url','')
    if offer.get('source_kind')!='automatic' or not url:
        return None
    key=hashlib.sha256(url.encode()).hexdigest()
    with _lock:
        hit=_cache.get(key)
        if hit and time.monotonic()-hit[0]<86400:
            return hit[1]
    for _ in range(3):
        parsed=urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname not in IMAGE_PATHS or parsed.port not in (None,443) or parsed.username or not parsed.path.startswith(IMAGE_PATHS.get(parsed.hostname, ())):
            return None
        with requests.get(url,timeout=(4,8),allow_redirects=False,stream=True,
                headers={'User-Agent':'Despensa/0.4 (+https://github.com/hubertdungen/Despensa)'}) as response:
            if response.status_code in (301,302,303,307,308):
                from urllib.parse import urljoin
                url=urljoin(url,response.headers.get('Location',''))
                continue
            response.raise_for_status()
            mime=response.headers.get('Content-Type','').split(';')[0]
            if mime not in ('image/jpeg','image/png','image/webp','image/avif','image/gif'):
                return None
            data=bytearray()
            for chunk in response.iter_content(32768):
                data.extend(chunk)
                if len(data)>2_000_000:
                    return None
            result=(bytes(data),mime)
        with _lock:
            # Bounded memory cache: at most 16 MB of thumbnails.
            if sum(len(x[1][0]) for x in _cache.values())+len(data)>16_000_000:
                _cache.clear()
            _cache[key]=(time.monotonic(),result)
        return result
    return None
