import json, time, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
API = "https://graphql.anilist.co"
F = '''id idMal title { romaji english native } synonyms startDate { year month day }
 averageScore popularity favourites genres tags { name rank isGeneralSpoiler } format status
 chapters volumes episodes siteUrl description(asHtml: false)
 characters(sort: [ROLE, RELEVANCE], perPage: 15) { edges { role node { name { full native } description(asHtml: false) } } }'''
Q = 'query ($page: Int, $type: MediaType) { Page(page: $page, perPage: 50) { pageInfo { hasNextPage } media(tag: "Yuri", type: $type, sort: POPULARITY_DESC) { %s } } }' % F
def post(q, v, retries=5):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(API, data=json.dumps({"query":q,"variables":v}).encode(), method="POST",
                headers={"Content-Type":"application/json","User-Agent":"yuri-corpus/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r: d=json.load(r)
            if d.get("errors"): raise RuntimeError(d["errors"])
            return d["data"]["Page"]
        except Exception as e:
            last=e; time.sleep(3*(i+1))
    raise last
for t,fn in [("ANIME","anilist_yuri_anime_deep.json"),("MANGA","anilist_yuri_manga_deep.json")]:
    out=RAW/fn
    items,page=[],1
    while len(items)<2000:
        d=post(Q,{"page":page,"type":t})
        items.extend(d["media"])
        print(fn,"p",page,"+",len(d["media"]),flush=True)
        if not d["pageInfo"]["hasNextPage"]: break
        page+=1; time.sleep(1.0)
    out.write_text(json.dumps(items,ensure_ascii=False),encoding="utf-8")
    print("saved",len(items),fn,flush=True)
