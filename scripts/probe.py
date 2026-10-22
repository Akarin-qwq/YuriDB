#!/usr/bin/env python3
"""探测各数据源：VNDB yuri tag id、Bangumi 百合 tag、AniList Yuri tag。"""
import json, urllib.request

def post(url, payload, headers=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "yuri-corpus/0.1 (local research)", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "yuri-corpus/0.1", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# 1. VNDB: 找 yuri tag
tags = post("https://api.vndb.org/kana/tag", {"filters": ["search", "=", "yuri"], "fields": "id,name,vn_count", "results": 10})
print("VNDB tags:", [(t["id"], t["name"], t["vn_count"]) for t in tags["results"]])

# 2. AniList GraphQL: Yuri tag 媒体数
q = '''query { Page(perPage: 5) { media(tag: "Yuri", sort: POPULARITY_DESC, type: ANIME) { id title { romaji native } popularity } } }'''
data = post("https://graphql.anilist.co", {"query": q})
print("AniList anime:", [(m["id"], m["title"]["romaji"]) for m in data["data"]["Page"]["media"]])

# 3. Bangumi: 百合 tag 搜索
try:
    bgm = post("https://api.bgm.tv/v0/search/subjects",
               {"keyword": "百合", "filter": {"tag": ["百合"]}, "limit": 5, "sort": "rank"},
               headers={"Authorization": ""})
    print("Bangumi:", [(s["id"], s["name"]) for s in bgm.get("data", [])], "total:", bgm.get("total"))
except Exception as e:
    print("Bangumi err:", e)
