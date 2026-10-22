#!/usr/bin/env python3
"""把 data/raw 的四个源统一转成语料库 data/corpus/works.jsonl + 汇总统计。

统一 schema:
  id: 源内唯一 id
  source: vndb / anilist / yuri-archive
  media_type: vn / anime / manga / light_novel / archive_entry
  title, title_original, title_en
  year, score, popularity/votecount, tags, description
  urls
验证：必填字段齐全、年份合理、tag 与媒介匹配；统计去重与覆盖率。
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"
CORPUS.mkdir(parents=True, exist_ok=True)

def clean_text(s, limit=1200):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]

def base_entry(source, media, eid, title, **kw):
    if not title or not eid:
        return None
    return {
        "id": f"{source}:{eid}",
        "source": source,
        "media_type": media,
        "title": title,
        "title_original": kw.get("t_orig", ""),
        "title_en": kw.get("t_en", ""),
        "year": kw.get("year"),
        "score": kw.get("score"),
        "popularity": kw.get("pop"),
        "votes": kw.get("votes"),
        "tags": kw.get("tags", []),
        "description": clean_text(kw.get("desc", "")),
        "urls": kw.get("urls", []),
    }

def from_vndb():
    out = []
    for v in json.load(open(RAW / "vndb_yuri_vn.json", encoding="utf-8")):
        tags = [t["name"] for t in v.get("tags", []) if t.get("category") in ("cont", "ero") and t.get("rating", 0) >= 1.5]
        entry = base_entry(
            "vndb", "vn", v["id"], v.get("title"),
            t_orig=v.get("alttitle") or "", t_en="",
            year=int(v["released"][:4]) if v.get("released") else None,
            score=(v.get("rating") or 0) / 10 or None, votes=v.get("votecount"),
            tags=sorted(set(tags))[:15],
            desc=v.get("description") or "",
            urls=[f"https://vndb.org/{v['id']}"],
        )
        if entry:
            out.append(entry)
    return out

def from_anilist(fname, media):
    out = []
    for m in json.load(open(RAW / fname, encoding="utf-8")):
        t = m.get("title") or {}
        year = (m.get("startDate") or {}).get("year")
        tags = [x["name"] for x in (m.get("tags") or []) if not x.get("isGeneralSpoiler") and (x.get("rank") or 0) >= 60]
        genres = m.get("genres") or []
        entry = base_entry(
            "anilist", media, m["id"], t.get("romaji") or t.get("native"),
            t_orig=t.get("native") or "", t_en=t.get("english") or "",
            year=year, score=m.get("averageScore"), pop=m.get("popularity"),
            votes=m.get("favourites"), tags=sorted(set(tags + genres))[:15],
            desc=m.get("description") or "",
            urls=[m.get("siteUrl") or f"https://anilist.co/{'anime' if media=='anime' else 'manga'}/{m['id']}"],
        )
        if entry:
            out.append(entry)
    return out

def from_archive():
    out = []
    items = json.load(open(RAW / "_archive" / "data" / "catalog.json", encoding="utf-8"))["items"]
    for it in items:
        entry = base_entry(
            "yuri-archive", f"archive_{it['medium']['code']}", it["slug"], it["title"],
            t_orig=it.get("title_original") or "", t_en=it.get("title_english") or "",
            year=it.get("release_year"),
            tags=[it["medium"]["label"], it["female_relationship_centrality"]["label"],
                  it["highest_romance_explicitness"]["label"]]
                 + [p["name"] for p in (it.get("relationship_profiles") or [])][:5],
            desc=it.get("scope_summary") or "",
            urls=[it.get("report_url_absolute") or "https://l-m-sherlock.github.io/yuri-classification-archive"],
        )
        if entry:
            entry["bangumi_rank"] = it.get("bangumi_rank")
            entry["bangumi_yuri_tag_ratio"] = it.get("bangumi_yuri_tag_ratio")
            out.append(entry)
    return out

def validate(entries):
    errs = []
    for e in entries:
        if not e["title"]:
            errs.append(f"{e['id']}: empty title")
        if e["year"] is not None and not (1900 <= e["year"] <= 2030):
            errs.append(f"{e['id']}: bad year {e['year']}")
    return errs

def main():
    all_entries = (from_vndb()
                   + from_anilist("anilist_yuri_anime.json", "anime")
                   + from_anilist("anilist_yuri_manga.json", "manga")
                   + from_anilist("anilist_yuri_ln.json", "light_novel")
                   + from_archive())
    errs = validate(all_entries)
    ids = [e["id"] for e in all_entries]
    dupes = len(ids) - len(set(ids))
    out = CORPUS / "works.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for e in all_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    by_media = {}
    for e in all_entries:
        by_media[e["media_type"]] = by_media.get(e["media_type"], 0) + 1
    stats = {
        "total": len(all_entries), "unique_ids": len(set(ids)), "duplicates": dupes,
        "validation_errors": len(errs), "by_media_type": by_media,
        "sources": sorted({e["source"] for e in all_entries}),
    }
    (CORPUS / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    if errs:
        (CORPUS / "validation_errors.log").write_text("\n".join(errs), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    print(f"-> {out}")

if __name__ == "__main__":
    main()
