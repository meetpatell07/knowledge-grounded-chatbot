"""
SQLAlchemy database models for Session and Message tables.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
import uuid
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Session(Base):
    """
    Session model representing a chat session.
    
    Attributes:
        id: Unique session identifier (UUID)
        userId: Optional user identifier
        createdAt: Timestamp when session was created
        lastActive: Timestamp of last activity
        messages: Relationship to associated messages
    """
    __tablename__ = "Session"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    userId = Column(String, nullable=True)
    createdAt = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    lastActive = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationship
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, userId={self.userId})>"


class Message(Base):
    """
    Message model representing a chat message.
    
    Attributes:
        id: Unique message identifier (UUID)
        sessionId: Foreign key to Session
        role: Message role (user, assistant, system)
        content: Message content
        source: Optional source identifier (KB, LLM, etc.)
        createdAt: Timestamp when message was created
        session: Relationship to parent session
    """
    __tablename__ = "Message"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    sessionId = Column(
        UUID(as_uuid=False),
        ForeignKey("Session.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=True)
    createdAt = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationship
    session = relationship("Session", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, sessionId={self.sessionId})>"
