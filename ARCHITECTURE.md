# Knowledge-Grounded Chatbot Backend

A FastAPI backend for a knowledge-grounded chatbot system with toggleable LLM augmentation.

## Features

- Document ingestion and vector storage (PostgreSQL + pgvector)
- Knowledge Base (KB) only mode - strict retrieval from internal docs
- LLM + KB mode - RAG with Google Gemini
- Session and message persistence
- RESTful API with FastAPI

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- Google Generative AI API key

## Setup

1. Install dependencies:
```bash
pip install -r requirement.txt
```

2. Set up PostgreSQL database with pgvector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE docs (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    metadata JSONB,
    embedding vector(768)
);
```

3. Create `.env` file: