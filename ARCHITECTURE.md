# Backend Architecture

This document explains the backend architecture, technology choices, and the logic for switching between Knowledge Base (KB) only and LLM-augmented response pathways.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                           │
│                    (app/main.py)                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  REST API Endpoints                                       │   │
│  │  - POST /chat                                             │   │
│  │  - GET /sessions                                         │   │
│  │  - DELETE /sessions/{id}                                 │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Chat Handler (app/graph_logic.py)                       │   │
│  │  handle_chat(session_id, message, enable_llm)            │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph Workflow                                       │   │
│  │                                                           │   │
│  │  START                                                    │   │
│  │    │                                                      │   │
│  │    ▼                                                      │   │
│  │  retrieve_node                                           │   │
│  │    ├─► embed_query(query)                                │   │
│  │    │   └─► Google text-embedding-004                      │   │
│  │    ├─► vector_search(query_embedding)                     │   │
│  │    │   └─► PostgreSQL pgvector                           │   │
│  │    └─► state["context"] = retrieved_docs                 │   │
│  │    │                                                      │   │
│  │    ▼                                                      │   │
│  │  evaluate_node(state)                                     │   │
│  │    ├─► Check enable_llm flag                             │   │
│  │    └─► Route decision                                    │   │
│  │         │                                                 │   │
│  │         ├──────────────┬──────────────────┐              │   │
│  │         │              │                  │              │   │
│  │         ▼              ▼                  ▼              │   │
│  │    kb_only_node   llm_augmented_node   (if distance      │   │
│  │         │              │                  < 0.35)        │   │
│  │         └──────────────┴──────────────────┘              │   │
│  │                  │                                        │   │
│  │                  ▼                                        │   │
│  │                END                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Vector Retrieval (app/retrieve.py)                       │   │
│  │  - Embed query using Google text-embedding-004             │   │
│  │  - PostgreSQL pgvector similarity search                   │   │
│  │  - Return top_k similar documents                          │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LLM Service (Google Gemini)                              │   │
│  │  - gemini-2.5-flash for response generation              │   │
│  │  - text-embedding-004 for embeddings                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Database Layer                                           │   │
│  │  ┌──────────────────┐  ┌──────────────────┐                │   │
│  │  │ PostgreSQL       │  │ PostgreSQL       │                │   │
│  │  │ + pgvector       │  │ (SQLAlchemy)    │                │   │
│  │  │                  │  │                  │                │   │
│  │  │ docs table       │  │ sessions table  │                │   │
│  │  │ - embedding      │  │ messages table  │                │   │
│  │  │   (vector 768)   │  │                  │                │   │
│  │  └──────────────────┘  └──────────────────┘                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Justification

### Python

**Why Python?**

- **AI/ML Ecosystem**: Extensive libraries for AI, NLP, and machine learning
- **Rapid Development**: Clean syntax enables fast prototyping and iteration
- **Community Support**: Large community with extensive documentation and resources
- **Integration**: Excellent integration with AI services (Google Gemini, OpenAI, etc.)
- **Data Science**: Strong support for data processing, embeddings, and vector operations
- **Maturity**: Well-established ecosystem for production AI applications

**Alternatives Considered**: Node.js, Go, Java
- **Rejected**: Python has superior AI/ML ecosystem, better integration with embedding models, and more mature libraries for vector operations

### FastAPI

**Why FastAPI?**

- **Performance**: High performance, comparable to Node.js and Go frameworks
- **Type Safety**: Built-in Pydantic validation provides TypeScript-like type safety
- **Async Support**: Native async/await support for concurrent operations
- **Auto Documentation**: Automatic OpenAPI/Swagger documentation generation
- **Modern Python**: Built for modern Python with type hints and async/await
- **Developer Experience**: Excellent IDE support, clear error messages, fast development
- **Standards**: Based on OpenAPI standards, easy integration with frontend

**Alternatives Considered**: Flask, Django, Express.js
- **Rejected**: 
  - Flask: Less performant, no built-in async support, requires more boilerplate
  - Django: Heavier framework, overkill for API-only application
  - Express.js: Would require Node.js, less suitable for AI/ML workloads

### PostgreSQL + pgvector

**Why PostgreSQL with pgvector Extension?**

- **Vector Search**: Native vector similarity search with pgvector extension
- **Production Ready**: Robust, ACID-compliant, battle-tested database
- **Scalability**: Handles large datasets efficiently with proper indexing
- **Unified Storage**: Same database for vectors and relational data (sessions, messages)
- **Full-Text Search**: Can combine vector search with traditional SQL queries
- **Reliability**: Enterprise-grade reliability and data integrity
- **Cost-Effective**: Open-source, no licensing fees
- **Integration**: Works seamlessly with SQLAlchemy ORM
- **Mature Extension**: pgvector is well-maintained and production-ready


**Why pgvector over alternatives?**
- **Single Database**: No need to maintain separate vector and relational databases
- **ACID Transactions**: Ensures data consistency across operations
- **SQL Integration**: Can combine vector search with SQL queries
- **Mature**: Production-ready, well-documented, active maintenance
- **Cost**: No additional service costs, uses existing PostgreSQL infrastructure

### LangGraph

**Why LangGraph?**

- **Workflow Management**: Clear visualization and management of chat workflow
- **State Management**: Typed state management with TypedDict for type safety
- **Conditional Routing**: Built-in support for conditional edges based on state
- **Modularity**: Easy to add, remove, or modify workflow nodes
- **Debugging**: Clear execution flow, easy to trace and debug
- **Extensibility**: Easy to extend with new nodes or modify routing logic
- **Documentation**: Good documentation and examples

**Alternatives Considered**: Custom state machine, LangChain
- **Rejected**: 
  - Custom state machine: More code to maintain, less clear visualization
  - LangChain: Heavier framework, LangGraph provides better workflow visualization

### Google Gemini

**Why Google Gemini?**

- **Performance**: Fast response times with gemini-2.5-flash model
- **Embeddings**: High-quality text-embedding-004 model (768 dimensions)
- **Cost**: Competitive pricing compared to alternatives
- **API Quality**: Reliable API with good error handling and response formats
- **Integration**: Easy Python SDK integration
- **Model Variety**: Multiple model options for different use cases

**Alternatives Considered**: OpenAI GPT, Anthropic Claude


## Response Pathway Switching Logic

The system implements a **user-controlled toggle** that switches between two distinct response pathways: **Knowledge Base (KB) Only** and **LLM-Augmented (KB + LLM)**.

### Complete Switching Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  User Request                                                   │
│  POST /chat { message, enable_llm: true/false }                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: retrieve_node(state)                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Embed user query                                       │  │
│  │    └─► Google text-embedding-004                         │  │
│  │                                                           │  │
│  │ 2. Vector similarity search                              │  │
│  │    └─► PostgreSQL pgvector:                              │  │
│  │        SELECT ... ORDER BY embedding <-> query_embedding │  │
│  │        LIMIT 3                                            │  │
│  │                                                           │  │
│  │ 3. Calculate best_distance                               │  │
│  │    └─► min(distance) from retrieved docs                 │  │
│  │                                                           │  │
│  │ 4. Build context                                          │  │
│  │    └─► Concatenate top_k documents                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: evaluate_node(state)                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Routing Decision Logic:                                 │  │
│  │                                                           │  │
│  │  if not state["enable_llm"]:                             │  │
│  │      return "kb_only"  ◄─── TOGGLE OFF: Always KB-only   │  │
│  │                                                           │  │
│  │  if state["enable_llm"]:                                  │  │
│  │      if best_distance < 0.35:                            │  │
│  │          return "kb_only"  (High confidence in KB)       │  │
│  │      else:                                                │  │
│  │          return "llm_augmented"  (Low confidence)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────┐                  ┌──────────────────────┐
│  Path A:          │                  │  Path B:             │
│  kb_only_node     │                  │  llm_augmented_node  │
└─────────┬─────────┘                  └──────────┬───────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────────────────────────────────────────┐
│  Path A: KB-Only Processing                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Check if context exists                            │  │
│  │    └─► If no context: "I couldn't find answer..."    │  │
│  │                                                       │  │
│  │ 2. Format response using LLM                         │  │
│  │    └─► Prompt: "Answer strictly from CONTEXT only"  │  │
│  │    └─► LLM formats but doesn't add external info     │  │
│  │                                                       │  │
│  │ 3. Label source as "KB"                              │  │
│  │                                                       │  │
│  │ 4. Save message to database                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Path B: LLM-Augmented Processing                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Check if context exists                            │  │
│  │                                                       │  │
│  │ 2. Build prompt:                                     │  │
│  │    - If context exists:                              │  │
│  │      "Use CONTEXT to answer. If insufficient,        │  │
│  │       provide general answer."                       │  │
│  │    - If no context:                                  │  │
│  │      "Answer conversationally."                     │  │
│  │                                                       │  │
│  │ 3. Generate response with Gemini                     │  │
│  │    └─► Can use KB context + general knowledge       │  │
│  │                                                       │  │
│  │ 4. Label source:                                     │  │
│  │    - "KB+LLM" if context exists                      │  │
│  │    - "LLM" if no context                             │  │
│  │                                                       │  │
│  │ 5. Save message to database                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Decision Matrix

| Toggle State | Similarity Distance | Route | Source Label | Behavior |
|-------------|---------------------|-------|--------------|----------|
| `enable_llm = false` | Any | `kb_only` | `"KB"` | Strict KB-only, LLM only formats, no general knowledge |
| `enable_llm = true` | < 0.35 (high similarity) | `kb_only` | `"KB"` | KB is sufficient, use KB-only formatting |
| `enable_llm = true` | ≥ 0.35 (low similarity) | `llm_augmented` | `"KB+LLM"` or `"LLM"` | Augment with LLM, allow general knowledge |

### Code Implementation

#### Routing Function

```python
def evaluate_node(state: ChatState) -> str:
    """Routing function - returns string, not dict!"""
    # User-controlled override: if toggle OFF, always KB-only
    if not state.get("enable_llm", False):
        return "kb_only"
    
    # When toggle ON, use similarity threshold for intelligent routing
    if state["best_distance"] is not None and state["best_distance"] < 0.35:
        return "kb_only"  # High confidence in KB
    else:
        return "llm_augmented"  # Low confidence, use LLM augmentation
```

#### KB-Only Node

```python
def kb_only_node(state: ChatState):
    """Respond strictly using the retrieved KB context."""
    if not state["context"]:
        reply = "I couldn't find an answer in internal docs."
    else:
        # Use LLM to format response, but strictly from KB context
        prompt = f"""You are an assistant that must answer strictly based on the provided CONTEXT.
        Do NOT add any information that is not explicitly stated there.
        If the context doesn't answer the question, reply: "I don't know based on internal docs."

        CONTEXT:
        {state['context']}

        QUESTION:
        {state['query']}
        """
        # Generate response using Gemini
        reply = MODEL.generate_content(prompt).text.strip()
    
    state["reply"] = reply
    state["source"] = "KB"  # Always marked as KB-only
    save_message(state["session_id"], "assistant", reply, source="KB")
    return state
```

#### LLM-Augmented Node

```python
def llm_augmented_node(state: ChatState):
    """Generate an answer using KB + LLM fallback."""
    context = state.get("context", "").strip()
    query = state.get("query", "").strip()

    if context:
        # Has KB context - use RAG approach
        prompt = f"""Use the CONTEXT below to answer the QUESTION.
        If the context doesn't contain enough information, say:
        "I don't know based on internal docs." Then provide a general answer.

        CONTEXT: {context}
        QUESTION: {query}
        """
        source = "KB+LLM"
    else:
        # No KB context - pure LLM mode
        prompt = f"""Answer the following question conversationally:
        QUESTION: {query}
        """
        source = "LLM"
    
    answer = MODEL.generate_content(prompt).text.strip()
    state["reply"] = answer
    state["source"] = source
    save_message(state["session_id"], "assistant", answer, source=source)
    return state
```

### Key Design Principles

1. **User Control**: When toggle is OFF, system always uses KB-only mode, regardless of similarity
2. **Intelligent Routing**: When toggle is ON, system uses similarity threshold (0.35) to decide
3. **Transparency**: Source label always indicates which pathway was used
4. **Consistency**: Vector retrieval always happens (no wasted computation)
5. **Graceful Degradation**: LLM mode can work even without KB context

### Similarity Threshold

The threshold of **0.35** (cosine distance) was chosen based on:
- **Empirical Testing**: Tested with various queries to find optimal balance
- **High Confidence**: Distance < 0.35 indicates strong semantic similarity
- **Low Confidence**: Distance ≥ 0.35 suggests KB may not have good answer
- **Tunable**: Can be adjusted based on domain and document characteristics

## Data Flow

### Document Ingestion Flow

```
Document (FAQ.txt)
    │
    ▼
ingest_docs.py
    │
    ├─► Read document content
    │
    ├─► Generate embedding
    │   └─► Google text-embedding-004 (768 dims)
    │
    └─► Store in PostgreSQL
        └─► INSERT INTO docs (title, content, embedding)
```

### Query Processing Flow

```
User Query
    │
    ▼
Embed Query
    └─► Google text-embedding-004
    │
    ▼
Vector Search
    └─► PostgreSQL pgvector
    │   └─► SELECT ... ORDER BY embedding <-> query_embedding
    │
    ▼
Retrieve Top-K Documents
    │
    ▼
Routing Decision (based on enable_llm flag)
    │
    ├─► KB-Only Path
    │   └─► Format from KB context
    │
    └─► LLM-Augmented Path
        └─► Generate with KB + general knowledge
    │
    ▼
Save to Database
    └─► Store message with source label
    │
    ▼
Return Response
    └─► { reply, source, session_id }
```

## Database Schema

### Vector Store (docs table)

```sql
CREATE TABLE docs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768)  -- pgvector type
);

CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops);
```

**Purpose**: Store document embeddings for similarity search

### Relational Store

**sessions table**:
- `id`: UUID primary key
- `created_at`: Timestamp
- `last_active`: Timestamp

**messages table**:
- `id`: UUID primary key
- `session_id`: Foreign key to sessions
- `role`: 'user' or 'assistant'
- `content`: Message text
- `source`: 'KB', 'KB+LLM', or 'LLM'
- `created_at`: Timestamp

**Relationships**: Session → Messages (one-to-many, cascade delete)

## Performance Considerations

1. **Vector Index**: ivfflat index on embeddings for fast similarity search
2. **Connection Pooling**: SQLAlchemy connection pool for database efficiency
3. **Async Support**: FastAPI async endpoints for concurrent requests
4. **Caching**: Can add Redis for frequently accessed sessions (future)

## Security Considerations

1. **API Keys**: Stored in environment variables, never in code
2. **Input Validation**: Pydantic schemas validate all inputs
3. **SQL Injection**: Prevented by SQLAlchemy ORM and parameterized queries
4. **CORS**: Configured to allow only frontend origin
