import os
import sys
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from pipelines.naive_rag.naive_rag                               import naive_rag
from pipelines.advanced_rag.advanced_rag                         import advanced_rag
from pipelines.hybrid_rag.hybrid_rag                             import hybrid_rag
from pipelines.contextual_compression_rag.contextual_compression_rag import contextual_compression_rag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def serve_dashboard():
    return FileResponse(os.path.join(BASE_DIR, "dashboard", "rag_compare.html"))

@app.post("/run/naive")
def run_naive(req: QueryRequest):
    start  = time.time()
    result = naive_rag(req.question)
    return {
        "answer":   result["answer"],
        "pipeline": "naive_rag",
        "ms":       int((time.time() - start) * 1000)
    }

@app.post("/run/advanced")
def run_advanced(req: QueryRequest):
    start  = time.time()
    result = advanced_rag(req.question)
    return {
        "answer":   result["answer"],
        "pipeline": "advanced_rag",
        "ms":       int((time.time() - start) * 1000)
    }

@app.post("/run/hybrid")
def run_hybrid(req: QueryRequest):
    start  = time.time()
    result = hybrid_rag(req.question)
    return {
        "answer":   result["answer"],
        "pipeline": "hybrid_rag",
        "ms":       int((time.time() - start) * 1000)
    }

@app.post("/run/compression")
def run_compression(req: QueryRequest):
    start  = time.time()
    result = contextual_compression_rag(req.question)
    return {
        "answer":   result["answer"],
        "pipeline": "contextual_compression_rag",
        "ms":       int((time.time() - start) * 1000)
    }