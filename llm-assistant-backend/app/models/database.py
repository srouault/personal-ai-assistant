from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

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
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    interaction_id = Column(Integer, nullable=False)  # To pair user questions with assistant answers
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
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