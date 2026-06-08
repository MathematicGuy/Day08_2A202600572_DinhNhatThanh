"""Task 3 - Convert landing files to markdown."""

import json
from pathlib import Path

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _looks_binary(text: str) -> bool:
    if not text:
        return False
    sample = text[:2000]
    control = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\r\t")
    return control / max(1, len(sample)) > 0.02


def _convert_pdf(filepath: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(filepath))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"\n\n## Trang {i}\n\n{text.strip()}")
        if pages:
            return "\n".join(pages)
    except ImportError as exc:
        raise RuntimeError("Cần cài pypdf để extract PDF thật: pip install pypdf") from exc
    except Exception:
        pass
    return ""


def _convert_with_markitdown(filepath: Path) -> str:
    if filepath.suffix.lower() == ".pdf":
        pdf_text = _convert_pdf(filepath)
        if pdf_text.strip():
            return pdf_text

    try:
        from markitdown import MarkItDown

        result = MarkItDown().convert(str(filepath))
        if result.text_content and not _looks_binary(result.text_content):
            return result.text_content
    except Exception:
        pass

    text = filepath.read_text(encoding="utf-8", errors="ignore")
    if _looks_binary(text):
        raise RuntimeError(f"Không extract được text sạch từ {filepath.name}")
    return text


def convert_legal_docs():
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_file in output_dir.glob("*.md"):
        old_file.unlink()

    if not legal_dir.exists():
        return []

    outputs = []
    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            content = _convert_with_markitdown(filepath).strip()
            if not content:
                content = f"# {filepath.stem}\n\nNo extracted text."
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(content, encoding="utf-8")
            outputs.append(output_path)
            print(f"Saved: {output_path}")
    return outputs


def convert_news_articles():
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_file in output_dir.glob("*.md"):
        old_file.unlink()

    if not news_dir.exists():
        return []

    outputs = []
    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() == ".json":
            data = json.loads(filepath.read_text(encoding="utf-8"))
            header = f"# {data.get('title', filepath.stem)}\n\n"
            header += f"**Source:** {data.get('url', 'N/A')}\n\n"
            header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"
            content = header + data.get("content_markdown", "")
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(content, encoding="utf-8")
            outputs.append(output_path)
            print(f"Saved: {output_path}")
        elif filepath.suffix.lower() in (".md", ".txt", ".html"):
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(filepath.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            outputs.append(output_path)
    return outputs


def convert_all():
    print("=" * 50)
    print("Task 3: Convert to Markdown")
    print("=" * 50)
    legal = convert_legal_docs()
    news = convert_news_articles()
    print(f"Done. Legal={len(legal)}, news={len(news)}. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
