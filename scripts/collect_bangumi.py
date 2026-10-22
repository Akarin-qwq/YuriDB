#!/usr/bin/env python3
"""采集 Bangumi 百合搜索（旧版 GET 接口，匿名可用，max_results=25/页）。
type: 1=书籍(轻小说/漫画) 2=动画 4=游戏。"""
import json, sys, time, urllib.request, urllib.parse, pathlib

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"

def get(url, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "yuri-corpus/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e
            print(f"  retry {i+1}/{retries}: {e}")
            time.sleep(3 * (i + 1))
    raise last

def main(limit=800):
    kw = urllib.parse.quote("百合")
    for stype, fname in [(1, "bangumi_yuri_book.json"), (2, "bangumi_yuri_anime.json"), (4, "bangumi_yuri_game.json")]:
        out = RAW / fname
        if out.exists():
            print(f"skip {fname} (exists)")
            continue
        items, start = [], 0
        while start < limit:
            d = get(f"https://api.bgm.tv/search/subject/{kw}?type={stype}&max_results=25&start={start}")
            batch = d.get("list", [])
            items.extend(batch)
            print(f"{fname} start {start}: +{len(batch)} (total {len(items)}, api_results={d.get('results')})")
            if len(batch) < 25:
                break
            start += 25
            time.sleep(1.0)
        out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"saved {len(items)} -> {out}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 800)
