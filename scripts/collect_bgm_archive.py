#!/usr/bin/env python3
"""从 Bangumi 官方全量 dump（bangumi/Archive）构建百合条目 + 角色档案。
输入: data/raw/bgm_archive/{subject,characters...}.jsonlines + yuri_ids.json
输出: data/raw/bgm_archive/enriched.jsonl（含中文角色档案）"""
import json, re, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARC = ROOT / "data" / "raw" / "bgm_archive"
TYPE_MAP = {1: "book", 2: "anime", 4: "game"}

def parse_infobox(s):
    """从 wiki infobox 提取顶层 key=value（多行块只取第一行）。"""
    out = {}
    for line in s.splitlines():
        m = re.match(r"\s*\|\s*([^=|]+?)\s*=\s*(.+)", line)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if k not in out:
                out[k] = v
    return out

def main():
    ids = json.load(open(ARC / "yuri_ids.json", encoding="utf-8"))
    wanted = {}
    for typ, items in ids.items():
        if int(typ) in TYPE_MAP:
            for sid, name, count, score in items:
                wanted[int(sid)] = {"count": count, "score": score}
    print(f"目标条目: {len(wanted)}")

    # 1) subject 详情
    subjects = {}
    with open(ARC / "subject.jsonlines", encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            if s["id"] in wanted:
                subjects[s["id"]] = s
    print(f"subject 详情: {len(subjects)}")

    # 2) subject -> character 关联
    sc_map = {}
    with open(ARC / "subject-characters.jsonlines", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["subject_id"] in wanted:
                sc_map.setdefault(r["subject_id"], []).append((r["character_id"], r.get("type")))
    need_chars = {cid for lst in sc_map.values() for cid, _ in lst}
    print(f"涉及角色: {len(need_chars)}")

    # 3) 角色档案
    chars = {}
    t0 = time.time()
    with open(ARC / "character.jsonlines", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["id"] in need_chars:
                info = parse_infobox(c.get("infobox") or "")
                chars[c["id"]] = {
                    "name": c.get("name"), "original": info.get("简体中文名", ""),
                    "gender": info.get("性别", ""),
                    "summary": re.sub(r"\s+", " ", c.get("summary") or "")[:500],
                }
    print(f"角色档案: {len(chars)} ({time.time()-t0:.0f}s)")

    # 4) 组装
    out = ARC / "enriched.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as w:
        for sid, s in subjects.items():
            typ = TYPE_MAP[s["type"]]
            tags = sorted({t["name"] for t in (s.get("tags") or []) if t["count"] >= 5},
                          key=lambda t: -next(x["count"] for x in s["tags"] if x["name"] == t))[:12]
            chr_list = [{"id": f"bangumi:c{cid}", "role": {1: "主角", 2: "配角", 3: "客串"}.get(ct),
                         **chars.get(cid, {})} for cid, ct in sc_map.get(sid, [])]
            chr_list = [c for c in chr_list if c.get("name")]
            info = parse_infobox(s.get("infobox") or "")
            w.write(json.dumps({
                "id": f"bangumi:{sid}", "source": "bangumi", "media_type": typ,
                "title": s.get("name_cn") or s["name"], "title_original": s["name"],
                "title_en": info.get("别名", info.get("英文名", ""))[:100],
                "year": int(s["date"][:4]) if s.get("date") else None,
                "score": s.get("score"), "rank": s.get("rank"),
                "votes": (s.get("score_details") or {}).get("total"),
                "platform": info.get("平台", ""),
                "tags": (tags if "百合" in tags else tags + ["百合"])[:12],
                "description": re.sub(r"\s+", " ", s.get("summary") or "")[:1500],
                "urls": [f"https://bgm.tv/subject/{sid}"],
                "yuri_tag_votes": wanted[sid]["count"],
                "characters": chr_list,
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"写入 {n} -> {out}")

if __name__ == "__main__":
    main()
