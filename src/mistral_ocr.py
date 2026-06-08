"""Mistral OCR pilot utilities for legal PDF preprocessing comparisons."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "data" / "ocr" / "mistral" / "legal"
DEFAULT_PILOT_FILES = [
    PROJECT_DIR / "data" / "landing" / "legal" / "luat-phong-chong-ma-tuy-2021.pdf",
    PROJECT_DIR / "data" / "landing" / "legal" / "nghi-dinh-105-2021.pdf",
]


def _mistral_client():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not configured")
    try:
        from mistralai import Mistral
    except Exception:
        from mistralai.client import Mistral
    return Mistral(api_key=api_key)


def _model_dump(response) -> dict:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    return json.loads(json.dumps(response, default=str))


def ocr_pdf(pdf_path: Path, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict:
    """Run Mistral OCR on one PDF and persist raw JSON plus Markdown output."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    client = _mistral_client()
    model = os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")

    with pdf_path.open("rb") as f:
        uploaded = client.files.upload(
            file={"file_name": pdf_path.name, "content": f},
            purpose="ocr",
        )

    signed_url = client.files.get_signed_url(file_id=uploaded.id)
    response = client.ocr.process(
        model=model,
        document={"type": "document_url", "document_url": signed_url.url},
        table_format="markdown",
        confidence_scores_granularity="page",
    )
    payload = _model_dump(response)

    raw_json_path = output_dir / f"{pdf_path.stem}.ocr.json"
    markdown_path = output_dir / f"{pdf_path.stem}.ocr.md"
    raw_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(ocr_payload_to_markdown(payload), encoding="utf-8")
    return {
        "pdf": str(pdf_path),
        "json": str(raw_json_path),
        "markdown": str(markdown_path),
        "model": model,
        "pages": len(payload.get("pages", [])),
    }


def ocr_payload_to_markdown(payload: dict) -> str:
    pages = []
    for page in payload.get("pages", []):
        index = page.get("index", len(pages))
        header = page.get("header")
        footer = page.get("footer")
        markdown = page.get("markdown", "")
        sections = [f"## Page {index + 1}"]
        if header:
            sections.append(f"**Header:** {header}")
        sections.append(markdown)
        if footer:
            sections.append(f"**Footer:** {footer}")
        pages.append("\n\n".join(section for section in sections if section))
    return "\n\n---\n\n".join(pages)


def run_pilot(files: list[Path] | None = None, output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[dict]:
    """Run OCR on the default legal pilot set. This requires MISTRAL_API_KEY."""
    return [ocr_pdf(path, output_dir=output_dir) for path in (files or DEFAULT_PILOT_FILES)]


def inspect_markdown_quality(md_path: Path) -> dict:
    """Cheap text-quality diagnostics for baseline vs OCR Markdown comparison."""
    text = Path(md_path).read_text(encoding="utf-8", errors="ignore")
    markers = ["ch ống", "qu ản", "ng ười", "ph ối", "c ơ quan", "ma t úy"]
    lines = [line for line in text.splitlines() if line.strip()]
    short_lines = [line for line in lines if len(line.strip()) < 25]
    return {
        "path": str(md_path),
        "chars": len(text),
        "lines": len(lines),
        "short_line_ratio": len(short_lines) / max(1, len(lines)),
        "split_word_marker_count": sum(text.count(marker) for marker in markers),
        "page_heading_count": text.count("## Trang") + text.count("## Page"),
    }


if __name__ == "__main__":
    results = run_pilot()
    print(json.dumps(results, ensure_ascii=False, indent=2))
