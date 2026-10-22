#!/usr/bin/env python3
"""中文维基富化 v2：generator=search 一次请求拿摘要，429 退避重试。"""
import json, time, urllib.request, urllib.parse, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = RAW / "enrich_wiki"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "yuri-corpus/0.1 (research; local)"}

def api(params, retries=5):
    url = "https://zh.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            wait = 6 * (i + 1) if e.code == 429 else 2 * (i + 1)
            time.sleep(wait)
        except Exception as e:
            last = e; time.sleep(2 * (i + 1))
    raise last

def lookup(title):
    d = api({"action": "query", "format": "json", "generator": "search",
             "gsrsearch": title, "gsrlimit": 1, "prop": "extracts",
             "explaintext": 1, "redirects": 1})
    pages = (d.get("query") or {}).get("pages") or {}
    for pid, p in pages.items():
        if pid != "-1" and p.get("extract"):
            return {"wiki_title": p["title"],
                    "url": "https://zh.wikipedia.org/wiki/" + urllib.parse.quote(p["title"]),
                    "extract": p["extract"][:6000]}
    return None

def main(limit=400):
    done = 0
    for fname in ("anilist_yuri_anime.json", "anilist_yuri_manga.json"):
        items = json.load(open(RAW / fname, encoding="utf-8"))
        for m in items[:limit]:
            eid = m["id"]
            f = OUT / f"{eid}.json"
            if f.exists(): continue
            for t in [m.get("title", {}).get("native"), m.get("title", {}).get("romaji")]:
                if not t: continue
                try:
                    res = lookup(t)
                except Exception as ex:
                    print(f"  skip {eid}: {ex}", flush=True); res = None
                if res:
                    res["anilist_id"] = eid
                    f.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
                    done += 1
                    if done % 20 == 0: print(f"wiki {done} (last {eid})", flush=True)
                    break
                time.sleep(1.2)
            time.sleep(1.0)
    print(f"DONE wiki {done}")

if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 400)
