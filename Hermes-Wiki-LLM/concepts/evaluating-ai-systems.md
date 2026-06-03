---
title: "Concept: Evaluating AI Systems"
type: concept
aliases: [[Model Selection]], [[Evaluation Pipeline]], [[AI System Evaluation]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #evaluation, #benchmark, #deployment]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Evaluating AI Systems

Chapter 4 of *AI Engineering* focuses on how to apply evaluation methods
to select models and build evaluation pipelines for real applications.

## Evaluation-Driven Development
Define evaluation criteria **before** building. Without visibility into how
an application is performing, it's worse than not deploying at all.

## Evaluation Criteria

### Factual Consistency
- **Local factual consistency:** output vs provided context (e.g.,
  summarization accuracy, policy adherence)
- **Global factual consistency:** output vs open knowledge (fact-checking,
  general Q&A)
- Hardest part: determining what the facts actually are
- Models rely heavily on relevance, largely ignoring stylistic features
  humans find important (scientific references, neutral tone)

### Safety Categories
1. Inappropriate language (profanity, explicit content)
2. Harmful recommendations/tutorials
3. Hate speech and discrimination
4. Violence and threats
5. Stereotypes and biases
6. Political/religious biases

Safety tools: OpenAI content moderation, Meta's Llama Guard, Perspective API,
specialized toxicity classifiers in different languages.

## Model Selection Workflow
Four iterative steps:
1. **Filter** — eliminate models whose hard attributes don't work
   (licenses, privacy, control requirements)
2. **Narrow** — use public benchmarks and leaderboards to find promising
   candidates
3. **Experiment** — run your own evaluation pipeline on shortlisted models
4. **Monitor** — track performance in production, collect feedback

### Hard vs Soft Attributes
- **Hard:** Licenses, training data, model size, privacy constraints —
  impossible or impractical to change
- **Soft:** Accuracy, toxicity, factual consistency — improvable with
  prompt engineering, RAG, fine-tuning

## Model APIs vs Self-Hosting
Key trade-off dimensions (see [[model-apis-vs-self-hosting]] for full
comparison):
- Cost, control, data privacy
- Performance ceiling (best proprietary models outperform open ones)
- Engineering effort (APIs are expensive, self-hosting needs engineering)
- On-device deployment requires self-hosting

## Public Benchmarks — Caveats
- Thousands of benchmarks exist but can't be fully trusted
- Data contamination is common (models trained on benchmark data)
- Benchmarks saturate quickly
- Must supplement with application-specific evaluation

## Building an Evaluation Pipeline
1. Define criteria and scoring rubrics
2. Map scores to business metrics
3. Determine usefulness thresholds
4. Select evaluation methods per criterion
5. Continuously monitor and iterate

## Related
- [[evaluation-methodology]]
- [[ai-engineering-overview]]
- [[data-engineering-for-ai]]
- [[model-apis-vs-self-hosting]]
