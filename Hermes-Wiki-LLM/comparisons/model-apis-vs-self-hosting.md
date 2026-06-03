---
title: "Comparison: Model APIs vs Self-Hosting"
type: comparison
aliases: [[API vs Self-Host]], [[Model Deployment Options]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 0.9
tags: [#comparison, #deployment, #architecture, #inference]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Model APIs vs Self-Hosting

Based on Chapter 4 of *AI Engineering* — whether to use commercial model
APIs or host models yourself is a recurring decision most teams face.

## Comparison Table

| Dimension | Model APIs | Self-Hosting |
|-----------|-----------|--------------|
| **Data Privacy** | Must send data to provider (leak risk) | Data stays in-house |
| **Performance** | Best model likely API-only (~top 5%) | Good, but model ceiling lower |
| **Cost** | Predictable per-query; expensive at scale | High upfront (GPUs), cheaper at volume |
| **Engineering Effort** | Minimal — provider handles scaling | Significant — infrastructure, ops, optimization |
| **Control** | Subject to provider terms, rate limits, roadmap | Full control (freeze versions, modify) |
| **Safety Guardrails** | Provider-managed (may over-censor) | Self-managed (flexible but your responsibility) |
| **On-Device** | Not possible | Required (edge, mobile, offline) |
| **Reliability** | Depends on provider SLA | Depends on your engineering |
| **Model Updates** | Provider updates — may break prompts | You decide when to update |
| **Customizability** | Limited to API surface | Full — fine-tuning, architecture changes |
| **Transparency** | Often opaque (training data, changes) | Complete visibility |

## Decision Framework

**Choose APIs when:**
- You're prototyping or have low volume
- The best model for your task is proprietary (GPT-4, Claude, Gemini)
- Engineering resources are limited
- Data privacy requirements are satisfied by the provider
- Latency isn't ultra-critical

**Choose Self-Hosting when:**
- You need data privacy (regulated industries, sensitive data)
- Volume is high enough that API costs exceed hosting costs
- You need on-device deployment
- You require full control over model behavior
- Your use case needs modifications the provider won't support

## Hybrid Approaches
- Start with APIs for prototyping, migrate to self-hosting at scale
- Use APIs for the most powerful model, self-host smaller models
- Model API services built on top of open-source models offer middle ground

## Related
- [[evaluating-ai-systems]]
- [[inference-optimization]]
- [[ai-application-lifecycle]]
- [[ai-engineering-overview]]
