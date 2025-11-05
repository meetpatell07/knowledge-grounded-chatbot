# ingest_docs.py
import os
from dotenv import load_dotenv
import openai
from psycopg2.extras import Json
from app.db import get_conn

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY not set in .env")

def embed_text(text: str):
    resp = openai.Embedding.create(input=[text], model="text-embedding-3-small")
    return resp["data"][0]["embedding"]

def ingest_file(path: str, title: str = None):
    title = title or os.path.basename(path)
    content = open(path, "r", encoding="utf-8").read()
    embedding = embed_text(content)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO docs (title, content, metadata, embedding) VALUES (%s, %s, %s, %s)",
            (title, content, Json({"source": path}), embedding)
        )
    conn.commit()
    conn.close()
    print("Ingested:", title)

if __name__ == "__main__":
    # default file path; adjust as needed
    ingest_file(os.path.join(os.path.dirname(__file__), "..", "..", "data", "internal_faq.txt"), "Internal FAQ")
