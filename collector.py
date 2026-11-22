#!/usr/bin/env python3
"""GitHub 热榜采集器。

今日 / 本周 / 本月：抓 github.com/trending（原生 trending，带周期内新增星数）
今年：走 Search API（created:>=365 天，按星数排序）

用法：python3 ghhot.py --out /srv/sitehub/data/ghhot.json
环境变量：GITHUB_TOKEN（可选，仅影响年度搜索额度）
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; starlithub-ghhot/1.1)"
TRENDING = "https://github.com/trending?since=%s"
API = "https://api.github.com/search/repositories"
PER = 12
RANGES = [("day", "daily", "今日"), ("week", "weekly", "本周"), ("month", "monthly", "本月"), ("year", None, "今年")]


def get(url, headers=None, timeout=25, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8", **(headers or {})})
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def parse_trending(page):
    out = []
    for block in re.findall(r"<article[\s\S]*?</article>", page):
        m = re.search(r"<h2[^>]*>[\s\S]*?href=\"/([^\"]+)\"", block)
        if not m:
            continue
        full = m.group(1).strip()
        d = re.search(r"<p[^>]*class=\"[^\"]*col-9[^\"]*\"[^>]*>([\s\S]*?)</p>", block)
        desc = strip_tags(d.group(1)) if d else ""
        lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', block)
        st = re.search(r'href="/[^"]+/stargazers"[\s\S]{0,800}?([\d,]+)\s*</a>', block)
        ga = re.search(r"([\d,]+)\s+stars\s+(today|this week|this month)", block)
        out.append({
            "full_name": full,
            "html_url": "https://github.com/" + full,
            "description": desc[:180],
            "stars": int(st.group(1).replace(",", "")) if st else 0,
            "gained": int(ga.group(1).replace(",", "")) if ga else None,
            "language": lang.group(1).strip() if lang else "",
        })
    return out


def search_year(token):
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=364)).isoformat()
    q = "created:>=%s fork:false archived:false stars:>=500" % since
    url = API + "?" + urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": PER})
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.loads(get(url, headers=headers))
    out = []
    for it in data.get("items", [])[:PER]:
        out.append({
            "full_name": it.get("full_name"),
            "html_url": it.get("html_url"),
            "description": (it.get("description") or "")[:180],
            "stars": it.get("stargazers_count", 0),
            "gained": None,
            "language": it.get("language") or "",
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ghhot.json"))
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "").strip()

    result = {"updated_at": int(time.time()), "ranges": {}}
    ok = 0
    for key, since, label in RANGES:
        try:
            if since:
                items = parse_trending(get(TRENDING % since))
            else:
                items = search_year(token)
        except Exception as e:
            print("%s failed: %s" % (key, e), file=sys.stderr)
            items = []
        items = items[:PER]
        for i, it in enumerate(items, 1):
            it["rank"] = i
        result["ranges"][key] = {"label": label, "items": items}
        if items:
            ok += 1
        print("%s: %d items" % (key, len(items)), flush=True)
        time.sleep(1.5)

    if ok == 0:
        print("nothing fetched, keep previous file", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    os.replace(tmp, args.out)
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
