---
title: "Concept: Foundation Models"
type: concept
aliases: [[Foundation Model]], [[LLM]], [[Large Language Model]], [[LMM]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#model, #llm, #foundation-model, #architecture, #training, #alignment]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Foundation Models

Large AI models trained on broad data that can be adapted to a wide range of
downstream tasks. The term covers both large language models (LLMs) and
large multimodal models (LMMs).

## Training Data
Differences in foundation models trace back to decisions about training data:
- **Data sources and distribution** determine capabilities and limitations
- Scale requires self-supervision — models learn from unlabeled data
- Data curation (filtering, deduplication, decontamination) is critical
- Growing lack of transparency from model developers about training data

## Model Architecture
- The **transformer architecture** dominates due to its ability to scale and
  handle long-range dependencies
- Key components: attention mechanisms, feed-forward layers, positional
  encodings
- Emerging competitors (state space models, etc.) are being explored but
  have not yet displaced transformers for most tasks

## Model Size and Scaling
- Model developers must determine appropriate size — larger is not always
  better for a given application
- Scaling laws guide the relationship between compute, data, and model size
- Vocabulary sizes vary (Mixtral 8x7B: 32,000; GPT-4: 100,256 tokens)
- Tokenization: breaking text into tokens (≈¾ the length of a word for GPT-4)

## Pre-training vs Post-training (Alignment)
- **Pre-training:** Makes the model capable — learns language patterns,
  facts, and reasoning from broad data
- **Post-training (alignment):** Shapes behavior for safety, usefulness, and
  ease of use — teaches human preferences, helpfulness, harmlessness

## Sampling and Generation
Often overlooked but critically important:
- Sampling strategy determines how the model chooses from all possible
  outputs
- Explains many baffling AI behaviors: hallucinations, inconsistency,
  variability
- Choosing the right sampling strategy (temperature, top-p, top-k) can
  significantly boost performance with little effort
- Changing generation settings is often the cheapest way to improve output

## Two Types of Language Models
1. **Masked language models** (e.g., BERT) — predict masked tokens using
   bidirectional context
2. **Autoregressive models** (e.g., GPT) — predict next token given
   previous tokens; power most modern applications

## Related
- [[ai-engineering-overview]]
- [[evaluation-methodology]]
- [[prompt-engineering]]
- [[fine-tuning]]
- [[inference-optimization]]
