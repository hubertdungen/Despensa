"""Rank grocery searches by name, brand and format without changing product identity."""
import re
from catalog import product_text

STOPWORDS = {'de','da','do','das','dos','del','la','el','los','las','para','por','con','com','e','y','a','o'}


def tokens(text):
    text=product_text(re.sub(r'(\d)([a-zA-Z])',r'\1 \2',str(text)))
    result=[]
    for word in text.split():
        if word in STOPWORDS:
            continue
        if len(word)>4 and word.endswith('oes'):
            word=word[:-3]+'ao'
        elif len(word)>4 and word.endswith('ais'):
            word=word[:-3]+'al'
        elif word=='paes':
            word='pao'
        elif len(word)>3 and word.endswith('s'):
            word=word[:-1]
        result.append(word)
    return result


def one_edit(a,b):
    if abs(len(a)-len(b))>1:
        return False
    if len(a)==len(b):
        diffs=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
        return len(diffs)<=1 or len(diffs)==2 and diffs[1]==diffs[0]+1 and a[diffs[0]]==b[diffs[1]] and a[diffs[1]]==b[diffs[0]]
    if len(a)>len(b):
        a,b=b,a
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:
            return a[i:]==b[i+1:]
    return True


def rank(query, name, brand='', pack='', fuzzy=False):
    wanted=tokens(query)
    if not wanted:
        return 1
    primary=tokens(name)
    brand_words=tokens(brand)
    words=set(primary+brand_words+tokens(pack))
    score=0
    for word in wanted:
        if word in words:
            score+=12 if word in primary else 10 if word in brand_words else 6
        elif len(word)>=3 and any(w.startswith(word) for w in words):
            score+=5
        elif fuzzy and len(word)>=5 and any(one_edit(word,w) for w in words if len(w)>=4):
            score+=2
        else:
            return 0
    return score+(10 if product_text(query)==product_text(name) else 0)


def find(offers, query):
    ranked=[(rank(query,o['name'],o.get('brand',''),o.get('pack','')),o) for o in offers]
    ranked=[(score,o) for score,o in ranked if score]
    corrected=False
    if query and not ranked:
        ranked=[(rank(query,o['name'],o.get('brand',''),o.get('pack',''),fuzzy=True),o) for o in offers]
        ranked=[(score,o) for score,o in ranked if score]
        corrected=bool(ranked)
    ranked.sort(key=lambda row:(-row[0],row[1]['price_cents']/row[1]['size'] if row[1].get('size') else 1e12,row[1]['name']))
    return [o for _,o in ranked],corrected
