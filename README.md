# yuri-corpus — 百合作品语料库

为 LLM（百合游戏制作）收集的百合作品数据库，覆盖 galgame、动漫、漫画、轻小说等。

## 数据源

| 源 | 覆盖 | 数量（当前） | 说明 |
|---|---|---|---|
| VNDB (api.vndb.org/kana) | galgame/ VN | 400 | tag `g97 Girl x Girl Romance`，按投票数取头部 |
| AniList (graphql.anilist.co) | 动漫/漫画/轻小说 | 400 + 400 + 179 | Yuri tag，按热度取头部 |
| L-M-Sherlock/yuri-classification-archive | 全媒介 | 823 | 社区维护的女女关系分类档案，含 Bangumi rank/百合标签比例 |

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
  "id": "vndb:v12345 | anilist:12345 | yuri-archive:slug",
  "source": "vndb | anilist | yuri-archive",
  "media_type": "vn | anime | manga | light_novel | archive_*",
  "title": "主标题", "title_original": "原文名", "title_en": "英文名",
  "year": 2020, "score": 8.1, "popularity": 12345, "votes": 678,
  "tags": ["..."], "description": "简介（去 HTML，截 1200 字）",
  "urls": ["来源页"]
}
```

## 重新构建

```sh
python scripts/collect_vndb.py 400
python scripts/collect_anilist.py 400
python scripts/build_corpus.py
```

持续任务：老大说停之前持续扩充（计划：VNDB g1986 "Romance Only" 补全、Bangumi 百合 tag 432 条、更多来源）。
