#!/usr/bin/env python3
"""采集 VNDB g1986 (Girl x Girl Romance Only) —— 纯百合 galgame。"""
import json, sys, time, urllib.request, pathlib

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
API = "https://api.vndb.org/kana/vn"
FIELDS = "title, alttitle, released, rating, votecount, tags{id,name,rating,category}, description"

def post(payload, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(API, data=json.dumps(payload).encode(), method="POST",
                headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last = e
            print(f"  retry {i+1}/{retries}: {e}")
            time.sleep(3 * (i + 1))
    raise last

def main(limit=800, page_size=100):
    out = RAW / "vndb_yuri_only_vn.json"
    items, page = [], 1
    while len(items) < limit:
        payload = {
            "filters": ["and", ["tag", "=", "g1986"], ["devstatus", "=", 0]],
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
    out.write_text(json.dumps(items[:limit], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {min(len(items), limit)} -> {out}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 800)
