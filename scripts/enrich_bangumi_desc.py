#!/usr/bin/env python3
"""Bangumi 描述/详情回填：对每条 bangumi 记录拉 /v0/subjects/{id}。"""
import json, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "enrich_bangumi_detail"
OUT.mkdir(parents=True, exist_ok=True)

def get(url, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "yuri-corpus/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e; time.sleep(2 * (i + 1))
    raise last

def main():
    done = 0
    for media in ("book", "anime", "game"):
        p = ROOT / "data" / "raw" / f"bangumi_yuri_{media}.json"
        if not p.exists(): continue
        for s in json.load(open(p, encoding="utf-8")):
            f = OUT / f"{s['id']}.json"
            if f.exists(): continue
            try:
                d = get(f"https://api.bgm.tv/v0/subjects/{s['id']}")
                f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
                done += 1
                time.sleep(0.6)
            except Exception as e:
                print(f"FAIL {s['id']}: {e}", flush=True)
    print(f"DONE detail, {done} fetched")

if __name__ == "__main__":
    main()
