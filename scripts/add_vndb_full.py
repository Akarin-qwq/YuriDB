#!/usr/bin/env python3
"""把 vndb_full 分片里的全部 VN 并入 works.jsonl（按 id 去重），并输出未富化 id 清单。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, CORPUS = ROOT / "data" / "raw", ROOT / "data" / "corpus"

def clean(s, limit=2500):
    if not s: return ""
    s = re.sub(r"\[url=[^\]]*\]", "", s)
    s = re.sub(r"\[/\w+\]", "", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    seen = {e["id"] for e in lines}
    added = 0
    for f in sorted((RAW / "vndb_full").glob("*.json")):
        for v in json.load(open(f, encoding="utf-8"))["results"]:
            eid = f"vndb:{v['id']}"
            if eid in seen: continue
            seen.add(eid)
            tags = sorted({t["name"] for t in v.get("tags", [])
                           if t.get("category") in ("cont","ero") and t.get("rating",0) >= 1.5})[:15]
            lines.append({
                "id": eid, "source": "vndb", "media_type": "vn",
                "title": v.get("title") or "", "title_original": v.get("alttitle") or "", "title_en": "",
                "year": int(v["released"][:4]) if v.get("released") else None,
                "score": (v.get("rating") or 0)/10 or None, "popularity": None, "votes": v.get("votecount"),
                "tags": tags, "description": clean(v.get("description") or ""),
                "urls": [f"https://vndb.org/{v['id']}"],
            })
            added += 1
    with open(CORPUS / "works.jsonl", "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    # 待富化清单
    enriched = {p.stem for p in (RAW / "enrich_vndb").glob("*.json")}
    todo = [e["id"].split(":",1)[1] for e in lines if e["source"] == "vndb" and e["id"].split(":",1)[1] not in enriched]
    (RAW / "vndb_todo_ids.txt").write_text("\n".join(sorted(todo)), encoding="utf-8")
    print(f"added {added} new VN; corpus {len(lines)}; to enrich {len(todo)}")

if __name__ == "__main__":
    main()
