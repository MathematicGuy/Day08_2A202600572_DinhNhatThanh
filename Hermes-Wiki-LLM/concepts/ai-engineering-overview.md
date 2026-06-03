---
title: "Concept: AI Engineering Overview"
type: concept
aliases: [[AI Engineering]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #architecture, #llm, #foundation-model, #deployment]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# AI Engineering Overview

AI engineering is the process of building applications on top of readily
available foundation models (LLMs and LMMs). The field emerged as training
foundation models became prohibitively expensive for most organizations,
shifting the focus from building models to **adapting and deploying** them.

## The Scale Shift
- AI models post-2020 consume a nontrivial portion of the world's electricity
- Training LLMs requires data, compute, and talent only a few organizations
  can afford → **model as a service** emerged
- The barrier to entry for *building applications* decreased dramatically
  (possible without writing a single line of code)

## Foundation Model Characteristics
- A *foundation model* is a large AI model trained on broad data that can be
  adapted to a wide range of downstream tasks
- Enables capabilities previously impossible: translation, summarization,
  coding, math, reasoning, multimodal understanding
- Models learn statistical patterns from data — outputs are probabilistic
  predictions, not deterministic answers

## AI vs Traditional ML Engineering
While many principles remain the same (systematic experimentation, rigorous
evaluation, optimization for speed/cost), foundation models introduce:
- **New possibilities:** open-ended generation, zero-shot/few-shot learning,
  multimodal capabilities, tool use, agentic behaviors
- **New challenges:** hallucinations, safety and alignment, evaluation at
  scale, prompt injection attacks, unpredictable model behavior

## Key Application Patterns
1. **RAG (Retrieval-Augmented Generation):** Provide relevant context from
   external knowledge bases alongside the query
2. **Agentic:** Models that can reason, plan, use tools, and take actions
3. **Fine-tuning:** Adapting model weights for specific tasks
4. **Prompt Engineering:** Crafting instructions to steer model behavior
   without changing weights

## The AI Stack
The AI stack has evolved from owning the entire pipeline (data → training →
deployment) to mostly using pre-trained models via APIs, with effort
concentrated on:
- Evaluation and monitoring
- Context construction (RAG, prompts)
- Fine-tuning and data engineering
- Inference optimization and deployment

## Related
- [[foundation-models]]
- [[evaluation-methodology]]
- [[rag-and-agents]]
- [[prompt-engineering]]
- [[fine-tuning]]
- [[chip-huyen]]
