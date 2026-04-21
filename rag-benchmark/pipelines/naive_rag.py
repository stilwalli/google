import os
import pickle
import numpy as np
import faiss
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Load FAISS index + chunks ─────────────────────────────────────
def load_index():
    index  = faiss.read_index("data/faiss_index.bin")
    with open("data/chunks_metadata.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

# ── Embed the user question ───────────────────────────────────────
def embed_query(query: str) -> np.ndarray:
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=[query],
    )
    return np.array(result.embeddings[0].values, dtype=np.float32)

# ── Retrieve top-k chunks ─────────────────────────────────────────
def retrieve(query: str, index, chunks: list, top_k: int = 5) -> list:
    query_vector = embed_query(query).reshape(1, -1)
    distances, indices = index.search(query_vector, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "text":     chunks[idx]["text"],
            "source":   chunks[idx]["source"],
            "score":    float(distances[0][i])  # L2 distance (lower = better)
        })
    return results

# ── Generate answer ───────────────────────────────────────────────
def generate(query: str, context_chunks: list) -> str:
    # Combine retrieved chunks into context
    context = "\n\n".join([c["text"] for c in context_chunks])
    
    prompt = f"""You are a helpful IRS tax assistant.
Use ONLY the context below to answer the question.
If the answer is not in the context, say "I don't know based on the provided documents."

Context:
{context}

Question: {query}

Answer:"""

    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=prompt,
    )
    return response.text

# ── Naive RAG Pipeline ────────────────────────────────────────────
def naive_rag(query: str) -> dict:
    print(f"\n🔍 Query: {query}")
    
    # Step 1 — Load
    index, chunks = load_index()
    
    # Step 2 — Retrieve
    print("📚 Retrieving chunks...")
    retrieved = retrieve(query, index, chunks, top_k=5)
    print(f"   → {len(retrieved)} chunks retrieved")
    
    # Step 3 — Generate
    print("🤖 Generating answer...")
    answer = generate(query, retrieved)
    
    return {
        "query":     query,
        "answer":    answer,
        "chunks":    retrieved,
        "pipeline":  "naive_rag"
    }

# ── Test it ───────────────────────────────────────────────────────
if __name__ == "__main__":
    
    # Test questions — nuanced IRS policy
    questions = [
        "What is the income limit to qualify for earned income credit?",
        "Can I claim EIC if I am self employed?",
        "What happens if I claim EIC incorrectly?"
    ]
    
    for q in questions:
        result = naive_rag(q)
        print(f"\n{'='*60}")
        print(f"Q: {result['query']}")
        print(f"A: {result['answer']}")
        print(f"Sources: {[c['source'] for c in result['chunks']]}")
        print(f"{'='*60}")