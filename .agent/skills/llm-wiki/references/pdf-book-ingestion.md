# PDF Book Ingestion into the Wiki

Concrete recipe for ingesting a PDF book (e.g. O'Reilly, Manning, Springer)
into an llm-wiki knowledge base. Based on ingesting *AI Engineering* by Chip
Huyen (991 pages, ~40% text-extractable).

## Tools
- `uv run --with pypdf python` — extracts text from PDF pages
- `pypdf.PdfReader` — reads PDF, `.pages` list, `.extract_text()` per page
- `grep`, `sed`, `head` — navigate extracted text for TOC/chapter headings

## Step-by-Step

### 1. Extract text from the PDF
```bash
uv run --with pypdf python -c "
import pypdf
reader = pypdf.PdfReader('raw/AI_Engineering_Building_Applications_Chip_Huyen.pdf')
print(f'Total pages: {len(reader.pages)}')
with open('raw/<book-name>-full-text.txt', 'w', encoding='utf-8') as f:
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        f.write(f'\n\n=== PAGE {i+1} ===\n\n')
        f.write(text)
"
```

### 2. Find the chapter structure
The PDF's Table of Contents page is often an image (not extractable). Instead,
look in the **preface outline** (usually pages 9-22 of the PDF). Search for
lines like "Chapter 5 covers..." or "Chapters 1 to 4..." — the preface
paragraphs list every chapter with a one-paragraph summary.

```bash
# Find chapter references in preface
grep -n "^Chapter [0-9]" raw/<book-name>-full-text.txt | head -20

# Read the preface section
sed -n '370,600p' raw/<book-name>-full-text.txt | head -120
```

The preface gives you: chapter numbers, chapter titles, and what each chapter
covers. This is enough to create one wiki page per chapter.

### 3. Identify non-extractable chapters
Check the last text-extractable page number:
```bash
grep -n "=== PAGE " raw/<book-name>-full-text.txt | tail -5
```
For *AI Engineering* (991 pages total, only 401 extractable), chapters 5-10
had no extractable text. Their content was reconstructed from preface summaries
and expected position between known chapters.

### 4. Create wiki pages per chapter
For each chapter, create a concept page at `concepts/<chapter-slug>.md`.
Use the preface paragraph as the outline for the page body. Cross-reference
to other chapters via `[[wikilinks]]`.

For chapters with direct extractable text, pull key definitions, frameworks,
and quotes. For non-extractable chapters, state what the preface says and set
`confidence: 0.7` in frontmatter.

### 5. Create entity pages
One entity page per notable person/organization mentioned:
- Author(s)
- Key figures referenced throughout

### 6. Create comparison pages
If the book contains a side-by-side analysis (e.g., Model APIs vs Self-Hosting),
create a page at `comparisons/<slug>.md` with a table.

### 7. Update index.md and log.md
Add all new pages to `index.md` under correct sections. Log the batch ingest.

## Pitfalls

- **"Binary file matches" from grep** — the extracted text is large; pipe grep
  output or use `grep -a` to avoid binary-file warnings
- **Chapter heading grep fails** — chapter headings often span lines in
  extracted text (e.g. "Chapter 1. Introduction to Building AI\nApplications
  with Foundation Models"). Search for just "Chapter N." instead of the full
  title
- **pypdf is slow on 1000+ page PDFs** — it processes sequentially; 991 pages
  takes ~20s. Acceptable for one-time extraction
- **Extracted text has no paragraph boundaries** — lines are word-wrapped.
  Accept this; the text is for reference, not display
