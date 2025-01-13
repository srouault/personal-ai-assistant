from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    summary = Column(Text, nullable=True)  # Overall chat summary
    
    # Relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    interaction_summaries = relationship("InteractionSummary", back_populates="chat", cascade="all, delete-orphan")
    interaction_contexts = relationship("InteractionContext", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    interaction_id = Column(Integer)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with chat
    chat = relationship("Chat", back_populates="messages") 

class InteractionSummary(Base):
    __tablename__ = "interaction_summaries"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    interaction_id = Column(Integer, nullable=False)
    user_summary = Column(Text, nullable=False)  # Summary of what user asked
    assistant_summary = Column(Text, nullable=False)  # Summary of assistant's response
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with chat
    chat = relationship("Chat", back_populates="interaction_summaries")

class InteractionContext(Base):
    __tablename__ = "interaction_contexts"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    interaction_id = Column(Integer, nullable=False)
    context_document_id = Column(Integer, nullable=True)  # ID from documents.db
    context_memory_message_id = Column(Integer, nullable=True)
    similarity_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with chat
    chat = relationship("Chat", back_populates="interaction_contexts")

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(String)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    path_metadata = Column(JSON)

class Tutorial(Base):
    __tablename__ = "tutorials"
    
    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
    title = Column(String)
    description = Column(String)
    order = Column(Integer)
    content = Column(String)
    estimated_duration = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    learning_path = relationship("LearningPath", back_populates="tutorials")

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"))
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    notes = Column(String)
    
    tutorial = relationship("Tutorial")

# Add relationship to LearningPath
LearningPath.tutorials = relationship("Tutorial", order_by=Tutorial.order, back_populates="learning_path")

# Database configuration
DATABASE_URL = "sqlite:///./data/assistant.db"
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)