#!/usr/bin/env python3
"""并入 AniList 深挖文件（各 2000 部，带角色表）：新增记录 + 已有记录补/升级角色档案。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"

def clean(s, limit=900):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

def to_entry(m, media):
    t = m.get("title") or {}
    tags = [x["name"] for x in (m.get("tags") or []) if not x.get("isGeneralSpoiler") and (x.get("rank") or 0) >= 60]
    chars = []
    for e in (m.get("characters") or {}).get("edges") or []:
        n = e.get("node") or {}
        chars.append({"name": (n.get("name") or {}).get("full"),
                      "original": (n.get("name") or {}).get("native") or "",
                      "role": e.get("role"), "description": clean((n or {}).get("description"))})
    return {
        "id": f"anilist:{m['id']}", "source": "anilist", "media_type": media,
        "title": t.get("romaji") or t.get("native") or "", "title_original": t.get("native") or "",
        "title_en": t.get("english") or "",
        "year": (m.get("startDate") or {}).get("year"), "score": m.get("averageScore"),
        "popularity": m.get("popularity"), "votes": m.get("favourites"),
        "tags": sorted(set(tags + (m.get("genres") or [])))[:15],
        "description": clean(m.get("description") or "", 1200),
        "urls": [m.get("siteUrl") or f"https://anilist.co/{'anime' if media=='anime' else 'manga'}/{m['id']}"],
        "characters": [c for c in chars if c["name"]],
        "format": m.get("format"), "episodes": m.get("episodes"), "chapters": m.get("chapters"),
    }

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    by_id = {e["id"]: e for e in lines}
    added = upgraded = 0
    for fname, media in [("anilist_yuri_anime_deep.json", "anime"), ("anilist_yuri_manga_deep.json", "manga")]:
        p = RAW / fname
        if not p.exists():
            print(f"missing {fname}"); continue
        for m in json.load(open(p, encoding="utf-8")):
            e = to_entry(m, media)
            cur = by_id.get(e["id"])
            if cur is None:
                lines.append(e); by_id[e["id"]] = e; added += 1
            elif len(e.get("characters") or []) > len(cur.get("characters") or []):
                if not cur.get("description"): cur["description"] = e["description"]
                cur["characters"] = e["characters"]
                cur["format"] = e.get("format"); cur["episodes"] = e.get("episodes"); cur["chapters"] = e.get("chapters")
                upgraded += 1
    with open(CORPUS / "works.jsonl", "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"anilist deep: added {added}, upgraded {upgraded}, total {len(lines)}")

if __name__ == "__main__":
    main()
