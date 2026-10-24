#!/usr/bin/env python3
"""采集 CnGal 百合题材（GL）标签下全部条目详情。
断点续跑：每条存 data/raw/cngal/<id>.json"""
import json, time, urllib.request, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "cngal"
OUT.mkdir(parents=True, exist_ok=True)
HDRS = {"User-Agent": "yuri-corpus/0.1 (local research)"}

def get(url, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as e:
            last = e; time.sleep(3 * (i + 1))
    raise last

def main():
    entries = json.load(open(ROOT / "data" / "raw" / "cngal_yuri_entries.json", encoding="utf-8"))
    done = 0
    for e in entries:
        f = OUT / f"{e['id']}.json"
        if f.exists():
            continue
        try:
            d = get(f"https://api.cngal.org/api/entries/GetEntryView/{e['id']}")
            f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            done += 1
            time.sleep(0.8)
        except Exception as ex:
            print(f"FAIL {e['id']} {e['name']}: {ex}", flush=True)
            time.sleep(5)
    print(f"DONE, newly fetched {done}")

if __name__ == "__main__":
    main()
