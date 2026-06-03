---
title: "Concept: Evaluation Methodology"
type: concept
aliases: [[AI Evaluation]], [[AI as Judge]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #evaluation, #benchmark, #data]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Evaluation Methodology

Evaluation is one of the hardest challenges in AI engineering. For some
applications, figuring out evaluation can take the majority of development
effort. This page covers the methods; [[evaluating-ai-systems]] covers how
to apply them in practice.

## Why Evaluation Is Hard
- Foundation models are **open-ended** — output quality is subjective
- Many teams settle for word of mouth or eyeballing results instead of
  systematic evaluation
- Evaluation must be considered in the context of the whole system, not
  in isolation

## Core Metrics for Language Models
- **Cross entropy** — measures how well the model predicts the next token
- **Perplexity** — exponential of cross entropy; lower is better
- These guide training and fine-tuning but don't capture real-world quality

## Human Evaluation
- Still necessary for many applications
- Slow and expensive — the goal is to automate as much as possible

## Automatic Evaluation
Two categories:

### Exact Evaluation
Checks outputs against ground truth (e.g., multiple choice, closed-form
answers). Works for structured tasks but not open-ended generation.

### Subjective Evaluation
Evaluates quality of open-ended responses. The rising star:

**AI as a Judge** — using AI to evaluate AI responses.
- Gaining rapid traction in the industry
- Controversial — critics argue AI isn't trustworthy enough for this task
- Quality depends on what model and prompt the judge uses
- Much cheaper than human evaluation, making it scalable
- Best practices: use multiple judges, benchmark the judge against human
  ratings, calibrate prompts carefully

## Challenges
- No single metric captures all aspects of quality
- Evaluation drift — as models improve, benchmarks become saturated
- Evaluation data contamination — models may have seen test data during
  training

## Related
- [[evaluating-ai-systems]]
- [[ai-engineering-overview]]
- [[data-engineering-for-ai]]
