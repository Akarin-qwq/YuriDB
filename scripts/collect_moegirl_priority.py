#!/usr/bin/env python3
"""萌百采集·高价值优先版：按优先级索引抓（有原文名的动画/漫画/书籍），单线程稳速。"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
# 复用 collect_moegirl 的 fetch/parse
import importlib.util
spec = importlib.util.spec_from_file_location("cm", pathlib.Path(__file__).resolve().parent / "collect_moegirl.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

def main():
    ROOT = cm.ROOT
    lines = [json.loads(l) for l in open(ROOT / "data" / "corpus" / "works.jsonl", encoding="utf-8")]
    priority = json.load(open(ROOT / "data" / "raw" / "moegirl_high_priority.json"))
    hit = miss = 0
    for idx in priority:
        e = lines[idx]
        f = cm.OUT / (e["id"].replace(":", "_") + ".json")
        if f.exists():
            continue
        found = None
        for t in (e.get("title_original"), e.get("title")):
            if not t or len(t) < 3:
                continue
            try:
                found = cm.fetch(t)
            except Exception as ex:
                print(f"  err {e['id']}: {ex}", flush=True)
                time.sleep(8)
            if found:
                break
            time.sleep(1.2)
        if found:
            found["work_id"] = e["id"]
            f.write_text(json.dumps(found, ensure_ascii=False), encoding="utf-8")
            hit += 1
            if hit % 20 == 0:
                print(f"hit {hit} / miss {miss} (last {e['id']} {e['title'][:20]})", flush=True)
        else:
            miss += 1
            f.write_text(json.dumps({"work_id": e["id"], "miss": True}, ensure_ascii=False), encoding="utf-8")
        time.sleep(1.2)
    print(f"DONE hit={hit} miss={miss}")

import time
if __name__ == "__main__":
    main()
