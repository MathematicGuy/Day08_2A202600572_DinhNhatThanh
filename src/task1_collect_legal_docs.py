"""Task 1 - Download real legal documents from official sources."""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

LEGAL_DOCS = [
    {
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-quyet-so-73-2021-qh14-33659.htm",
        "filename": "luat-phong-chong-ma-tuy-2021.pdf",
    },
    {
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-105-2021-nd-cp-34944/37821.htm",
        "filename": "nghi-dinh-105-2021.pdf",
    },
    {
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-57-2022-nd-cp-37734.htm",
        "filename": "nghi-dinh-57-2022.pdf",
    },
    {
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-90-2024-nd-cp-42369/51055.htm",
        "filename": "nghi-dinh-90-2024.pdf",
    },
    {
        "page_url": "https://congbao.chinhphu.vn/tai-ve-van-ban-so-116-2021-nd-cp-36404-39135?format=pdf",
        "filename": "nghi-dinh-116-2021-cai-nghien.pdf",
    },
    {
        "page_url": "https://congbao.chinhphu.vn/so-do-van-ban-so-12-2017-qh14-24289",
        "filename": "luat-sua-doi-bo-luat-hinh-su-2017.pdf",
    },
    {
        "page_url": "https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-01-vbhn-vpqh-24866.htm",
        "filename": "bo-luat-hinh-su-hop-nhat-2017.pdf",
        "download_all": True,
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Day08RAG/1.0)",
}


def setup_directory():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in DATA_DIR.glob("*.pdf"):
        old_file.unlink()
    print(f"Directory ready: {DATA_DIR}")


def _find_download_url(page_url: str, preferred_ext: str = ".pdf") -> str:
    response = requests.get(page_url, headers=HEADERS, timeout=30, verify=False)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/pdf" in content_type or "application/octet-stream" in content_type:
        return page_url

    html = response.text
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    candidates = [unescape(urljoin(page_url, href)) for href in hrefs]

    for ext in (preferred_ext, ".doc", ".docx"):
        for url in candidates:
            if ext in url.lower() and "cdnchinhphu.vn" in url.lower():
                return url

    raise RuntimeError(f"Cannot find PDF/DOC download link in {page_url}")


def _find_download_urls(page_url: str, preferred_ext: str = ".pdf") -> list[str]:
    response = requests.get(page_url, headers=HEADERS, timeout=30, verify=False)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/pdf" in content_type or "application/octet-stream" in content_type:
        return [page_url]

    hrefs = re.findall(r'href=["\']([^"\']+)["\']', response.text, flags=re.IGNORECASE)
    candidates = [unescape(urljoin(page_url, href)) for href in hrefs]
    urls = []
    for url in candidates:
        if preferred_ext in url.lower() and "cdnchinhphu.vn" in url.lower() and url not in urls:
            urls.append(url)
    if not urls:
        raise RuntimeError(f"Cannot find PDF/DOC download link in {page_url}")
    return urls


def download_file(page_url: str, filename: str) -> Path:
    download_url = _find_download_url(page_url, Path(filename).suffix.lower())
    response = requests.get(download_url, headers=HEADERS, timeout=60, verify=False)
    response.raise_for_status()
    if len(response.content) <= 1024:
        raise RuntimeError(f"Downloaded file is too small: {download_url}")

    filepath = DATA_DIR / filename
    filepath.write_bytes(response.content)
    print(f"Saved: {filepath}")
    print(f"Source: {download_url}")
    return filepath


def download_files(page_url: str, filename: str) -> list[Path]:
    urls = _find_download_urls(page_url, Path(filename).suffix.lower())
    if len(urls) == 1:
        return [download_file(page_url, filename)]

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    paths = []
    for i, download_url in enumerate(urls, 1):
        response = requests.get(download_url, headers=HEADERS, timeout=60, verify=False)
        response.raise_for_status()
        if len(response.content) <= 1024:
            raise RuntimeError(f"Downloaded file is too small: {download_url}")
        filepath = DATA_DIR / f"{stem}-part-{i:02d}{suffix}"
        filepath.write_bytes(response.content)
        paths.append(filepath)
        print(f"Saved: {filepath}")
        print(f"Source: {download_url}")
    return paths


def collect_legal_docs() -> list[Path]:
    setup_directory()
    paths = []
    for doc in LEGAL_DOCS:
        if doc.get("download_all"):
            paths.extend(download_files(doc["page_url"], doc["filename"]))
        else:
            paths.append(download_file(doc["page_url"], doc["filename"]))
    return paths


if __name__ == "__main__":
    collect_legal_docs()
