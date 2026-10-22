# yuri-corpus — 百合作品语料库

为 LLM（百合游戏制作）收集的百合作品数据库，覆盖 galgame、动漫、漫画、轻小说等。

## 数据源

| 源 | 覆盖 | 数量（当前） | 说明 |
|---|---|---|---|
| VNDB (api.vndb.org/kana) | galgame / VN | 2440 | tag `g97 Girl x Girl Romance`（全量）+ `g1986 Romance Only` |
| AniList (graphql.anilist.co) | 动漫 / 漫画 / 轻小说 | 877 + 2000 + 179 | Yuri tag 全量，带角色表 |
| L-M-Sherlock/yuri-classification-archive | 全媒介 | 823 | 社区维护的女女关系分类档案，含 Bangumi rank/百合标签比例 |
| Bangumi (api.bgm.tv) | 书 / 动画 / 游戏 | 117 | 中文译名 + 简介 + 角色表 |
| 中文维基百科 (API) | 动漫 / 漫画 | 增长中 | 中文摘要与剧情段落（`wiki_extract`） |

## 结构

```
scripts/           采集与构建脚本（probe / collect_vndb / collect_anilist / build_corpus）
data/raw/          各源原始抓取结果（json）
data/corpus/
  works.jsonl      统一语料库（每行一个作品）
  stats.json       构建统计（总数/去重/验证错误）
```

## 统一 schema（works.jsonl 每行）

```json
{
  "id": "vndb:v12345 | anilist:12345 | bangumi:12345 | yuri-archive:slug",
  "source": "vndb | anilist | bangumi | yuri-archive",
  "media_type": "vn | anime | manga | light_novel | book | game | archive_*",
  "title": "主标题", "title_original": "原文名", "title_en": "英文名",
  "year": 2020, "score": 8.1, "popularity": 12345, "votes": 678,
  "tags": ["..."], "description": "简介（去 HTML）", "urls": ["来源页"],

  "characters": [
    {"name": "角色名", "original": "原文名",
     "role": "main|primary|side|appears (VNDB) / MAIN|SUPPORTING (AniList)",
     "description": "角色描述",
     "position": "主线|副线 (仅 yuri-archive)", "explicitness": "恋爱|非恋爱", "mutuality": "双向|单向"}
  ],

  "ending_tags": ["Bad Ending(s)", "Only Good Endings", "Multiple Endings"],
  "plot_tags": ["All-girls School", "Assassin Heroine"],
  "full_description": "VNDB 完整故事简介（未截断）",
  "wiki_extract": "中文维基摘要+剧情（≤6000 字）", "wiki_url": "...",
  "format": "TV|MANGA|NOVEL", "episodes": 12, "chapters": 50
}
```

## 已知边界

- **结局（BE/HE/TE）来自 VNDB tag 体系**（`Bad Ending(s)` / `Only Good Endings` / `Multiple Endings` / `Death of Heroine` 等），是社区标注而非官方结局清单；动漫/漫画的剧情走向看 `wiki_extract`。
- Bangumi 匿名 API 有限额（搜索每类约 50 条，部分条目 404 失效），中文译名覆盖不完整。
- 萌娘百科直连/镜像当前不可达（SSL 握手超时、镜像 500），中文剧情暂以中文维基为主。
- `characters` 描述可能含剧透（源站如此），使用时注意。

## 重新构建

```sh
python scripts/collect_vndb_full.py both     # VNDB g97+g1986 全量
python scripts/collect_anilist_deep.py       # AniList 动漫/漫画全量（带角色）
python scripts/enrich_vndb.py                # 每部 VN 角色表（断点续跑）
python scripts/enrich_bangumi.py             # Bangumi 角色表
python scripts/enrich_wikipedia.py 500       # 中文维基摘要
python scripts/build_corpus.py               # 重建主语料
python scripts/add_vndb_full.py              # 并入 VNDB 全量分片
python scripts/add_anilist_deep.py           # 并入 AniList 深挖
python scripts/merge_enriched.py             # 合并角色/结局/剧情档案
python scripts/merge_extras.py               # 合并 Bangumi 详情与中文维基
```

持续任务：老大说停之前持续扩充。待做：Bangumi 登录后突破限额、萌百反爬绕行、MAL 补充。
