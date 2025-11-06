# ingest_docs.py
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from psycopg2.extras import Json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.db import get_conn

load_dotenv()
GOOGLE_GEN_AI_API_KEY = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GOOGLE_GEN_AI_API_KEY:
    raise RuntimeError("GOOGLE_GENERATIVE_AI_API_KEY or GOOGLE_API_KEY not set in .env")

genai.configure(api_key=GOOGLE_GEN_AI_API_KEY)

def embed_text(text: str):
    """Generate embedding using Google's text-embedding-004 model for documents"""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document"  # Use "retrieval_document" for documents
    )
    return result["embedding"]

def ingest_file(path: str, title: str = None):
    title = title or os.path.basename(path)
    content = open(path, "r", encoding="utf-8").read()
    embedding = embed_text(content)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO docs (title, content, metadata, embedding) VALUES (%s, %s, %s, %s)",
                (title, content, Json({"source": path}), embedding)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    print("Ingested:", title)

if __name__ == "__main__":
    # default file path; adjust as needed
    ingest_file(os.path.join(os.path.dirname(__file__), "..", "data", "imaginary_product_faq.txt"), "Product FAQ")
