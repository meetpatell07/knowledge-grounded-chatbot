# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from app.graph_logic import handle_chat
from app.db import get_db, engine
from app.models import Base, Session as SessionModel, Message as MessageModel

from app.schemas import (
    ChatRequest,
    ChatResponse,
    SessionResponse,
    SessionCreateRequest,
    MessageResponse,
)

# Create tables (in production, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

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

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    if not req.message:
        raise HTTPException(status_code=400, detail="message required")
    result = handle_chat(session_id, req.message)
    return ChatResponse(reply=result["reply"], source=result["source"], session_id=session_id)

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}

# Session endpoints
@app.get("/sessions", response_model=List[SessionResponse])
def get_all_sessions(db: Session = Depends(get_db)):
    """Get all sessions with their messages"""
    try:
        sessions = db.query(SessionModel).order_by(SessionModel.createdAt.desc()).all()
        
        result = []
        for session in sessions:
            # Messages are loaded via relationship
            session_messages = [
                MessageResponse(
                    id=str(msg.id),
                    sessionId=str(msg.sessionId),
                    role=msg.role,
                    content=msg.content,
                    source=msg.source,
                    createdAt=msg.createdAt
                )
                for msg in sorted(session.messages, key=lambda m: m.createdAt)
            ]
            
            result.append(SessionResponse(
                id=str(session.id),
                userId=session.userId,
                createdAt=session.createdAt,
                lastActive=session.lastActive,
                messages=session_messages
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a specific session"""
    try:
        messages = db.query(MessageModel).filter(
            MessageModel.sessionId == session_id
        ).order_by(MessageModel.createdAt.asc()).all()
        
        return [
            MessageResponse(
                id=str(msg.id),
                sessionId=str(msg.sessionId),
                role=msg.role,
                content=msg.content,
                source=msg.source,
                createdAt=msg.createdAt
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

@app.post("/sessions", response_model=SessionResponse)
def create_or_get_session(req: SessionCreateRequest, db: Session = Depends(get_db)):
    """Create a new session or get existing one"""
    try:
        session_id = req.sessionId or str(uuid.uuid4())
        
        # Try to find existing session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        
        if session:
            # Update lastActive
            from datetime import datetime
            session.lastActive = datetime.utcnow()
            db.commit()
            db.refresh(session)
            
            return SessionResponse(
                id=str(session.id),
                userId=session.userId,
                createdAt=session.createdAt,
                lastActive=session.lastActive,
                messages=[]
            )
        else:
            # Create new session
            new_session = SessionModel(id=session_id)
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            return SessionResponse(
                id=str(new_session.id),
                userId=new_session.userId,
                createdAt=new_session.createdAt,
                lastActive=new_session.lastActive,
                messages=[]
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/get session: {str(e)}")
