#!/usr/bin/env python3
"""Bangumi 富化：对已抓的 bangumi 条目逐个拉 /v0/subjects/{id}/characters。"""
import json, sys, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "enrich_bangumi"
OUT.mkdir(parents=True, exist_ok=True)

def get(url, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "yuri-corpus/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e; time.sleep(3 * (i + 1))
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
                chars = get(f"https://api.bgm.tv/v0/subjects/{s['id']}/characters")
                f.write_text(json.dumps({"subject": s["id"], "media": media, "characters": chars}, ensure_ascii=False), encoding="utf-8")
                done += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"FAIL {s['id']}: {e}", flush=True)
    print(f"DONE, enriched {done}")

if __name__ == "__main__":
    main()
