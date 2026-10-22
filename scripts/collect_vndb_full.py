#!/usr/bin/env python3
"""VNDB 全量扩抓：g97 (Girl x Girl Romance) 全部 + g1986 (GxG Only) 全部。
按 votecount 降序分页，断点续跑（每页存一个分片文件）。"""
import json, sys, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "vndb_full"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.vndb.org/kana/vn"
FIELDS = "title, alttitle, released, rating, votecount, tags{id,name,rating,category,spoiler}, description"

def post(payload, retries=6):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(API, data=json.dumps(payload).encode(), method="POST",
                headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last = e; time.sleep(3 * (i + 1))
    raise last

def run(tagid, fname):
    page = 1
    total = 0
    while True:
        f = OUT / f"{fname}_p{page:03d}.json"
        if f.exists():
            d = json.load(open(f, encoding="utf-8"))
            total += len(d["results"])
            if not d.get("more"):
                print(f"{fname}: already complete, {total} entries"); return
            page += 1; continue
        d = post({"filters": ["and", ["tag","=",tagid], ["devstatus","=",0]],
                  "fields": FIELDS, "sort": "votecount", "reverse": True, "results": 100, "page": page})
        f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        total += len(d["results"])
        print(f"{fname} p{page}: +{len(d['results'])} (total {total}, more={d.get('more')})", flush=True)
        if not d.get("more"):
            return
        page += 1
        time.sleep(1.0)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("g97", "both"):
        run("g97", "g97")
    if which in ("g1986", "both"):
        run("g1986", "g1986")
    print("DONE")
