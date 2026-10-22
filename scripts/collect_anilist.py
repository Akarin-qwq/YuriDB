#!/usr/bin/env python3
"""采集 AniList Yuri tag 的动漫/漫画/轻小说，按热度排序分页抓取。"""
import json, sys, time, urllib.request, pathlib

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
API = "https://graphql.anilist.co"

FIELDS = '''
      id idMal
      title { romaji english native }
      synonyms
      startDate { year month day }
      averageScore popularity favourites
      genres tags { name rank isGeneralSpoiler }
      format status chapters volumes episodes
      siteUrl
      description(asHtml: false)'''

Q_ANIME = f'query ($page: Int) {{ Page(page: $page, perPage: 50) {{ pageInfo {{ hasNextPage }} media(tag: "Yuri", type: ANIME, sort: POPULARITY_DESC) {{ {FIELDS} }} }} }}'
Q_MANGA = f'query ($page: Int) {{ Page(page: $page, perPage: 50) {{ pageInfo {{ hasNextPage }} media(tag: "Yuri", type: MANGA, format_in: [MANGA], sort: POPULARITY_DESC) {{ {FIELDS} }} }} }}'
Q_LN    = f'query ($page: Int) {{ Page(page: $page, perPage: 50) {{ pageInfo {{ hasNextPage }} media(tag: "Yuri", type: MANGA, format: NOVEL, sort: POPULARITY_DESC) {{ {FIELDS} }} }} }}'

def post(query, variables, retries=5):
    import time as _t
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables}).encode(),
                method="POST", headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            if data.get("errors"):
                raise RuntimeError(data["errors"])
            return data["data"]["Page"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            last = RuntimeError(f"{e} body={body}")
            print(f"  retry {i+1}/{retries} after error: {last}")
            _t.sleep(3 * (i + 1))
    raise last

def fetch(query, limit, fname):
    out = RAW / fname
    if out.exists():
        print(f"skip {fname} (exists)")
        return
    items, page = [], 1
    while len(items) < limit:
        data = post(query, {"page": page})
        items.extend(data["media"])
        print(f"{fname} page {page}: +{len(data['media'])} (total {len(items)})")
        if not data["pageInfo"]["hasNextPage"]:
            break
        page += 1
        time.sleep(1.0)
    out.write_text(json.dumps(items[:limit], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {min(len(items), limit)} -> {out}")

def main(limit=400):
    fetch(Q_ANIME, limit, "anilist_yuri_anime.json")
    fetch(Q_MANGA, limit, "anilist_yuri_manga.json")
    fetch(Q_LN, limit, "anilist_yuri_ln.json")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400)
