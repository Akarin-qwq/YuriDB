#!/usr/bin/env python3
"""采集 VNDB 百合 galgame（g97 Girl x Girl Romance）。按投票数排序分页抓取。"""
import json, sys, time, urllib.request, pathlib

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
API = "https://api.vndb.org/kana/vn"
FIELDS = "title, alttitle, titles{lang,title}, aliases, released, rating, votecount, tags{id,name,rating,category}, olang, length_minutes"

def post(payload):
    req = urllib.request.Request(API, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1 (local research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def main(limit=400, page_size=100):
    out = RAW / "vndb_yuri_vn.json"
    items = []
    page = 1
    while len(items) < limit:
        payload = {
            "filters": ["and", ["tag", "=", "g97"], ["devstatus", "=", 0]],
            "fields": FIELDS, "sort": "votecount", "reverse": True,
            "results": page_size, "page": page,
        }
        data = post(payload)
        items.extend(data["results"])
        print(f"page {page}: +{len(data['results'])} (total {len(items)})")
        if not data.get("more"):
            break
        page += 1
        time.sleep(1.2)
    items = items[:limit]
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {len(items)} -> {out}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400)
