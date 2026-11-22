# gh-hot — GitHub 项目热榜（今日 / 本周 / 本月 / 今年）

一个零依赖的小工具：每天定时抓一次 GitHub 热榜，产出一个 JSON，配一个纯静态卡片页。
本站 [dash.starlithub.com](https://dash.starlithub.com/) 的「GitHub 热榜」板块就是它。

## 数据从哪来

| 周期 | 来源 | 说明 |
| --- | --- | --- |
| 今日 / 本周 / 本月 | `https://github.com/trending?since=daily|weekly|monthly` | GitHub 原生 trending，带「周期内新增星数」 |
| 今年 | GitHub Search API `created:>=一年前`，按星数排序 | trending 没有年度维度，用搜索补位 |

每个条目包含：`rank`、`full_name`、`html_url`、`description`、`stars`、`gained`（周期内新增星数，年度为空）、`language`。

## 用法

```bash
# 抓一次，产出 data/ghhot.json
python3 collector.py --out data/ghhot.json

# 带 token 可提高年度搜索额度（可选）
GITHUB_TOKEN=ghp_xxx python3 collector.py --out data/ghhot.json
```

只依赖 Python 3.9+ 标准库，不需要 `pip install` 任何东西。

## 定时

两种任选：

1. **cron**（自建服务器）：
   ```
   5 6 * * * cd /path/to/gh-hot && /usr/bin/python3 collector.py --out data/ghhot.json >> /var/log/ghhot.log 2>&1
   ```
2. **GitHub Actions**：仓库自带 `.github/workflows/update.yml`，每天 22:05 UTC（北京 06:05）跑一次并把新数据提交回仓库，无需服务器。

## 页面

`demo/index.html` 是一个读取同目录 `../data/ghhot.json` 的纯静态展示页：

```bash
python3 -m http.server 8000   # 然后打开 http://127.0.0.1:8000/demo/
```

## 数据结构

```json
{
  "updated_at": 1795193532,
  "ranges": {
    "day":   { "label": "今日", "items": [ { "rank": 1, "full_name": "owner/repo", "stars": 14000, "gained": 1700, "language": "Python", "html_url": "https://github.com/owner/repo", "description": "..." } ] },
    "week":  { "label": "本周", "items": [] },
    "month": { "label": "本月", "items": [] },
    "year":  { "label": "今年", "items": [] }
  }
}
```

抓取失败时保留上一份文件（不会写出空数据）。

## 说明

- trending 页面是 HTML，解析用的是 `article` 分块 + 正则；GitHub 改版时可能需要跟着调。
- 仅供个人展示与研究使用，请遵守 GitHub 的服务条款，别把请求频率拉高。

## License

MIT
