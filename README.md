# Knowledge-Grounded Chatbot Backend

A FastAPI backend for a knowledge-grounded chatbot system with toggleable LLM augmentation. This system leverages a private, internal document knowledge base for primary responses, with an option to consult Google Gemini for general or supplementary inquiries.

## 🎯 Features

- **Document Ingestion**: Process and embed documents using Google's text-embedding-004 model
- **Vector Storage**: PostgreSQL with pgvector extension for efficient similarity search
- **Dual Response Modes**:
  - **KB Only Mode**: Strict retrieval from internal documents (no LLM calls)
  - **LLM + KB Mode**: RAG (Retrieval-Augmented Generation) with Google Gemini
- **Session Management**: Persistent conversation history with session tracking
- **Toggle Control**: User-controlled switching between KB-only and LLM-augmented responses
- **RESTful API**: Clean FastAPI endpoints with proper error handling

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **PostgreSQL**: 12+ with pgvector extension installed
- **Google Generative AI API Key**: Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirement.txt
```

### 2. Set Up PostgreSQL Database

First, ensure PostgreSQL is installed and the pgvector extension is available:

```bash
# Install pgvector extension (example for Ubuntu/Debian)
sudo apt-get install postgresql-14-pgvector

# Or for macOS with Homebrew
brew install pgvector
```

Create a database and enable the extension:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE kg_chatbot;

-- Connect to the database
\c kg_chatbot

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table for vector storage
CREATE TABLE docs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768)
);

-- Create index for faster similarity search
CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops);
```

### 3. Create Environment File

Create a `.env` file in the `backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/kg_chatbot

# Google Generative AI API Key
GOOGLE_GENERATIVE_AI_API_KEY=your_api_key_here
# Alternative: GOOGLE_API_KEY=your_api_key_here
```

**Note**: Replace `username`, `password`, and `your_api_key_here` with your actual credentials.

### 4. Ingest Documents

Before running the API, you need to ingest your knowledge base documents:

```bash
# From the backend directory
python -m app.ingest_docs
```

This will process the document in `data/imaginary_product_faq.txt` and store it in the vector database.

### 5. Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints

#### `POST /chat`

Send a message to the chatbot and get a response.

**Request Body:**
```json
{
  "message": "What is ImaginaryProduct?",
  "enable_llm": false,
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "reply": "Based on internal docs:\n\n...",
  "source": "KB",
  "session_id": "uuid-here"
}
```

**Parameters:**
- `message` (string, required): The user's question or message
- `enable_llm` (boolean, optional, default: `false`): Toggle for LLM augmentation
  - `false`: KB-only mode (strict retrieval from documents)
  - `true`: LLM + KB mode (RAG with Gemini)
- `session_id` (string, optional): Session ID for conversation continuity

**Source Values:**
- `"KB"`: Response from Knowledge Base only
- `"KB+LLM"`: Response augmented with LLM (has KB context)
- `"LLM"`: Response from LLM only (no KB context found)

#### `GET /health`

Health check endpoint to verify server and database connectivity.

**Response:**
```json
{
  "status": "ok",
  "database": "connected"
}
```

#### `GET /sessions`

Get all chat sessions with their messages.

**Response:**
```json
[
  {
    "id": "session-uuid",
    "userId": null,
    "createdAt": "2024-01-01T00:00:00",
    "lastActive": "2024-01-01T00:00:00",
    "messages": [...]
  }
]
```

#### `GET /sessions/{session_id}/messages`

Get all messages for a specific session.

**Response:**
```json
[
  {
    "id": "message-uuid",
    "sessionId": "session-uuid",
    "role": "user",
    "content": "Hello",
    "source": null,
    "createdAt": "2024-01-01T00:00:00"
  }
]
```

#### `POST /sessions`

Create a new session or get an existing one.

**Request Body:**
```json
{
  "sessionId": "optional-session-id"
}
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and routes
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database configuration (SQLAlchemy)
│   ├── graph_logic.py       # LangGraph workflow for chat logic
│   ├── retrieve.py          # Vector retrieval functions
│   └── ingest_docs.py       # Document ingestion script
├── data/
│   └── imaginary_product_faq.txt  # Sample knowledge base document
├── repositories/            # Repository pattern (optional)
├── requirement.txt          # Python dependencies
├── ARCHITECTURE.md          # Architecture documentation
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `GOOGLE_GENERATIVE_AI_API_KEY` | Google AI API key | Yes |
| `GOOGLE_API_KEY` | Alternative name for API key | Yes (if above not set) |

### Database Models

- **Session**: Stores conversation sessions
- **Message**: Stores individual messages with source tracking
- **docs**: Vector table for document embeddings (created via SQL)

## 🧠 How It Works

### KB Only Mode (`enable_llm=false`)

1. User sends a message with `enable_llm: false`
2. System retrieves relevant documents using vector similarity search
3. Returns the retrieved context directly (no LLM processing)
4. Source is marked as `"KB"`

### LLM + KB Mode (`enable_llm=true`)

1. User sends a message with `enable_llm: true`
2. System retrieves relevant documents using vector similarity search
3. If similarity is high (distance < 0.35), uses KB-only response
4. Otherwise, sends retrieved context + user query to Gemini LLM
5. LLM generates an augmented response
6. Source is marked as `"KB+LLM"` or `"LLM"` depending on context availability

### Routing Logic

The system uses LangGraph to manage the chat workflow:
- **Retrieve Node**: Performs vector similarity search
- **Evaluate Node**: Routes based on `enable_llm` flag and similarity threshold
- **KB Only Node**: Returns raw document context
- **LLM Augmented Node**: Calls Gemini API with context

## 🧪 Testing

Test the API using curl:

```bash
# Health check
curl http://localhost:8000/health

# Send a message (KB only)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is ImaginaryProduct?", "enable_llm": false}'

# Send a message (LLM enabled)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about pricing", "enable_llm": true}'
```

## 🐛 Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running: `pg_isready`
- Check `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Ensure pgvector extension is installed: `SELECT * FROM pg_extension WHERE extname = 'vector';`

### API Key Issues

- Verify your Google API key is valid
- Check that the key has access to Generative AI models
- Ensure the key is set in `.env` file

### Vector Search Issues

- Verify documents are ingested: `SELECT COUNT(*) FROM docs;`
- Check embedding dimensions match (should be 768 for text-embedding-004)
- Ensure vector index is created for performance

## 📖 Additional Documentation

- See `ARCHITECTURE.md` for detailed architecture overview
- API documentation available at `/docs` when server is running


