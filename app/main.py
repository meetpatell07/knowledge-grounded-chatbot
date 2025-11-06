# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.graph_logic import handle_chat
from app.db import get_conn
import uuid

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    reply: str
    source: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    if not req.message:
        raise HTTPException(status_code=400, detail="message required")
    result = handle_chat(session_id, req.message)
    return ChatResponse(reply=result["reply"], source=result["source"], session_id=session_id)

@app.get("/health")
def health():
    return {"status":"ok"}
