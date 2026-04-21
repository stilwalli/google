import os
import sys
import pickle
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from google import genai
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from config import GEMINI_MODEL, EMBEDDING_MODEL

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Load FAISS + Chunks ───────────────────────────────────────────
def load_index():
    index = faiss.read_index(os.path.join(BASE_DIR, "data", "faiss_index.bin"))
    with open(os.path.join(BASE_DIR, "data", "chunks_metadata.pkl"), "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

# ── Embed Query ───────────────────────────────────────────────────
def embed_query(query: str) -> np.ndarray:
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
    )
    return np.array(result.embeddings[0].values, dtype=np.float32)

# ── Dense Search (FAISS) ──────────────────────────────────────────
def dense_search(query: str, index, chunks: list, top_k: int = 10) -> list:
    """
    Semantic search — finds chunks by meaning.
    Good for: conceptual questions, paraphrased queries.
    """
    query_vector = embed_query(query).reshape(1, -1)
    distances, indices = index.search(query_vector, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "text":         chunks[idx]["text"],
            "source":       chunks[idx]["source"],
            "chunk_id":     chunks[idx]["chunk_id"],
            "dense_score":  1 / (1 + float(distances[0][i])),  # convert distance to score
            "sparse_score": 0.0
        })
    return results

# ── Sparse Search (BM25) ──────────────────────────────────────────
def sparse_search(query: str, chunks: list, top_k: int = 10) -> list:
    """
    Keyword search — finds chunks by exact word matches.
    Good for: specific numbers, exact terms, named entities.
    """
    # Tokenize all chunks
    tokenized_chunks = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized_chunks)

    # Score all chunks against query
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Get top_k indexes
    top_indexes = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indexes:
        results.append({
            "text":         chunks[idx]["text"],
            "source":       chunks[idx]["source"],
            "chunk_id":     chunks[idx]["chunk_id"],
            "dense_score":  0.0,
            "sparse_score": float(scores[idx])
        })
    return results

# ── Combine Results (Reciprocal Rank Fusion) ──────────────────────
def combine_results(dense: list, sparse: list, top_k: int = 5) -> list:
    """
    Reciprocal Rank Fusion (RRF) — merges two ranked lists fairly.
    Each chunk gets a score based on its rank in both lists.
    RRF formula: score = 1/(rank + 60)

    Why 60? It's a constant that dampens the impact of very high ranks.
    Standard value used in information retrieval research.
    """
    k = 60
    chunk_scores = {}  # chunk_id → combined score
    chunk_data   = {}  # chunk_id → chunk dict

    # Score dense results by rank
    for rank, chunk in enumerate(dense):
        cid = chunk["chunk_id"]
        chunk_scores[cid] = chunk_scores.get(cid, 0) + 1 / (rank + k)
        chunk_data[cid]   = chunk

    # Score sparse results by rank
    for rank, chunk in enumerate(sparse):
        cid = chunk["chunk_id"]
        chunk_scores[cid] = chunk_scores.get(cid, 0) + 1 / (rank + k)
        chunk_data[cid]   = chunk

    # Sort by combined score
    sorted_ids = sorted(chunk_scores, key=lambda x: chunk_scores[x], reverse=True)

    results = []
    for cid in sorted_ids[:top_k]:
        chunk = chunk_data[cid]
        chunk["rrf_score"] = chunk_scores[cid]
        results.append(chunk)

    return results

# ── Generate ──────────────────────────────────────────────────────
def generate(query: str, chunks: list) -> str:
    context = "\n\n".join([c["text"] for c in chunks])

    prompt = f"""You are a helpful IRS tax assistant.
Use ONLY the context below to answer the question.
If the answer is not in the context, say "I don't know based on the provided documents."

Context:
{context}

Question: {query}

Answer:"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    return response.text

# ── Hybrid RAG Pipeline ───────────────────────────────────────────
def hybrid_rag(query: str) -> dict:
    print(f"\n🔍 Query: {query}")

    index, chunks = load_index()

    # Step 1 — Dense search (semantic)
    print("\n🧠 Dense search (FAISS)...")
    dense_results = dense_search(query, index, chunks, top_k=10)
    print(f"   → {len(dense_results)} chunks")

    # Step 2 — Sparse search (keywords)
    print("\n🔤 Sparse search (BM25)...")
    sparse_results = sparse_search(query, chunks, top_k=10)
    print(f"   → {len(sparse_results)} chunks")

    # Step 3 — Combine with RRF
    print("\n🔀 Combining with Reciprocal Rank Fusion...")
    combined = combine_results(dense_results, sparse_results, top_k=5)
    print(f"   → {len(combined)} chunks after fusion")

    print("\n   RRF scores:")
    for c in combined:
        print(f"   {c['rrf_score']:.4f} → {c['text'][:60]}...")

    # Step 4 — Generate
    print("\n🤖 Generating answer...")
    answer = generate(query, combined)

    return {
        "query":    query,
        "answer":   answer,
        "chunks":   combined,
        "pipeline": "hybrid_rag"
    }

# ── Test ──────────────────────────────────────────────────────────
if __name__ == "__main__":

    questions = [
        "What is the income limit to qualify for earned income credit?",
        "Can I claim EIC if I am self employed?",
        "What happens if I claim EIC incorrectly?"
    ]

    for q in questions:
        result = hybrid_rag(q)
        print(f"\n{'='*60}")
        print(f"Q: {result['query']}")
        print(f"A: {result['answer']}")
        print(f"{'='*60}")