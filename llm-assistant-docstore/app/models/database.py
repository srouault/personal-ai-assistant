from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Create data directory if it doesn't exist
data_dir = "./data"
os.makedirs(data_dir, exist_ok=True)

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    collection = Column(String(50), nullable=False)  # 'context' or 'memory'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create DB and tables
db_path = os.path.join(data_dir, "documents.db")
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine) 