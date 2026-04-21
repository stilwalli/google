# Contextual Compression RAG

## What it does
Retrieves chunks like Naive RAG, but compresses each chunk before sending to Gemini — keeping only the parts relevant to the question.

---

## Pipeline

```
User Question
  ↓
Retrieve top 5 chunks (FAISS)
  ↓
For each chunk:
  Gemini extracts only relevant sentences
  ↓
  512 chars → ~50 chars (or skip if NOT RELEVANT)
  ↓
Send compressed chunks to Gemini → Answer
```

---

## The Key Step — Compression

```
BEFORE compression (512 chars):
"The Earned Income Credit was introduced in 1975...
 It is a refundable credit for low income workers...
 For 2023, the limit for single filers is $17,640...   ← useful
 The credit was expanded several times over decades..."

AFTER compression (~20 chars):
"For 2023, the limit for single filers is $17,640"
```

Noise removed. Only the answer stays.

---

## Files

| File | Where | Purpose |
|---|---|---|
| `config.py` | root | model names, settings |
| `.env` | root | API key |
| `data/ingest.py` | data/ | build index (run once) |
| `pipelines/contextual-compression-rag/contextual_compression_rag.py` | pipelines/ | run queries |

---

## Run

```bash
python pipelines/contextual-compression-rag/contextual_compression_rag.py
```

---

## Comparison

| | Naive RAG | Contextual Compression RAG |
|---|---|---|
| Retrieval | Top 5 chunks | Top 5 chunks |
| What's sent to Gemini | Full chunks (noisy) | Compressed chunks (clean) |
| Irrelevant chunks | Included | Filtered out |
| Answer quality | Good | Better |
| Speed | Fast | Slower (compression step) |

---

## Why It Matters
Less noise in the prompt = Gemini focuses on what matters = more precise answers.