# retrieve.py
from app.db import get_conn
import openai, os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def embed_text(text: str):
    resp = openai.Embedding.create(input=[text], model="text-embedding-3-small")
    return resp["data"][0]["embedding"]

def retrieve(query: str, top_k: int = 3):
    q_emb = embed_text(query)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, title, content, metadata, embedding <-> %s AS distance
            FROM docs
            ORDER BY embedding <-> %s
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
