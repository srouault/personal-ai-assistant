from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    chat_id: Optional[int] = None
    interaction_id: Optional[int] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = Field(800, ge=1, le=2000)  # Ensure max_tokens is between 1 and 2000

class ChatSummary(BaseModel):
    id: int
    title: str
    updated_at: datetime
    summary: Optional[str] = None

class ChatDetail(BaseModel):
    id: int
    title: str
    messages: List[ChatMessage]
    summary: Optional[str] = None

class ChatResponse(BaseModel):
    text: str 