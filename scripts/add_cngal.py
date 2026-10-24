#!/usr/bin/env python3
"""CnGal 112 部国产百合游戏并入 works.jsonl（id: cngal:<id>）。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"

def clean_html(s, limit=2500):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    seen = {e["id"] for e in lines}
    added = 0
    out_entries = []
    for f in sorted((RAW / "cngal").glob("*.json")):
        d = json.load(open(f, encoding="utf-8"))
        eid = f"cngal:{d['id']}"
        if eid in seen:
            continue
        seen.add(eid)
        roles = [{"name": r.get("name"), "original": r.get("anotherName") or "",
                  "role": r.get("roleIdentity") or "角色", "cv": r.get("cv") or "",
                  "description": re.sub(r"\s+", " ", r.get("briefIntroduction") or "")[:400]}
                 for r in (d.get("roles") or []) if r.get("name")]
        groups = [r.get("name") for r in (d.get("entryRelevances") or []) if r.get("type") == "ProductionGroup"]
        tags = sorted({t.get("name") for t in (d.get("tags") or []) if t.get("name")})
        out_entries.append({
            "id": eid, "source": "cngal", "media_type": "cn_galgame",
            "title": d.get("name") or "", "title_original": d.get("anotherName") or "",
            "title_en": "",
            "year": d.get("publishTime") and int(str(d["publishTime"])[:4]) or None,
            "score": None, "popularity": None, "votes": None,
            "tags": tags,
            "description": clean_html(d.get("briefIntroduction"), 600),
            "urls": [f"https://www.cngal.org/entries/index/{d['id']}"],
            "main_page": clean_html(d.get("mainPage"), 2500),  # 详细剧情介绍（长文）
            "characters": roles,
            "production_groups": groups,
        })
    with open(CORPUS / "works.jsonl", "a", encoding="utf-8") as f:
        for e in out_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"added {len(out_entries)}; corpus now {len(lines) + len(out_entries)}")

if __name__ == "__main__":
    main()
