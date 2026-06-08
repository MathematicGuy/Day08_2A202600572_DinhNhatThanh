"""Task 2 - Crawl real news articles and store JSON with metadata."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vietnamnet.vn/cong-an-tphcm-thong-tin-vu-2-khoi-to-bat-giu-ca-si-chi-dan-va-nguoi-mau-an-tay-2341921.html",
    "https://vietnamnet.vn/ca-si-chi-dan-nguoi-mau-an-tay-gui-loi-xin-loi-va-khuyen-dung-dinh-den-ma-tuy-2342348.html",
    "https://vietnamnet.vn/chi-dan-an-tay-truc-phuong-la-nhung-mat-xich-cuoi-trong-duong-day-ma-tuy-2341934.html",
    "https://thanhnien.vn/ca-si-son-ngoc-minh-vua-bi-bat-vi-lien-quan-den-ma-tuy-la-ai-18526052012481811.htm",
    "https://ngoisao.vnexpress.net/dien-vien-huu-tin-bi-tam-giu-vi-lien-quan-ma-tuy-4475248.html",
    "https://vnexpress.net/dien-vien-hai-huu-tin-bi-de-nghi-truy-to-7-15-nam-tu-4530802.html",
    "https://plo.vn/bat-khan-cap-ca-si-chau-viet-cuong-post473865.html",
    "https://www.mps.gov.vn/bai-viet/chuong-trinh-nghe-thuat-hung-yen-nang-ha-xanh-trong-vi-cong-dong-khong-ma-tuy-1777080724",
    "https://www.mps.gov.vn/bai-viet/khao-sat-huong-dan-thuc-hien-diem-chuong-trinh-muc-tieu-quoc-gia-phong-chong-ma-tuy-den-nam-2030-tai-tinh-nghe-an-1769516110",
    "https://www.mps.gov.vn/bai-viet/co-so-cai-nghien-ma-tuy-tinh-quang-ninh-phat-huy-tot-vai-tro-gop-phan-phong-ngua-va-dau-tranh-phong-chong-toi-pham-te-nan-ma-tuy-d23-t45713",
    "https://mps.gov.vn/bai-viet/thanh-hoa-day-manh-cong-tac-tuyen-truyen-phong-chong-ma-tuy-xay-la-chan-mem-tu-nhan-thuc-cong-dong-1778213020",
    "https://vnexpress.net/25-canh-sat-cai-trang-dan-choi-tinh-nhan-de-bat-ong-trum-ma-tuy-3373694.html",
    "https://vnexpress.net/cuoc-vay-bat-doi-vo-chong-20-nam-tron-truy-na-4219270.html",
    "https://ngoisao.vnexpress.net/truong-ban-mo-dai-ly-ma-tuy-2477022.html",
    "https://vietnamnet.vn/ca-si-chi-dan-tag12386958729930987427.html",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Day08RAG/1.0)",
}


def setup_directory():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in DATA_DIR.glob("article_*.json"):
        old_file.unlink()


def _strip_tags(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</p\s*>", "\n\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _extract_title(html: str, fallback: str) -> str:
    patterns = [
        r"<h1[^>]*>([\s\S]*?)</h1>",
        r"<meta[^>]+property=[\"']og:title[\"'][^>]+content=[\"']([^\"']+)",
        r"<title[^>]*>([\s\S]*?)</title>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return _strip_tags(match.group(1)).strip()
    return fallback


def _extract_article_text(html: str) -> str:
    candidates = []
    for pattern in [
        r"<article[^>]*>([\s\S]*?)</article>",
        r"<div[^>]+class=[\"'][^\"']*(?:article|detail|content|maincontent|fck_detail)[^\"']*[\"'][^>]*>([\s\S]*?)</div>",
    ]:
        candidates.extend(re.findall(pattern, html, flags=re.IGNORECASE))

    raw = max(candidates, key=len) if candidates else html
    text = _strip_tags(raw)
    if len(text) < 500:
        text = _strip_tags(html)
    if len(text) < 500:
        raise RuntimeError("Article text is too short after extraction")
    return text


async def crawl_article(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=30, verify=False)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    html = response.text
    title = _extract_title(html, url)
    content = _extract_article_text(html)
    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": f"# {title}\n\n{content}",
    }


async def crawl_all():
    setup_directory()
    saved = []
    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        try:
            article = await crawl_article(url)
        except Exception as exc:
            print(f"Skip failed URL: {url} ({exc})")
            continue
        filepath = DATA_DIR / f"article_{i:02d}.json"
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        saved.append(filepath)
        print(f"Saved: {filepath}")
    return saved


if __name__ == "__main__":
    asyncio.run(crawl_all())
