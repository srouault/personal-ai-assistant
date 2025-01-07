from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class RelevanceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_RELEVANT = "not_relevant"

class DocumentMetadata(BaseModel):
    source: str
    full_document: str
    similarity: float
    relevance: RelevanceLevel
    document_id: Optional[int] = None

class QueryResult(BaseModel):
    text: str
    metadata: DocumentMetadata
    is_relevant: bool

class QueryResponse(BaseModel):
    results: List[QueryResult]
    has_results: bool = False

class QueryRequest(BaseModel):
    query: str
    num_results: Optional[int] = 3
    min_relevance: Optional[RelevanceLevel] = None
    min_similarity: Optional[float] = None