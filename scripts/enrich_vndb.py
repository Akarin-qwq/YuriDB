#!/usr/bin/env python3
"""富化 VNDB 作品：每部 VN 抓角色表 + 完整 tag（含结局类 tag）。
断点续跑：结果按 id 存 data/raw/enrich_vndb/<vnid>.json，已存在则跳过。"""
import json, sys, time, urllib.request, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "enrich_vndb"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.vndb.org/kana"

def post(path, payload, retries=6):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(f"{API}/{path}", data=json.dumps(payload).encode(), method="POST",
                headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last

def main(limit=None):
    vnids = sorted({e["id"].split(":",1)[1] for e in map(json.loads, open(ROOT/"data"/"corpus"/"works.jsonl", encoding="utf-8"))
                    if e["source"] == "vndb"})
    if limit:
        vnids = vnids[:limit]
    done = 0
    for vnid in vnids:
        f = OUT / f"{vnid}.json"
        if f.exists():
            continue
        try:
            vn = post("vn", {"filters": ["id","=",vnid],
                             "fields": "description, tags{id,name,rating,category,spoiler}", "results": 1})["results"][0]
            time.sleep(0.6)
            chars, page = [], 1
            while True:
                d = post("character", {
                    "filters": ["vn","=",["id","=",vnid]],
                    "fields": "name, original, description, vns.id, vns.role",
                    "results": 100, "page": page})
                chars.extend(d["results"])
                if not d.get("more") or page >= 3:
                    break
                page += 1
                time.sleep(0.6)
            roles = {c_vn["id"]: c_vn["role"] for c_vn in
                     next((c["vns"] for c in chars if False), [])}  # placeholder
            for c in chars:
                role = next((v["role"] for v in c.get("vns", []) if v["id"] == vnid), None)
                c["_role"] = role
            f.write_text(json.dumps({"vn": vn, "characters": chars}, ensure_ascii=False), encoding="utf-8")
            done += 1
            if done % 20 == 0:
                print(f"{done} enriched (last {vnid})", flush=True)
            time.sleep(0.6)
        except Exception as e:
            print(f"FAIL {vnid}: {e}", flush=True)
            time.sleep(5)
    print(f"DONE, newly enriched {done}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
