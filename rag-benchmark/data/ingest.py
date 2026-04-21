import os
import pickle
import requests
import numpy as np
import faiss
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

IRS_DOCS = {
    "pub970": "https://www.irs.gov/pub/irs-pdf/p596.pdf",  # Tax Benefits for Education ~90 pages
}

CHUNK_SIZE    = 512
CHUNK_OVERLAP = 50

# ── Parse PDF ─────────────────────────────────────────────────────
def parse_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages  = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text  = text.replace("\x00", "")
            lines = [l for l in text.split("\n") if len(l.strip()) > 30]
            pages.append("\n".join(lines))
    return "\n\n".join(pages)

# ── Chunk ─────────────────────────────────────────────────────────
def chunk_text(text: str) -> list[str]:
    chunks = []
    start  = 0
    length = len(text)
    while start < length:
        end = start + CHUNK_SIZE
        if end < length:
            para = text.rfind("\n\n", start, end)
            if para != -1 and para > start + CHUNK_SIZE // 2:
                end = para
            else:
                sent = text.rfind(". ", start, end)
                if sent != -1 and sent > start + CHUNK_SIZE // 2:
                    end = sent + 1
                else:
                    word = text.rfind(" ", start, end)
                    if word != -1:
                        end = word
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - CHUNK_OVERLAP
    return chunks

# ── Embed ─────────────────────────────────────────────────────────
def embed_chunks(chunks: list[str]) -> list[list[float]]:
    embeddings = []
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch  = chunks[i:i + batch_size]
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=batch,
        )
        embeddings.extend([e.values for e in result.embeddings])
        print(f"  Embedded {min(i+batch_size, len(chunks))}/{len(chunks)}")
    return embeddings

# ── Build FAISS ───────────────────────────────────────────────────
def build_index(embeddings: list[list[float]]) -> faiss.IndexFlatL2:
    dim     = len(embeddings[0])
    index   = faiss.IndexFlatL2(dim)
    vectors = np.array(embeddings, dtype=np.float32)
    index.add(vectors)
    return index

# ── Main ──────────────────────────────────────────────────────────
def main():
    print("\n🚀 Starting Ingestion\n")

    os.makedirs("data/raw", exist_ok=True)

    # Download PDFs
    for name, url in IRS_DOCS.items():
        path = f"data/raw/{name}.pdf"
        if os.path.exists(path):
            print(f"✅ Already exists: {path}")
            continue
        print(f"⬇️  Downloading {name}...")
        r = requests.get(url, timeout=60)
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"✅ Saved {path}")

    all_chunks = []

    # Parse + chunk
    for name in IRS_DOCS:
        path = f"data/raw/{name}.pdf"
        print(f"\n📄 Processing {name}...")
        text   = parse_pdf(path)
        chunks = chunk_text(text)
        print(f"   → {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text":     chunk,
                "source":   name,
                "chunk_id": i
            })

    print(f"\n📦 Total chunks: {len(all_chunks)}")

    # Embed
    print("\n🔢 Embedding with Gemini...")
    texts      = [c["text"] for c in all_chunks]
    embeddings = embed_chunks(texts)

    # Save
    print("\n🗂️  Building FAISS index...")
    index = build_index(embeddings)
    faiss.write_index(index, "data/faiss_index.bin")
    with open("data/chunks_metadata.pkl", "wb") as f:
        pickle.dump(all_chunks, f)

    print("\n✅ Ingestion complete!")
    print("   → data/faiss_index.bin")
    print("   → data/chunks_metadata.pkl")

if __name__ == "__main__":
    main()