---
title: "Concept: Prompt Engineering"
type: concept
aliases: [[Prompting]], [[In-Context Learning]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #prompt-engineering, #inference]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# Prompt Engineering

The practice of crafting input instructions (prompts) to steer a model's
behavior without modifying its weights. A foundational technique in AI
engineering — often the first thing to try before RAG or fine-tuning.

## Why It Works
- Models learn patterns from training data; prompts activate relevant
  patterns and suppress irrelevant ones
- **In-context learning:** the model uses examples in the prompt to infer
  the desired output format and reasoning
- Prompt format and structure significantly influence output quality

## Best Practices
- Be specific and explicit — vague prompts produce vague outputs
- Use clear formatting (numbered lists, sections, delimiters)
- Provide examples (few-shot) for complex tasks
- Decompose complex tasks into steps (chain-of-thought)
- Iterate — test and refine prompts systematically
- Start with the strongest model to evaluate feasibility, then work backward
  to smaller models

## Common Techniques
- **Zero-shot:** Task description only, no examples
- **Few-shot:** Include examples of inputs and desired outputs
- **Chain-of-thought:** Ask the model to reason step by step
- **Role prompting:** Assign a persona (e.g., "you are a helpful assistant")
- **Structured output:** Specify JSON format, markdown, or other schemas

## Prompt Attacks and Defense
Bad actors can exploit applications through:
- **Prompt injection:** Override system instructions with user-supplied
  content
- **Jailbreaking:** Bypass safety guardrails via creative prompting
- **Leaking:** Extract system prompts or proprietary instructions

Defense strategies:
- Input sanitization and content filtering
- Separate system and user prompts
- Rate limiting and anomaly detection
- Robust output validation

## Relationship to Other Techniques
- Prompt engineering is the **easiest, cheapest** adaptation method
- Best used before investing in RAG or fine-tuning
- Can be combined with RAG (prompt + retrieved context) and fine-tuning
  (base behavior shaped by weights, further steered by prompts)

## Related
- [[rag-and-agents]]
- [[fine-tuning]]
- [[foundation-models]]
- [[ai-engineering-overview]]
