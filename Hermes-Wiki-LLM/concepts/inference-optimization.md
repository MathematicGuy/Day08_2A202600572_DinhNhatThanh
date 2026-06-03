---
title: "Concept: Inference Optimization"
type: concept
aliases: [[Model Optimization]], [[Inference]], [[Quantization]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #inference, #optimization, #deployment]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Inference Optimization

Making model inference cheaper and faster. Chapters 5-8 focus on improving
quality; Chapter 9 focuses on reducing cost and latency.

## Who Needs This
- **API users:** The API provider handles inference optimization
- **Self-hosters:** Must implement many of these techniques — critical
  for anyone hosting open-source or in-house models

## Model-Level Optimization

### Quantization
- Reduce model precision (FP32 → FP16 → INT8 → INT4)
- Dramatically reduces memory and speeds up inference
- Trade-off: lower precision can reduce quality
- Techniques: GPTQ, AWQ, GGUF (for CPU inference)

### Pruning
- Remove less important weights or attention heads
- Reduces model size with minimal quality loss
- Requires careful evaluation after pruning

### Knowledge Distillation
- Train a smaller "student" model to replicate a larger "teacher" model
- Most effective when you can run teacher inference offline for training

### Architecture Optimization
- Flash Attention (faster attention computation)
- KV-cache optimization
- Speculative decoding (use a small model to draft, large model to verify)

## Inference Service-Level Optimization

### Batching
- Process multiple requests together to maximize GPU utilization
- Dynamic batching vs static batching

### Caching
- Cache frequent queries and responses
- Semantic caching (return cached response for semantically similar queries)

### Scaling
- Horizontal scaling (more instances)
- Vertical scaling (bigger GPUs)
- Auto-scaling based on demand

### Serving Frameworks
- vLLM, TensorRT-LLM, TGI (Hugging Face Text Generation Inference)
- Handle kv-cache management, continuous batching, prefix caching

## Monitoring Optimization
- Latency P50/P95/P99
- Throughput (tokens/second)
- Cost per query
- GPU utilization
- Cache hit rate

## Related
- [[fine-tuning]]
- [[foundation-models]]
- [[ai-application-lifecycle]]
- [[evaluating-ai-systems]]
