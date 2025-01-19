from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, create_engine, ForeignKey, Boolean, JSON, Text, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from sqlalchemy.sql import func
import json

Base = declarative_base()

class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    content = Column(LargeBinary)  # Store original file content as bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    file_type = Column(String)  # Store file extension


class LearningPath(Base):
    __tablename__ = 'learning_paths'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    path_metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    tutorials = relationship("Tutorial", back_populates="learning_path")


class Tutorial(Base):
    __tablename__ = 'tutorials'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text)
    order = Column(Integer)
    estimated_duration = Column(Integer)  # in minutes
    learning_path_id = Column(Integer, ForeignKey('learning_paths.id'))
    created_at = Column(DateTime, server_default=func.now())

    learning_path = relationship("LearningPath", back_populates="tutorials")
    chapters = relationship("Chapter", back_populates="tutorial", order_by="Chapter.order")


class Chapter(Base):
    __tablename__ = 'chapters'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text)
    order = Column(Integer)
    tutorial_id = Column(Integer, ForeignKey('tutorials.id'))
    created_at = Column(DateTime, server_default=func.now())

    tutorial = relationship("Tutorial", back_populates="chapters")
    steps = relationship("Step", back_populates="chapter", order_by="Step.order")


class Step(Base):
    __tablename__ = 'steps'

    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    order = Column(Integer, nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    expected_result = Column(Text)
    validation_type = Column(String(50))  # manual, code, file_check
    created_at = Column(DateTime, server_default=func.now())

    chapter = relationship("Chapter", back_populates="steps")

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)  # We can use chat_id as user_id for now
    tutorial_id = Column(Integer, ForeignKey("tutorials.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    step_id = Column(Integer, ForeignKey("steps.id"))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    tutorial = relationship("Tutorial")
    chapter = relationship("Chapter")
    step = relationship("Step")


# Create SQLite database engine
DATABASE_URL = "sqlite:///./data/documents.db"
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine) 