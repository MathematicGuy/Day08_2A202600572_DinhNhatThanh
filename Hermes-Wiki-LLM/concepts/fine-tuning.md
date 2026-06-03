---
title: "Concept: Fine-Tuning"
type: concept
aliases: [[Finetuning]], [[Model Adaptation]], [[SFT]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #fine-tuning, #training, #optimization]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Fine-Tuning

Adapting a foundation model to a specific application by updating its
weights. More powerful than prompt engineering but requires more data,
compute, and expertise.

## Why Fine-Tune?
- Improves performance on specific tasks beyond what prompting can achieve
- Can match or exceed proprietary model quality with smaller, open models
- Gives control over model behavior (safety, style, domain knowledge)
- Reduces inference cost (smaller fine-tuned model vs larger prompted model)

## Memory Challenges
Foundation models are large — fine-tuning them naively requires enormous
memory. Key techniques to reduce memory footprint:
- **LoRA (Low-Rank Adaptation):** Train low-rank matrices injected into
  the model, keeps base weights frozen
- **QLoRA:** Quantized LoRA — further reduces memory via 4-bit quantization
- **Adapters:** Small trainable modules inserted between layers
- **Parameter-efficient fine-tuning (PEFT):** Family of methods that update
  only a small fraction of parameters

## Approaches

### Full Fine-Tuning
- Updates all model parameters
- Highest quality but most expensive
- Requires multiple GPUs for all but the smallest models

### Parameter-Efficient Fine-Tuning (PEFT)
- LoRA, QLoRA, adapters, prefix tuning, prompt tuning
- Much less memory — can fine-tune 70B models on a single GPU
- Quality is close to full fine-tuning for many tasks

### Model Merging (Experimental)
- Combine weights from multiple fine-tuned models
- Emerging technique, results vary
- Can produce models that inherit capabilities from multiple sources

## The Fine-Tuning Process
1. Getting data is the hardest part (see [[data-engineering-for-ai]])
2. Fine-tuning frameworks make the training process straightforward
3. Calculate memory footprint before starting (model size + optimizer
   states + activations + gradients)

## When to Fine-Tune vs Other Methods
- **Prompt engineering:** First — cheapest, fastest
- **RAG:** Second — adds knowledge without modifying weights
- **Fine-tuning:** Third — when the above aren't enough for task quality
- Can be combined: fine-tune the base behavior, then use RAG/prompts
  to steer specific responses

## Related
- [[foundation-models]]
- [[data-engineering-for-ai]]
- [[inference-optimization]]
- [[prompt-engineering]]
