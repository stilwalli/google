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

# ── Embed Query ───────────────────────────────────────────────────
def embed_query(query: str) -> np.ndarray:
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
    )
    return np.array(result.embeddings[0].values, dtype=np.float32)

# ── Retrieve ──────────────────────────────────────────────────────
def retrieve(query: str, index, chunks: list, top_k: int = 5) -> list:
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

# ── Compress Each Chunk ───────────────────────────────────────────
def compress_chunk(query: str, chunk: dict) -> dict:
    """
    Ask Gemini to extract ONLY the parts of the chunk
    that are relevant to the question.
    Drops everything else — noise, background, unrelated text.
    """
    prompt = f"""You are a document compression assistant.

Extract ONLY the sentences or phrases from the text below that are 
directly relevant to answering the question.

If nothing in the text is relevant, reply with exactly: "NOT RELEVANT"
Do not add any explanation. Do not answer the question. Just extract.

Question: {query}

Text:
{chunk['text']}

Relevant extract:"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    compressed = response.text.strip()

    return {
        **chunk,
        "original_text":   chunk["text"],
        "compressed_text": compressed,
        "is_relevant":     compressed != "NOT RELEVANT"
    }

# ── Compress All Chunks ───────────────────────────────────────────
def compress_chunks(query: str, chunks: list) -> list:
    """
    Compress each retrieved chunk.
    Filter out chunks marked NOT RELEVANT.
    """
    compressed = []
    print("\n   Compressing chunks:")

    for i, chunk in enumerate(chunks):
        result = compress_chunk(query, chunk)

        original_len   = len(result["original_text"])
        compressed_len = len(result["compressed_text"])

        if result["is_relevant"]:
            print(f"   Chunk {i+1}: {original_len} chars → {compressed_len} chars ✅")
            compressed.append(result)
        else:
            print(f"   Chunk {i+1}: {original_len} chars → NOT RELEVANT ❌ skipped")

    return compressed

# ── Generate ──────────────────────────────────────────────────────
def generate(query: str, chunks: list) -> str:
    # Use compressed text not original
    context = "\n\n".join([c["compressed_text"] for c in chunks])

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

# ── Contextual Compression RAG Pipeline ──────────────────────────
def contextual_compression_rag(query: str) -> dict:
    print(f"\n🔍 Query: {query}")

    index, chunks = load_index()

    # Step 1 — Retrieve
    print("\n📚 Retrieving chunks...")
    retrieved = retrieve(query, index, chunks, top_k=5)
    print(f"   → {len(retrieved)} chunks retrieved")

    # Step 2 — Compress
    print("\n✂️  Compressing chunks...")
    compressed = compress_chunks(query, retrieved)
    print(f"\n   → {len(compressed)} relevant chunks kept")

    if not compressed:
        return {
            "query":      query,
            "answer":     "No relevant information found in the documents.",
            "chunks":     [],
            "pipeline":   "contextual_compression_rag"
        }

    # Step 3 — Generate
    print("\n🤖 Generating answer...")
    answer = generate(query, compressed)

    return {
        "query":    query,
        "answer":   answer,
        "chunks":   compressed,
        "pipeline": "contextual_compression_rag"
    }

# ── Test ──────────────────────────────────────────────────────────
if __name__ == "__main__":

    questions = [
        "What is the income limit to qualify for earned income credit?",
        "Can I claim EIC if I am self employed?",
        "What happens if I claim EIC incorrectly?"
    ]

    for q in questions:
        result = contextual_compression_rag(q)
        print(f"\n{'='*60}")
        print(f"Q: {result['query']}")
        print(f"A: {result['answer']}")
        if result["chunks"]:
            print(f"\nCompressed context sent to Gemini:")
            for c in result["chunks"]:
                print(f"  → {c['compressed_text'][:100]}...")
        print(f"{'='*60}")