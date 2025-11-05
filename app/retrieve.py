# retrieve.py
from app.db import get_conn
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_GEN_AI_API_KEY = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GOOGLE_GEN_AI_API_KEY:
    raise RuntimeError("GOOGLE_GENERATIVE_AI_API_KEY or GOOGLE_API_KEY not set in .env")

genai.configure(api_key=GOOGLE_GEN_AI_API_KEY)

def embed_text(text: str):
    """Generate embedding using Google's text-embedding-004 model"""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query"  # Use "retrieval_document" for documents
    )
    return result["embedding"]

def retrieve(query: str, top_k: int = 3):
    q_emb = embed_text(query)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, title, content, metadata, embedding <-> %s::vector AS distance
            FROM docs
            ORDER BY embedding <-> %s::vector
            LIMIT %s;
        """, (q_emb, q_emb, top_k))
        rows = cur.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "title": r[1],
            "content": r[2],
            "metadata": r[3],
            "distance": float(r[4])
        })
    return results
