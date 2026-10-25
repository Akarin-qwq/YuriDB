#!/usr/bin/env python3
"""把萌百角色/剧情并入 works.jsonl（只补空缺，不覆盖已有档案）。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "enrich_moegirl"
CORPUS = ROOT / "data" / "corpus"
GROUP_KW = ("家", "居民", "学生会", "其他人物", "结局角色", "其他角色", "组", "会", "社")

def main():
    lines = [json.loads(l) for l in open(CORPUS / "works.jsonl", encoding="utf-8")]
    by_id = {e["id"]: e for e in lines}
    merged_c = merged_p = 0
    for f in OUT.glob("*.json"):
        d = json.load(open(f, encoding="utf-8"))
        if d.get("miss"):
            continue
        e = by_id.get(d["work_id"])
        if not e:
            continue
        chars = [c for c in (d.get("moegirl_chars") or [])
                 if c.get("name") and not any(c["name"].endswith(k) and len(c["name"]) <= 5 for k in ("家","会","社","组"))]
        if chars and not e.get("characters"):
            e["characters"] = [{"name": c["name"], "original": "", "role": None,
                                "cv": c.get("cv") or "", "description": c.get("description") or ""}
                               for c in chars]
            e["characters_source"] = "moegirl"
            merged_c += 1
        if d.get("moegirl_plot") and not e.get("wiki_extract"):
            e["moegirl_plot"] = d["moegirl_plot"]
            merged_p += 1
        if d.get("moegirl_title"):
            e["moegirl_url"] = d["moegirl_url"]
    with open(CORPUS / "works.jsonl", "w", encoding="utf-8") as f:
        for e in lines:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"moegirl: 角色档案并入 {merged_c} 部, 剧情并入 {merged_p} 部")

if __name__ == "__main__":
    main()
