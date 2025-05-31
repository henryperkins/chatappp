"""Database setup and utility functions for SQLAlchemy ORM."""
import os
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
)  # pylint: disable=import-error
from sqlalchemy.ext.declarative import declarative_base  # pylint: disable=import-error
from sqlalchemy.orm import sessionmaker  # pylint: disable=import-error
from .config import settings  # pylint: disable=import-error,relative-beyond-top-level

# Ensure SQLite DB directory exists; prevents "unable to open database file"
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.split(":///")[1].split("?")[0]
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ChatMessage(Base):
    """SQLAlchemy ORM model for storing chat messages."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model = Column(String)
    temperature = Column(Float)
    max_tokens = Column(Integer)


def get_db():
    """Database session generator (used for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes DB tables by creating all defined SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)
