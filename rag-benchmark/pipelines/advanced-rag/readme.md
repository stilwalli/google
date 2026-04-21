# Advanced RAG

## What it does
Naive RAG but smarter — rewrites the question first, retrieves more chunks, then reranks by true relevance before answering.

---

## Pipeline

```
User Question
  ↓
Rewrite Question (Gemini)     ← NEW
  ↓
Embed Rewritten Question
  ↓
FAISS finds top 10 chunks     ← wider net than Naive (top 5)
  ↓
Rerank by true relevance      ← NEW
  ↓
Keep top 5
  ↓
Send to Gemini → Answer
```

---

## Two New Steps vs Naive RAG

### Step 1 — Query Rewriting
```
User asks:    "EIC limit?"
Rewritten:    "What is the income limit to qualify for
               Earned Income Credit for tax year 2023?"
```
Better question → better retrieval.

### Step 2 — Reranking
```
FAISS returns 10 chunks (by vector distance)
Gemini scores each chunk 0.0 → 1.0 (by true relevance)
Keep top 5 by relevance score
```
Better chunks → better answer.

---

## Files

| File | Where | Purpose |
|---|---|---|
| `config.py` | root | model names, settings |
| `.env` | root | API key |
| `data/ingest.py` | data/ | build index (run once) |
| `pipelines/advanced-rag/advanced_rag.py` | pipelines/ | run queries |

---

## Run

```bash
python pipelines/advanced-rag/advanced_rag.py
```

---

## Naive RAG vs Advanced RAG

| | Naive RAG | Advanced RAG |
|---|---|---|
| Query | Used as-is | Rewritten by Gemini |
| Retrieval | Top 5 chunks | Top 10 chunks |
| Ranking | Vector distance | True relevance score |
| Quality | Basic | Better |
| Speed | Fast | Slower (more LLM calls) |

---

## Limitation
Reranking calls Gemini once per chunk — slower than Naive RAG.
That tradeoff is acceptable when answer quality matters more than speed.