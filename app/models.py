"""
SQLAlchemy database models for Session and Message tables.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
import uuid
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()



class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationship: one session has many messages
    messages = relationship("Message", back_populates="session", cascade="all, delete")

    def __repr__(self):
        return f"<Session id={self.id} user_id={self.user_id}>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)        # 'user' or 'assistant'
    content = Column(Text)
    source = Column(String, nullable=True)  # e.g. "Internal Docs" or "LLM"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: message belongs to a session
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message id={self.id} role={self.role} session={self.session_id}>"