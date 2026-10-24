#!/usr/bin/env python3
"""把 Bangumi 全量 dump 的 7839 条并入 works.jsonl：新条目追加；已有 bangumi: 条目升级（带全量 tags/角色/中文摘要）。"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
SRC = ROOT / "data" / "raw" / "bgm_archive" / "enriched.jsonl"

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    by_id = {e["id"]: e for e in lines}
    added = upgraded = 0
    for e in map(json.loads, open(SRC, encoding="utf-8")):
        cur = by_id.get(e["id"])
        if cur is None:
            lines.append(e); by_id[e["id"]] = e; added += 1
        else:
            # 升级：中文名/摘要/角色/票数 补强
            cur["title"] = cur.get("title") or e["title"]
            if not cur.get("description") and e.get("description"):
                cur["description"] = e["description"]
            if len(e.get("characters") or []) > len(cur.get("characters") or []):
                cur["characters"] = e["characters"]
            cur["yuri_tag_votes"] = e.get("yuri_tag_votes")
            if e.get("rank"): cur["rank"] = e["rank"]
            upgraded += 1
    with open(CORPUS / "works.jsonl", "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"added {added}, upgraded {upgraded}, total {len(lines)}")

if __name__ == "__main__":
    main()
