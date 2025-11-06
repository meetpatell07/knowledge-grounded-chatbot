"""
Pydantic schemas for requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ---------- Chat ----------
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    source: str
    session_id: str


# ---------- Messages ----------
class MessageResponse(BaseModel):
    id: str
    sessionId: str
    role: str
    content: str
    source: Optional[str]
    createdAt: datetime

    class Config:
        from_attributes = True  # Enables ORM → Pydantic conversion


# ---------- Sessions ----------
class SessionResponse(BaseModel):
    id: str
    userId: Optional[str]
    createdAt: datetime
    lastActive: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class SessionCreateRequest(BaseModel):
    sessionId: Optional[str] = None
