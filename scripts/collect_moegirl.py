#!/usr/bin/env python3
"""萌娘百科（moegirl.uk 镜像）角色/剧情富化：全部作品按标题匹配萌百条目。
断点续跑：命中结果存 data/raw/enrich_moegirl/<workid>.json
输出字段：moegirl_title, moegirl_url, moegirl_chars（名字+CV+描述）, moegirl_plot（剧情章节文本）"""
import json, re, time, urllib.request, urllib.parse, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "enrich_moegirl"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "yuri-corpus/0.1 (research; local)"}

HOSTS = ["https://moegirl.uk/api.php", "https://zh.moegirl.org.cn/api.php"]  # 镜像优先（主站时断时续）

def api(params, retries=4):
    qs = urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        host = HOSTS[i % len(HOSTS)]
        try:
            req = urllib.request.Request(f"{host}?{qs}", headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.load(r)
        except Exception as e:
            last = e; time.sleep(2 * (i + 1))
    raise last

def strip_wiki(s):
    if not s: return ""
    s = re.sub(r"\{\{黑幕\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\[\[([^|\]]*)\|([^\]]*)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{lang\|[^|]*\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"''+", "", s)
    s = re.sub(r"<del>.*?</del>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", s).strip()

def parse_sections(wikitext):
    """返回 (chars, plot)"""
    chars = None
    m = re.search(r"==+\s*(?:登场人物|主要角色|角色介绍|人物介绍|登场角色|角色简介)\s*==+", wikitext)
    if m:
        rest = wikitext[m.end():]
        m_end = re.search(r"\n==[^=\n]", rest)   # 下一个二级标题（含 === 以上都会被 ==[^=] 排除? 不：== 后跟== 的情况）
        if not m_end:
            m_end = re.search(r"\n=== [^=\n]", rest)
        seg = rest[:m_end.start()] if m_end else rest
        chars = []
        for b in re.split(r"\n(?=[;*])", seg):
            if not (b.startswith(";") or b.startswith("*")): continue
            lines = b.splitlines()
            first_line = lines[0].lstrip(";* ")
            nm = re.match(r"\s*\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", first_line)
            if nm:
                name = strip_wiki(nm.group(2) or nm.group(1))
            else:
                nm2 = re.match(r"\s*([^(（\n:{\[]{2,20})", first_line)
                if not nm2: continue
                name = strip_wiki(nm2.group(1))
            cvm = re.search(r"CV：(.+)", lines[0])
            cv = strip_wiki(cvm.group(1)) if cvm else ""
            desc = strip_wiki(" ".join(l.lstrip(":") for l in lines[1:] if not l.startswith(";")))
            desc = re.sub(r"CV：.*", "", desc).strip()
            desc = re.sub(r"====.*", "", desc).strip()
            if name and 1 < len(name) <= 25 and "Category" not in name:
                chars.append({"name": name, "cv": cv[:60], "description": desc[:400]})
        if not chars:
            # 表格/大字布局：'''[[名字]]''' + <br/> 描述
            for m in re.finditer(r"\'\'\'\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\'\'\'([\s\S]{0,700}?)(?=\|\-|\n\{|\Z)", seg):
                name = strip_wiki(m.group(2) or m.group(1))
                body = strip_wiki(m.group(3))
                cvm = re.search(r"CV[：:]([^\s].{0,60})", body)
                cv = strip_wiki(cvm.group(1)) if cvm else ""
                desc = body[:400]
                if name and 1 < len(name) <= 25:
                    chars.append({"name": name, "cv": cv, "description": desc})
        chars = chars or None
    # 剧情：=== 剧情简介 === / == 故事 ==等
    p = re.search(r"===+\s*(?:剧情简介|剧情介绍|故事简介|故事|剧情)\s*===+(.*?)(?=\n===|\Z)", wikitext, re.S)
    plot = strip_wiki(p.group(1))[:2500] if p else None
    return chars, plot

def fetch(title):
    d = api({"action": "query", "format": "json", "list": "search", "srsearch": title, "srlimit": 3})
    hit = None
    for h in d.get("query", {}).get("search", []):
        if title[:4] in h["title"]:
            hit = h["title"]; break
    if not hit:
        return None
    d2 = api({"action": "query", "format": "json", "prop": "revisions", "rvprop": "content",
              "rvslots": "main", "redirects": 1, "titles": hit})
    for pid, p in d2["query"]["pages"].items():
        if pid != "-1" and p.get("revisions"):
            wt = p["revisions"][0]["slots"]["main"]["*"]
            if not any(k in wt[:3000] for k in ("Infobox", "Infobox", "{{Infobox")):
                return None
            chars, plot = parse_sections(wt)
            return {"moegirl_title": hit,
                    "moegirl_url": "https://zh.moegirl.org.cn/" + urllib.parse.quote(hit.replace(" ", "_")),
                    "moegirl_chars": chars, "moegirl_plot": plot}
    return None

def main(start=0, end=None):
    lines = [json.loads(l) for l in open(ROOT / "data" / "corpus" / "works.jsonl", encoding="utf-8")]
    todo = lines[start:end] if end else lines[start:]
    hit = miss = 0
    for e in todo:
        f = OUT / (e["id"].replace(":", "_") + ".json")
        if f.exists():
            continue
        found = None
        for t in (e.get("title_original"), e.get("title")):
            if not t or len(t) < 3:
                continue
            try:
                found = fetch(t)
            except Exception as ex:
                print(f"  err {e['id']}: {ex}", flush=True)
            if found:
                break
            time.sleep(0.8)
        if found:
            found["work_id"] = e["id"]
            f.write_text(json.dumps(found, ensure_ascii=False), encoding="utf-8")
            hit += 1
            if hit % 25 == 0:
                print(f"moegirl hit {hit} / miss {miss} (last {e['id']})", flush=True)
        else:
            miss += 1
            # miss 也记录，避免重复搜索
            f.write_text(json.dumps({"work_id": e["id"], "miss": True}, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.8)
    print(f"DONE hit={hit} miss={miss}")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0,
         int(sys.argv[2]) if len(sys.argv) > 2 else None)
