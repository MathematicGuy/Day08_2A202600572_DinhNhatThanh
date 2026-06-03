---
title: "Concept: RAG and Agentic Patterns"
type: concept
aliases: [[RAG]], [[Retrieval-Augmented Generation]], [[AI Agents]], [[Agentic]]
created_at: 2026-06-01
updated_at: 2026-06-01
confidence: 1.0
tags: [#concept, #rag, #agent, #architecture]
sources: [raw/articles/ai-engineering-chip-huyen.md]
---

# RAG and Agentic Patterns

Both patterns address the same core need: providing context to a model so it
can generate accurate, grounded responses. They differ in how context is
constructed and used.

## Why Context Matters
- A model's knowledge is frozen at training time — it can't access
  new or proprietary information without external context
- Without context, models hallucinate, produce outdated information, or
  fail on domain-specific queries
- Providing the right context is often more impactful than changing the
  model itself

## RAG (Retrieval-Augmented Generation)
**Status:** Better understood, proven in production.

How it works:
1. User query comes in
2. Retrieve relevant documents/chunks from a knowledge base
3. Insert retrieved context into the prompt
4. Model generates response grounded in the context

Key components:
- **Retrieval:** Vector search, keyword search, hybrid search
- **Chunking strategy:** Document splitting affects retrieval quality
- **Re-ranking:** Improve relevance of top results
- **Context window management:** Fit within the model's token limit

Strengths:
- Grounds model in verifiable sources
- Knowledge base is easy to update (ingest/remove documents)
- Transparent — you can trace which sources informed the response

## Agentic Pattern
**Status:** More powerful but more complex and still being explored.

How it works:
- The model doesn't just answer — it reasons, plans, and takes actions
- Can use tools (APIs, databases, code execution, search)
- Maintains state and memory across steps
- Can iterate: act → observe → reason → act again

Capabilities:
- Multi-step reasoning and problem decomposition
- Tool use and API calling
- Self-correction based on feedback
- Dynamic context gathering

Challenges:
- Complex to build and debug
- Expensive (many model calls per task)
- Unpredictable behavior in edge cases
- Safety concerns (autonomous actions)

## Choosing Between RAG and Agents
- **RAG first** — simpler, more reliable, good for knowledge-intensive tasks
- **Agent when needed** — when the task requires dynamic exploration,
  tool use, or multi-step planning
- Many applications use both: RAG for grounding, agentic for execution

## Related
- [[prompt-engineering]]
- [[fine-tuning]]
- [[evaluating-ai-systems]]
- [[ai-application-lifecycle]]
