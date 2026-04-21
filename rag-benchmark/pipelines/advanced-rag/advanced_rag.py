import os
import sys
import pickle
import numpy as np
import faiss
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

# ── Step 1: Query Rewriting ───────────────────────────────────────
def rewrite_query(query: str) -> str:
    prompt = f"""You are a search query optimizer for IRS tax documents.

Rewrite the following question into a detailed search query that will
retrieve the most relevant IRS policy information.

Original question: {query}

Rules:
- Be specific and detailed
- Include relevant tax terminology
- Keep it as one sentence
- Do not answer the question, just rewrite it

Rewritten query:"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    rewritten = response.text.strip()
    print(f"   Original:  {query}")
    print(f"   Rewritten: {rewritten}")
    return rewritten

# ── Step 2: Embed Query ───────────────────────────────────────────
def embed_query(query: str) -> np.ndarray:
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
    )
    return np.array(result.embeddings[0].values, dtype=np.float32)

# ── Step 3: Retrieve ──────────────────────────────────────────────
def retrieve(query: str, index, chunks: list, top_k: int = 10) -> list:
    query_vector = embed_query(query).reshape(1, -1)
    distances, indices = index.search(query_vector, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "text":   chunks[idx]["text"],
            "source": chunks[idx]["source"],
            "score":  float(distances[0][i])
        })
    return results

# ── Step 4: Reranking ─────────────────────────────────────────────
def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    scored_chunks = []

    for chunk in chunks:
        prompt = f"""Score how relevant this text is for answering the question.

Question: {query}

Text: {chunk['text']}

Reply with ONLY a number between 0 and 1.
1.0 = perfectly relevant
0.0 = completely irrelevant

Score:"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        try:
            score = float(response.text.strip())
        except:
            score = 0.0

        scored_chunks.append({
            **chunk,
            "relevance_score": score
        })

    reranked = sorted(scored_chunks, key=lambda x: x["relevance_score"], reverse=True)

    print(f"\n   Reranking scores:")
    for c in reranked:
        print(f"   {c['relevance_score']:.2f} → {c['text'][:60]}...")

    return reranked[:top_k]

# ── Step 5: Generate ──────────────────────────────────────────────
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

# ── Advanced RAG Pipeline ─────────────────────────────────────────
def advanced_rag(query: str) -> dict:
    print(f"\n🔍 Query: {query}")

    index, chunks = load_index()

    # Step 1 — Rewrite
    print("\n✏️  Rewriting query...")
    rewritten_query = rewrite_query(query)

    # Step 2 — Retrieve top 10
    print("\n📚 Retrieving chunks (top 10)...")
    retrieved = retrieve(rewritten_query, index, chunks, top_k=10)
    print(f"   → {len(retrieved)} chunks retrieved")

    # Step 3 — Rerank to top 5
    print("\n🎯 Reranking...")
    reranked = rerank(query, retrieved, top_k=5)
    print(f"   → {len(reranked)} chunks after reranking")

    # Step 4 — Generate
    print("\n🤖 Generating answer...")
    answer = generate(query, reranked)

    return {
        "query":           query,
        "rewritten_query": rewritten_query,
        "answer":          answer,
        "chunks":          reranked,
        "pipeline":        "advanced_rag"
    }

# ── Test ──────────────────────────────────────────────────────────
if __name__ == "__main__":

    questions = [
        "What is the income limit to qualify for earned income credit?",
        "Can I claim EIC if I am self employed?",
        "What happens if I claim EIC incorrectly?"
    ]

    for q in questions:
        result = advanced_rag(q)
        print(f"\n{'='*60}")
        print(f"Q:         {result['query']}")
        print(f"Rewritten: {result['rewritten_query']}")
        print(f"A:         {result['answer']}")
        print(f"{'='*60}")