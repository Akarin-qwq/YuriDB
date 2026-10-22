#!/usr/bin/env python3
"""把富化数据（VNDB 角色表+完整tag、AniList 角色表、Bangumi 角色）并入 works.jsonl。
每条记录新增：characters[]、ending_tags[]、plot_tags[]（结局/剧情拆分）、full_description。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"

def clean(s, limit=900):
    if not s: return ""
    s = re.sub(r"\[url=[^\]]*\]", "", s)
    s = re.sub(r"\[/\w+\]", "", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

ENDING_KW = ("bad ending", "good ending", "true ending", "normal ending", "ending",
             "death of heroine", "death of protagonist", "multiple endings", "branching plot")

def vndb_enrich():
    out = {}
    for f in (RAW / "enrich_vndb").glob("*.json"):
        d = json.load(open(f, encoding="utf-8"))
        vnid = f.stem
        chars = [{"name": c["name"], "original": c.get("original") or "",
                  "role": c.get("_role"), "description": clean(c.get("description"))}
                 for c in d.get("characters", []) if c.get("name")]
        tags = d["vn"].get("tags") or []
        ending, plot = [], []
        for t in tags:
            n = t["name"]
            if any(k in n.lower() for k in ENDING_KW) or "death of" in n.lower():
                ending.append(n)  # 结局 tag 可能是 cont/tech 任意类
            elif t.get("category") == "cont" and t.get("spoiler", 0) < 2:
                plot.append(n)
        out[f"vndb:{vnid}"] = {
            "characters": chars,
            "ending_tags": sorted(set(ending)),
            "plot_tags": sorted(set(plot))[:20],
            "full_description": clean(d["vn"].get("description")),
        }
    return out

def anilist_enrich():
    out = {}
    for fname, media in [("anilist_yuri_anime_v2.json", "anime"), ("anilist_yuri_manga_v2.json", "manga")]:
        p = RAW / fname
        if not p.exists(): continue
        for m in json.load(open(p, encoding="utf-8")):
            chars = []
            for e in (m.get("characters") or {}).get("edges") or []:
                n = e.get("node") or {}
                chars.append({"name": (n.get("name") or {}).get("full"),
                              "original": (n.get("name") or {}).get("native") or "",
                              "role": e.get("role"), "description": clean((n or {}).get("description"))})
            out[f"anilist:{m['id']}"] = {"characters": [c for c in chars if c["name"]]}
    return out

def bangumi_enrich():
    out = {}
    for f in (RAW / "enrich_bangumi").glob("*.json"):
        d = json.load(open(f, encoding="utf-8"))
        chars = [{"name": c.get("name"), "original": c.get("original") or "",
                  "role": c.get("type"), "description": clean(c.get("summary"))}
                 for c in d.get("characters") or [] if c.get("name")]
        if chars:
            out[f"bangumi:{d['subject']}"] = {"characters": chars}
    return out

def archive_enrich():
    out = {}
    items = json.load(open(RAW / "_archive" / "data" / "catalog.json", encoding="utf-8"))["items"]
    for it in items:
        profiles = []
        for p in (it.get("relationship_profiles") or []):
            profiles.append({
                "name": p.get("name"),
                "position": (p.get("position") or {}).get("label"),
                "explicitness": (p.get("explicitness") or {}).get("label"),
                "mutuality": (p.get("mutuality") or {}).get("label"),
            })
        if profiles:
            out[f"yuri-archive:{it['slug']}"] = {
                "characters": profiles,  # 关系组档案：定位/明确度/单向双向
            }
    return out

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    enrich = {}
    for src in (vndb_enrich(), anilist_enrich(), bangumi_enrich(), archive_enrich()):
        enrich.update(src)
    hit = 0
    for e in lines:
        extra = enrich.get(e["id"])
        if extra:
            e.update(extra)
            hit += 1
        if not e.get("description") and e.get("full_description"):
            e["description"] = e["full_description"]  # 回填第一批漏抓的 VNDB 描述
    with open(CORPUS / "works.jsonl", "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with_char = sum(1 for e in lines if e.get("characters"))
    print(f"enriched {hit}/{len(lines)} records; {with_char} records now have character profiles")

if __name__ == "__main__":
    main()
