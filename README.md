# YuriDB — 百合作品语料库

为 LLM（百合游戏向创作/分析）收集的百合作品数据库：**14270 部作品、49043 条角色档案**，覆盖 galgame、动画、漫画、轻小说、国产 galgame，全部统一为一个 JSONL，git 管理。

## 数据源

| 源 | 覆盖 | 数量 | 说明 |
|---|---|---|---|
| [VNDB](https://api.vndb.org/kana) | galgame / VN | 2440 | tag `g97 Girl x Girl Romance` **全量** + `g1986 Romance Only`；角色表（main/primary/side/appears）+ 完整 tag 体系 |
| [AniList](https://graphql.anilist.co) | 动画 / 漫画 / 轻小说 | 877 + 2000 + 179 | Yuri tag 全量（按热度），带 15 人主演角色表 |
| [Bangumi 官方 Archive](https://github.com/bangumi/Archive) | 书 / 动画 / 游戏 | 7893 | **百合 tag 全量**（书籍 5461 / 动画 1127 / 游戏 1251），中文名+简介+中文角色档案+`yuri_tag_votes` 百合票数 |
| [CnGal](https://www.cngal.org) | 国产 galgame | 112 | 百合题材（GL）标签全量：中文名+剧情长文+角色档案（**含中文 CV**）+制作组 |
| [yuri-classification-archive](https://github.com/L-M-Sherlock/yuri-classification-archive) | 全媒介 | 823 | 社区维护的女女关系分类档案：主线/副线、恋爱明确度、单向/双向 |
| [中文维基百科](https://zh.wikipedia.org) | 动画 / 漫画 | 988 | 中文摘要+剧情段落（`wiki_extract`，≤6000 字） |

## 快速上手

```python
import json
works = [json.loads(l) for l in open("data/corpus/works.jsonl", encoding="utf-8")]

# 按百合浓度排序的国产 galgame
cn = sorted((w for w in works if w["source"] == "cngal"), key=lambda w: len(w.get("characters") or []))

# 有 BE 标注的 galgame
be = [w for w in works if any("Bad Ending" in t for t in w.get("ending_tags", []))]

# 中文剧情资料齐全的动画
anime_cn = [w for w in works if w["media_type"] == "anime" and w.get("wiki_extract")]
```

## 统一 schema（works.jsonl 每行）

```jsonc
{
  "id": "vndb:v12345 | anilist:12345 | bangumi:12345 | cngal:24 | yuri-archive:slug",
  "source": "vndb | anilist | bangumi | cngal | yuri-archive",
  "media_type": "vn | anime | manga | light_novel | book | game | cn_galgame | archive_*",
  "title": "主标题（中文优先）", "title_original": "原文名", "title_en": "英文名",
  "year": 2020, "score": 8.1, "votes": 678, "rank": 123,
  "tags": ["百合", "..."], "description": "简介（去 HTML）", "urls": ["来源页"],

  "characters": [
    {
      "name": "角色名", "original": "中文名/原文名",
      "role": "main|primary|side|appears (VNDB) / 主角|配角|客串 (Bangumi) / MAIN|SUPPORTING (AniList)",
      "cv": "中文配音演员 (仅 CnGal)",
      "description": "角色描述",
      "position": "主线|副线", "explicitness": "恋爱|非恋爱", "mutuality": "双向|单向"
    }
  ],

  "ending_tags": ["Bad Ending(s)", "Only Good Endings", "Multiple Endings"],
  "plot_tags": ["All-girls School", "Assassin Heroine"],
  "full_description": "VNDB 完整故事简介（未截断）",
  "wiki_extract": "中文维基摘要+剧情段落", "wiki_url": "...",
  "yuri_tag_votes": 6081,
  "main_page": "CnGal 长文剧情介绍",
  "production_groups": ["白露社"],
  "format": "TV|MANGA|NOVEL", "episodes": 12, "chapters": 50
}
```

## 覆盖统计

| 维度 | 数量 |
|---|---|
| 作品总数 | 14270 |
| 含角色档案 | 5638 部 / 49043 条角色 |
| 结局 tag（BE/HE/TE/多结局） | 1056 部 galgame |
| 剧情走向 tag | 2440 部 galgame |
| 中文剧情资料（维基/CnGal/Bangumi） | ~10000 部 |
| 百合浓度票数（Bangumi） | 7839 部 |

按媒介：VN 2440 · 动画 2035 · 漫画 1946 · 书籍 5465 · 游戏 1270 · 国产 galgame 112 · 档案 823

## 目录结构

```
scripts/                     采集与构建脚本（全部断点续跑 + 重试）
data/raw/                    原始抓取缓存（不入 git，可重抓）
data/corpus/
  works.jsonl                统一语料库（每行一个作品）
  stats.json                 构建统计
```

## 已知边界

- **结局（BE/HE/TE）来自 VNDB tag 体系**（`Bad Ending(s)` / `Only Good Endings` / `Multiple Endings` / `Death of Heroine` 等），是社区标注而非官方结局清单；动漫/漫画剧情走向看 `wiki_extract`。
- 萌娘百科直连/镜像当前不可达，中文剧情以中文维基 + Bangumi dump 为主。
- CnGal 条目仅 42/112 有完整角色表（其余多为新作或未编辑），CnGal 无评分数据。
- `characters` 描述可能含剧透（源站如此），使用时注意。

## 重建 / 更新

```sh
python scripts/collect_vndb_full.py both     # VNDB g97+g1986 全量
python scripts/collect_anilist_deep.py       # AniList 动漫/漫画全量（带角色）
python scripts/enrich_vndb.py                # 每部 VN 角色表（断点续跑）
python scripts/enrich_wikipedia.py 500       # 中文维基摘要
python scripts/collect_bgm_archive.py        # Bangumi 官方 dump -> 百合条目+角色
python scripts/collect_cngal.py              # CnGal 百合题材全量
python scripts/build_corpus.py               # 重建主语料
python scripts/add_vndb_full.py && python scripts/add_anilist_deep.py
python scripts/add_bgm_archive.py && python scripts/add_cngal.py
python scripts/merge_enriched.py && python scripts/merge_extras.py
```

## 数据来源与许可

各源数据版权归原站：VNDB (CC BY-NC-SA)、AniList (TOU)、Bangumi Archive (CC BY-NC-ND)、CnGal (CC BY-NC-SA)、Wikipedia (CC BY-SA)、yuri-classification-archive (见其 LICENSE)。本仓库仅作研究/语料聚合使用，请遵循各源许可。

持续任务：老大说停之前持续扩充。待做：VNDB 冷门作角色补漏、CnGal STAFF/制作组子标签挖掘、MAL 补充。
