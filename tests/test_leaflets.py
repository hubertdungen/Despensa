"""Public leaflet integrity, honest tax basis and robots decisions."""
import json
from datetime import datetime,timezone
import pytest
import requests
import leaflets
from research import SourceRules,base_offer
from planner import ineligible_reason,match
from app import default_profile


def paper():
    root='https://cdn.ipaper.io/iPaper/Papers/12345678-1234-1234-1234-123456789abc/'
    return dict(paperCompleteUrl=leaflets.RECHEIO_URL,aws={'url':root},
        pageTexts=['27 de outubro a 2 de novembro de 2026. Preços Cash sem IVA'],
        enrichments={'chunkUrls':{'0':root+'Enrichments/v1/one/two/Page1-8.json'}})


def html(data):
    return '<script>window.staticSettings = '+json.dumps(data)+';ignoredCode()</script>'


def test_public_leaflet_prices_keep_vat_excluded_and_explicit_validity():
    raw={'enrichments':[dict(type=13,productId='coffee',name='CAFÉ DELTA 1 KG',price='9,99',pageIndex=0),
        dict(type=13,productId='banana',name='BANANA KG',price='0,99',pageIndex=0)]}
    data=leaflets.collect(html(paper()),lambda url:json.dumps(raw),lambda url:True)
    rows=leaflets.records(data,base_offer)
    assert len(rows)==2
    coffee,banana=rows
    assert coffee['price_cents']==999 and coffee['vat_included'] is False
    assert coffee['valid_from']=='2026-10-27' and coffee['valid_to']=='2026-11-02'
    assert coffee['condition']=='professional' and coffee['image_url']==''
    assert banana['variable_weight'] and banana['size']==1 and banana['unit']=='kg'
    now=datetime(2026,10,27,tzinfo=timezone.utc)
    profile=default_profile();profile['stores']['recheio'].update(enabled=True,access=True)
    assert ineligible_reason(dict(coffee,observed_at=now.isoformat()),profile,'2026-10-27',now)=='vat_excluded'


def test_leaflet_never_follows_external_or_unapproved_assets():
    data=paper();data['enrichments']['chunkUrls']['0']='https://attacker.example/a.json'
    def forbidden(url):
        raise AssertionError('Unsafe URL fetched')
    with pytest.raises(ValueError):leaflets.collect(html(data),forbidden,lambda url:True)
    with pytest.raises(ValueError):leaflets.collect(html(paper()),forbidden,lambda url:False)
    data=paper();data['pageTexts']=['27 de outubro a 2 de novembro de 2026']
    with pytest.raises(ValueError):leaflets.collect(html(data),forbidden,lambda url:True)


def test_leaflet_dates_never_guess_year_and_handle_year_transition():
    assert leaflets.dates('28 de dezembro a 3 de janeiro de 2027')==('2026-12-28','2027-01-03')
    with pytest.raises(ValueError):leaflets.dates('27 de outubro a 2 de novembro')
    assert leaflets.records(dict(products=[dict(type=13,productId='a',name='Café',price=1,pageIndex=2)],pages=['one']),base_offer)==[]


def test_robots_wildcards_specific_agents_and_allow_precedence():
    rules=SourceRules();rules.parse(['User-agent: *','Disallow: /*.js$','Disallow: /private/*','Allow: /private/public/',
        'Disallow: /same','Allow: /same','User-agent: Googlebot-Image','Disallow: /'])
    assert not rules.can_fetch('Despensa','https://example.org/a.js')
    assert rules.can_fetch('Despensa','https://example.org/a.json')
    assert rules.can_fetch('Despensa','https://example.org/a.js?x=1')
    assert not rules.can_fetch('Despensa','https://example.org/private/one')
    assert rules.can_fetch('Despensa','https://example.org/private/public/one')
    assert rules.can_fetch('Despensa','https://example.org/same')
    assert not rules.can_fetch('Googlebot-Image','https://example.org/a.json')


def test_missing_cdn_robots_does_not_allow_server_failures(monkeypatch):
    import research
    def error(code):
        response=requests.Response();response.status_code=code
        return requests.HTTPError(response=response)
    monkeypatch.setattr(research,'robots',lambda root:(_ for _ in ()).throw(error(403)))
    assert research.leaflet_asset_allowed('https://cdn.ipaper.io/asset.json')
    monkeypatch.setattr(research,'robots',lambda root:(_ for _ in ()).throw(error(503)))
    with pytest.raises(requests.HTTPError):research.leaflet_asset_allowed('https://cdn.ipaper.io/asset.json')


def test_planner_uses_brand_and_format_and_excludes_prepared_generic_matches():
    row=dict(name='Água mineral sem gás',brand='Luso',pack='7 l',size=7,unit='l')
    assert match(dict(query='Água Luso 7L',unit='l'),row)
    assert not match(dict(query='Água Luso 5L',unit='l'),row)
    assert not match(dict(query='banana',unit='kg'),dict(name='Iogurte banana',size=1,unit='kg'))
