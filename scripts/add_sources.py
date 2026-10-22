#!/usr/bin/env python3
"""把 vndb_yuri_only_vn 和 bangumi_* 并入 build_corpus 的输出，追加进 works.jsonl（按 id 去重）。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"

def clean_text(s, limit=1200):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

def vndb_only():
    out = []
    for v in json.load(open(RAW / "vndb_yuri_only_vn.json", encoding="utf-8")):
        tags = sorted({t["name"] for t in v.get("tags", [])
                       if t.get("category") in ("cont","ero") and t.get("rating",0) >= 1.5})[:15]
        out.append({
            "id": f"vndb:{v['id']}", "source": "vndb", "media_type": "vn",
            "title": v.get("title") or "", "title_original": v.get("alttitle") or "", "title_en": "",
            "year": int(v["released"][:4]) if v.get("released") else None,
            "score": (v.get("rating") or 0)/10 or None, "popularity": None, "votes": v.get("votecount"),
            "tags": tags + ["纯百合(GxG Only)"],
            "description": clean_text(v.get("description") or ""),
            "urls": [f"https://vndb.org/{v['id']}"],
        })
    return [e for e in out if e["title"]]

BGM_TYPE = {1: "book", 2: "anime", 4: "game"}

def bangumi():
    out = []
    for stype, media in BGM_TYPE.items():
        p = RAW / f"bangumi_yuri_{media}.json"
        if not p.exists(): continue
        for s in json.load(open(p, encoding="utf-8")):
            if not s.get("name"): continue
            url = s.get("url") or f"https://bgm.tv/subject/{s['id']}"
            out.append({
                "id": f"bangumi:{s['id']}", "source": "bangumi", "media_type": media,
                "title": s.get("name_cn") or s["name"], "title_original": s["name"], "title_en": "",
                "year": int(s["date"][:4]) if s.get("date") else None,
                "score": s.get("rating", {}).get("score") if isinstance(s.get("rating"), dict) else None,
                "popularity": s.get("rating", {}).get("total") if isinstance(s.get("rating"), dict) else None,
                "votes": None,
                "tags": [s.get("platform") or media, "百合"],
                "description": clean_text(s.get("summary") or ""),
                "urls": [url],
            })
    return out

def main():
    lines = open(CORPUS / "works.jsonl", encoding="utf-8").read().splitlines()
    seen = {json.loads(l)["id"] for l in lines}
    added = 0
    with open(CORPUS / "works.jsonl", "a", encoding="utf-8") as f:
        for e in vndb_only() + bangumi():
            if e["id"] in seen: continue
            seen.add(e["id"])
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
            added += 1
    stats = json.load(open(CORPUS / "stats.json", encoding="utf-8"))
    stats["total"] = len(seen)
    by = stats["by_media_type"]
    for e in [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]:
        pass
    by_media = {}
    for l in open(CORPUS / "works.jsonl", encoding="utf-8"):
        m = json.loads(l)["media_type"]
        by_media[m] = by_media.get(m, 0) + 1
    stats["by_media_type"] = by_media
    stats["sources"] = sorted({"vndb","anilist","yuri-archive","bangumi"})
    (CORPUS / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added {added}, corpus now {stats['total']} works")

if __name__ == "__main__":
    main()
