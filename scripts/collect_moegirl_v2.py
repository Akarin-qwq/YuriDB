#!/usr/bin/env python3
"""萌百采集 v2：按 Bangumi 百合票数降序的优先队列（中文名搜索，命中率高）。"""
import json, sys, time, pathlib, importlib.util

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cm", HERE / "collect_moegirl.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

def main():
    ROOT = cm.ROOT
    by_id = {e["id"]: e for e in map(json.loads, open(ROOT / "data" / "corpus" / "works.jsonl", encoding="utf-8"))}
    queue = json.load(open(ROOT / "data" / "raw" / "moegirl_priority_v2.json", encoding="utf-8"))
    hit = miss = 0
    for wid in queue:
        e = by_id[wid]
        f = cm.OUT / (e["id"].replace(":", "_") + ".json")
        if f.exists():
            continue
        found = None
        # 搜索词：Bangumi 中文名（=萌百常用条目名）→ 原文名
        for t in (e.get("title"), e.get("title_original")):
            if not t or len(t) < 3:
                continue
            try:
                found = cm.fetch(t)
            except Exception as ex:
                print(f"  err {wid}: {ex}", flush=True)
                time.sleep(8)
            if found:
                break
            time.sleep(1.2)
        if found:
            found["work_id"] = wid
            f.write_text(json.dumps(found, ensure_ascii=False), encoding="utf-8")
            hit += 1
            if hit % 20 == 0:
                print(f"hit {hit} / miss {miss} (last {e['title'][:24]})", flush=True)
        else:
            miss += 1
            f.write_text(json.dumps({"work_id": wid, "miss": True}, ensure_ascii=False), encoding="utf-8")
    print(f"DONE hit={hit} miss={miss}")

if __name__ == "__main__":
    main()
