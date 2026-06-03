# WikiLLM Governance Schema

## Domain
AI/ML Engineering — building applications with large language models, covering
tooling, architecture, deployment, data management, and evaluation.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `ai-engineering-overview.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated_at` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append
  `^[raw/articles/source-file.md]` at the end of paragraphs whose claims come
  from a specific source. This lets a reader trace each claim back without
  re-reading the whole raw file. Optional on single-source pages where the
  `sources:` frontmatter is enough.

## Frontmatter (Wiki Pages)
```yaml
---
title: "Concept: [Name]"
type: concept | entity | comparison | query | summary
aliases: [[Shorthand]]
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
confidence: 0.0-1.0
tags: [#concept, #relevant-tag]
sources: [raw/articles/source-name.md]
contradictions: [other-page-slug]   # only when in conflict
---
```

`confidence` is a decimal between 0.0 and 1.0:
- 0.9-1.0 = well-supported across multiple sources
- 0.5-0.8 = reasonable but limited corroboration
- 0.0-0.4 = speculative, single-source, or contested

Pages with `confidence < 0.5` are flagged for review during lint. Pages with
`contradictions` set must note both positions in the body with dates.

## Frontmatter (Raw Sources)
```yaml
---
source_url: <original URL if applicable>
ingested: YYYY-MM-DD
sha256: <hex digest of body content>
---
```
The sha256 lets re-ingests detect drift. Compute over body only (everything
after the closing `---`), not the frontmatter itself.

## Tag Taxonomy
- **Concepts:** #concept, #architecture, #deployment, #training, #inference,
  #evaluation, #data, #alignment
- **Models:** #model, #llm, #foundation-model, #fine-tuning, #rag
- **Techniques:** #optimization, #prompt-engineering, #tool-use, #agent,
  #multimodal
- **People/Orgs:** #person, #company, #lab, #open-source, #research
- **Product:** #product-management, #analyst, #design, #ux
- **Meta:** #comparison, #timeline, #controversy, #prediction

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed,
add it here first, then use it. This prevents tag sprawl.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central
  to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details, or things outside
  the domain
- **Split a page** when it exceeds ~200 lines — break into sub-topics with
  cross-links
- **Archive a page** when its content is fully superseded — move to `_archive/`,
  remove from index

## Entity Pages
One page per notable entity. Include:
- Overview / what it is
- Key facts and dates
- Relationships to other entities ([[wikilinks]])
- Source references

## Concept Pages
One page per concept or topic. Include:
- Definition / explanation
- Current state of knowledge
- Open questions or debates
- Related concepts ([[wikilinks]])

## Comparison Pages
Side-by-side analyses. Include:
- What is being compared and why
- Dimensions of comparison (table format preferred)
- Verdict or synthesis
- Sources

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
