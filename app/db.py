"""
Database configuration and session management.
"""
import os
from typing import Generator
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import psycopg2
import logging

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Please set DATABASE_URL in .env")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (for non-FastAPI contexts).
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_context() as db:
            session = db.query(Session).first()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_conn() -> psycopg2.extensions.connection:
    """
    Get a raw psycopg2 connection for vector operations.
    
    This is used for pgvector queries that require raw SQL.
    
    Returns:
        psycopg2.extensions.connection: Database connection
        
    Example:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM docs WHERE embedding <-> %s::vector < 0.5", (embedding,))
    """
    return psycopg2.connect(DATABASE_URL)


def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
