# web-scraper-template

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**中文** | [English](#english)

一个干净、可复用的 Python 爬虫模板：翻页、失败重试（指数退避）、限速、CSV / Excel / JSON 导出、命令行参数，并附带 pytest 测试。
示例目标使用专门供练习爬虫的网站 [quotes.toscrape.com](https://quotes.toscrape.com) 和 [books.toscrape.com](https://books.toscrape.com)。

## 功能

- **httpx + selectolax**：速度快、依赖少
- **自动翻页**：跟随 “下一页” 链接，支持 `--max-pages` / `--max-items`
- **重试与退避**：对 429 / 5xx / 网络错误自动重试（指数退避 + 抖动），404 等不重试
- **限速**：两次请求之间最少间隔 `--delay` 秒，对目标网站友好
- **导出**：`.csv`（UTF-8 BOM，Excel 打开中文不乱码）、`.xlsx`（冻结表头、自动列宽）、`.json`
- **配置**：命令行参数或 `.env`（支持代理）
- **易扩展**：新增网站只需写一个解析函数并注册到 `PARSERS`

## 快速开始

```bash
git clone https://github.com/lucas-cr-dev/web-scraper-template.git
cd web-scraper-template
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # 可选

python -m scraper quotes -o output/quotes.csv
python -m scraper books --max-pages 3 --delay 1.5 -o output/books.xlsx
```

## 命令行参数

| 参数 | 说明 |
|---|---|
| `site` | `quotes` 或 `books` |
| `-o, --output` | 输出文件，按后缀决定格式（`.csv` / `.xlsx` / `.json`） |
| `--url` | 起始 URL（默认使用网站首页） |
| `--max-pages` / `--max-items` | 页数 / 条数上限 |
| `--delay` | 请求间隔秒数（默认 1.0） |
| `--retries` / `--timeout` | 重试次数 / 超时秒数 |
| `--proxy` | 代理，例如 `http://127.0.0.1:7890` |
| `-v` | 输出详细日志 |

## 新增一个网站

```python
# scraper/parsers.py
def parse_mysite(html: str, base_url: str):
    tree = HTMLParser(html)
    items = [{"name": n.text(strip=True)} for n in tree.css(".item .name")]
    return items, _next_link(tree, base_url)   # 没有下一页时返回 None

PARSERS["mysite"] = parse_mysite
```

## 测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

测试使用本地 HTML 样本和 `httpx.MockTransport`，不访问网络。

## 合规说明

请遵守目标网站的 robots.txt 与服务条款，只采集公开数据并控制请求频率。本模板仅作技术示例。

## 关于

代码由 AI 辅助编写，并经人工审核与测试。需要定制爬虫 / 数据采集？欢迎在 [GitHub 主页](https://github.com/lucas-cr-dev) 联系我。

---

<a id="english"></a>
## English

A clean, reusable Python scraping template: pagination, retries with exponential backoff, rate limiting, CSV / Excel / JSON export, a CLI, and pytest tests. The demo targets are the scraping sandboxes [quotes.toscrape.com](https://quotes.toscrape.com) and [books.toscrape.com](https://books.toscrape.com).

### Features

- **httpx + selectolax** – fast, lightweight
- **Pagination** – follows "next" links; `--max-pages` / `--max-items` limits
- **Retries** – 429 / 5xx / network errors retried with exponential backoff + jitter; 4xx like 404 are not retried
- **Rate limiting** – at least `--delay` seconds between requests
- **Export** – `.csv` (UTF-8 BOM, Excel-friendly), `.xlsx` (frozen header, auto width), `.json`
- **Config** – CLI flags or `.env` (proxy supported)
- **Extensible** – add a site by writing one parser function and registering it in `PARSERS`

### Quick start

```bash
pip install -r requirements.txt
python -m scraper quotes -o output/quotes.csv
python -m scraper books --max-pages 3 --delay 1.5 -o output/books.xlsx
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests use local HTML fixtures and `httpx.MockTransport` – no network access.

### Responsible use

Respect each site's robots.txt and terms of service, scrape only public data, and keep request rates low.

### About

Code is AI-assisted and human-reviewed. Need a custom scraper? Reach me via my [GitHub profile](https://github.com/lucas-cr-dev).

License: [MIT](LICENSE)
