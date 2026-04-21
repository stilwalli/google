# Hybrid RAG

## What it does
Combines semantic search (FAISS) and keyword search (BM25) to get the best of both worlds.

---

## Pipeline

```
User Question
  ↓
Run both searches in parallel
  ↓
Dense Search (FAISS)    +    Sparse Search (BM25)
semantic meaning              exact keywords
  ↓                                ↓
        Combine with RRF
        (Reciprocal Rank Fusion)
  ↓
Top 5 best chunks
  ↓
Gemini → Answer
```

---

## Two Search Types

### Dense Search (FAISS)
```
Finds by meaning
"how much can I earn" → finds "income limit for EIC"
Good for: concepts, paraphrased questions
```

### Sparse Search (BM25)
```
Finds by exact words
"$10,300 investment income" → finds "$10,300" instantly
Good for: numbers, specific terms, named entities
```

---

## How RRF Works
```
Each chunk gets a score based on rank in both lists:
score = 1/(rank + 60)

Dense rank 1  → 1/61 = 0.0164
Sparse rank 1 → 1/61 = 0.0164
Combined      → 0.0328  ← appears in both = higher score
```
Chunks that appear in both lists rank highest.

---

## Files

| File | Where | Purpose |
|---|---|---|
| `config.py` | root | model names, settings |
| `.env` | root | API key |
| `data/ingest.py` | data/ | build index (run once) |
| `pipelines/hybrid-rag/hybrid_rag.py` | pipelines/ | run queries |

---

## Run

```bash
python pipelines/hybrid-rag/hybrid_rag.py
```

---

## Comparison

| | Naive RAG | Advanced RAG | Hybrid RAG |
|---|---|---|---|
| Search | Semantic | Semantic | Semantic + Keyword |
| Query | As-is | Rewritten | As-is |
| Ranking | Vector distance | Relevance score | RRF fusion |
| Best for | General questions | Vague questions | Specific terms/numbers |

---

## Extra Dependency
```
rank-bm25    ← keyword search library
```
