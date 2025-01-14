from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, create_engine, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from sqlalchemy.sql import func

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    content = Column(LargeBinary)  # Store original file content as bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    file_type = Column(String)  # Store file extension

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(String)
    category = Column(String)  # e.g., "Engineering Onboarding", "Sales Training", etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    path_metadata = Column(JSON)  # Changed from metadata to path_metadata

    # Relationship
    tutorials = relationship("Tutorial", back_populates="learning_path")

class Tutorial(Base):
    __tablename__ = "tutorials"
    
    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
    title = Column(String)
    description = Column(String)
    order = Column(Integer)  # Position in the learning path
    content = Column(String)  # Tutorial content/instructions
    estimated_duration = Column(Integer)  # in minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    learning_path = relationship("LearningPath", back_populates="tutorials")
    chapters = relationship("TutorialChapter", back_populates="tutorial", order_by="TutorialChapter.order")

class TutorialChapter(Base):
    __tablename__ = "tutorial_chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"))
    title = Column(String)
    content = Column(String)
    order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tutorial = relationship("Tutorial", back_populates="chapters")

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)  # We can use chat_id as user_id for now
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"))
    chapter_id = Column(Integer, ForeignKey("tutorial_chapters.id"))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    tutorial = relationship("Tutorial")
    chapter = relationship("TutorialChapter")

# Add relationship to LearningPath
LearningPath.tutorials = relationship("Tutorial", order_by=Tutorial.order, back_populates="learning_path")

# Create SQLite database engine
DATABASE_URL = "sqlite:///./data/documents.db"
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine) 