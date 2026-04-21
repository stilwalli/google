# Naive RAG

## What it does
Find relevant document chunks → show to LLM → get answer.

---

## Pipeline

```
IRS PDF
  ↓
Cut into chunks (512 chars)
  ↓
Convert chunks to numbers (embed)
  ↓
Save to FAISS + Pickle
  ↓

User asks question
  ↓
Convert question to numbers
  ↓
FAISS finds 5 closest chunks
  ↓
Send chunks + question to Gemini
  ↓
Answer
```

---

## FAISS vs Pickle

```
FAISS (faiss_index.bin)
  → stores vectors (numbers)
  → used for search

Pickle (chunks_metadata.pkl)
  → stores text
  → used to fetch actual content

They link by position:
  FAISS[42] ←→ Pickle[42]
  (numbers)     (text)
```

---

## Files

| File | Where | Purpose |
|---|---|---|
| `config.py` | root | settings |
| `.env` | root | API key |
| `data/ingest.py` | data/ | build index |
| `pipelines/naive_rag.py` | pipelines/ | run queries |

---

## Run

```bash
python data/ingest.py         # once
python pipelines/naive_rag.py # every query
```

---

## Limitation

Blindly trusts retrieval — no reranking, no query rewriting.
That is what Advanced RAG fixes.