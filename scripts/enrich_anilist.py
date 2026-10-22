#!/usr/bin/env python3
"""AniList 富化：重抓动漫/漫画，带角色表（主演 12 人 + 描述）。"""
import json, sys, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
API = "https://graphql.anilist.co"

Q = '''query ($page: Int, $type: MediaType) {
  Page(page: $page, perPage: 50) {
    pageInfo { hasNextPage }
    media(tag: "Yuri", type: $type, sort: POPULARITY_DESC) {
      id
      title { romaji native }
      characters(sort: [ROLE, RELEVANCE], perPage: 12) {
        edges { role node { name { full native } description(asHtml: false) } }
      }
      relations { edges { relationType node { id title { romaji } type } } }
    }
  }
}'''

def post(query, variables, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables}).encode(),
                method="POST", headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            if data.get("errors"): raise RuntimeError(data["errors"])
            return data["data"]["Page"]
        except Exception as e:
            last = e; time.sleep(3 * (i + 1))
    raise last

def main(limit=800):
    for mtype, fname in [("ANIME", "anilist_yuri_anime_v2.json"), ("MANGA", "anilist_yuri_manga_v2.json")]:
        out = RAW / fname
        if out.exists():
            print(f"skip {fname}"); continue
        items, page = [], 1
        while len(items) < limit:
            d = post(Q, {"page": page, "type": mtype})
            items.extend(d["media"])
            print(f"{fname} page {page}: +{len(d['media'])}", flush=True)
            if not d["pageInfo"]["hasNextPage"]: break
            page += 1; time.sleep(1.0)
        out.write_text(json.dumps(items[:limit], ensure_ascii=False), encoding="utf-8")
        print(f"saved {min(len(items),limit)} -> {out}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 800)
