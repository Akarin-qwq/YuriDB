#!/usr/bin/env python3
"""并入 Bangumi 详情描述 + 中文维基摘要/剧情 到 works.jsonl。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"

def clean(s, limit=3000):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    by_id = {e["id"]: e for e in lines}
    bgm_desc = wiki = 0
    for f in (RAW / "enrich_bangumi_detail").glob("*.json"):
        d = json.load(open(f, encoding="utf-8"))
        e = by_id.get(f"bangumi:{f.stem}")
        if e and d.get("summary"):
            e["description"] = clean(d["summary"]) if not e.get("description") else e["description"]
            e["summary"] = clean(d["summary"])
            infobox = d.get("infobox") or []
            e["infobox"] = [{"key": i.get("key"), "value": i.get("value")} for i in infobox[:12]]
            bgm_desc += 1
    for f in (RAW / "enrich_wiki").glob("*.json"):
        d = json.load(open(f, encoding="utf-8"))
        e = by_id.get(f"anilist:{d['anilist_id']}")
        if e:
            e["wiki_title"] = d.get("wiki_title")
            e["wiki_url"] = d.get("url")
            e["wiki_extract"] = clean(d.get("extract"), 6000)
            if not e.get("description"):
                e["description"] = clean(d.get("extract"), 1200)
            wiki += 1
    with open(CORPUS / "works.jsonl", "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"bangumi descriptions merged: {bgm_desc}; wiki extracts merged: {wiki}; total {len(lines)}")

if __name__ == "__main__":
    main()
