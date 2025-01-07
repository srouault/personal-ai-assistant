import os
os.environ["LANGCHAIN_DISABLE_TELEMETRY"] = "true"

from pathlib import Path
import uuid
from typing import List, Optional, Dict
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from app.models.document import QueryResponse, QueryResult, DocumentMetadata, RelevanceLevel

class DocumentService:
    def __init__(self):
        # Initialize embedding model from local path
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="models/embeddings",  # Local path to model
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize ChromaDB
        self.persist_directory = "data/chromadb"
        self.context_collection = self._initialize_collection("context")
        self.memory_collection = self._initialize_collection("memory")
        
        logging.info("Vector store initialized with context and memory collections")

    def _initialize_collection(self, collection_name: str) -> Chroma:
        """Initialize or load existing ChromaDB collection"""
        return Chroma(
            collection_name=collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model
        )

    async def add_document(self, filename: str, content: bytes, collection: str = "context") -> str:
        try:
            db = self.context_collection if collection == "context" else self.memory_collection
            
            # Check if document with this filename already exists
            existing_docs = db._collection.get(
                where={"source": filename}
            )
            if existing_docs['ids']:
                logging.info(f"Document {filename} already exists in {collection}, skipping")
                return existing_docs['ids'][0]

            text = content.decode('utf-8')
            doc_id = str(uuid.uuid4())
            chunks = self._chunk_text(text)
            
            logging.info(f"Processing document {filename} with {len(chunks)} chunks for {collection}")
            
            documents = []
            for chunk in chunks:
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": filename,
                            "full_document": text,
                            "collection": collection
                        }
                    )
                )
            
            db.add_documents(documents)
            db.persist()
            
            logging.info(f"Successfully added document {filename} to {collection} with ID {doc_id}")
            return doc_id
            
        except Exception as e:
            logging.error(f"Error adding document to {collection}: {str(e)}")
            logging.exception("Full traceback:")
            raise

    def _get_relevance_level(self, similarity: float) -> RelevanceLevel:
        """Determine relevance level based on similarity score"""
        # Using similarity score directly (higher is better)
        if similarity > 0.5:     # Very high similarity
            return RelevanceLevel.HIGH
        elif similarity > 0.2:   # Good similarity
            return RelevanceLevel.MEDIUM
        elif similarity > 0.1:   # Acceptable similarity
            return RelevanceLevel.LOW
        return RelevanceLevel.NOT_RELEVANT  # Too dissimilar

    def _is_relevant(self, relevance: RelevanceLevel) -> bool:
        """Determine if a result is relevant based on relevance level"""
        # Consider all levels except NOT_RELEVANT as relevant
        return relevance != RelevanceLevel.NOT_RELEVANT

    async def query_documents(
        self, 
        query: str, 
        collection: str = "context",
        num_results: int = 3, 
        min_relevance: Optional[RelevanceLevel] = None,
        min_similarity: Optional[float] = None
    ) -> QueryResponse:
        try:
            logging.info(f"Querying {collection} collection with: '{query}'")
            
            db = self.context_collection if collection == "context" else self.memory_collection
            doc_count = db._collection.count()
            logging.info(f"Total documents in {collection} collection: {doc_count}")
            
            if doc_count == 0:
                logging.warning(f"No documents in {collection} collection")
                return QueryResponse(results=[], has_results=False)
            
            # Search in ChromaDB
            logging.info(f"Searching for top {num_results * 2} results in {collection}")
            results = db.similarity_search_with_relevance_scores(
                query,
                k=num_results * 2  # Get more results to filter
            )
            
            logging.info(f"Found {len(results)} initial results")
            
            # Use dict to deduplicate by source while keeping highest similarity
            source_results = {}
            for doc, similarity in results:
                source = doc.metadata["source"]
                if source not in source_results or similarity > source_results[source][1]:
                    source_results[source] = (doc, similarity)
            
            # Convert back to list and format results
            formatted_results = []
            for doc, similarity in source_results.values():
                relevance = self._get_relevance_level(similarity)
                
                # Apply filters
                if min_similarity is not None and similarity < min_similarity:
                    logging.info(f"Skipping result due to low similarity: {similarity} < {min_similarity}")
                    continue
                    
                if min_relevance is not None and relevance.value < min_relevance.value:
                    logging.info(f"Skipping result due to low relevance: {relevance} < {min_relevance}")
                    continue
                
                result = QueryResult(
                    text=doc.page_content,
                    metadata=DocumentMetadata(
                        source=doc.metadata["source"],
                        full_document=doc.metadata["full_document"],
                        similarity=float(similarity),
                        relevance=relevance
                    ),
                    is_relevant=self._is_relevant(relevance)
                )
                formatted_results.append(result)
            
            # Sort by similarity
            formatted_results.sort(key=lambda x: x.metadata.similarity, reverse=True)
            
            # Limit to requested number
            formatted_results = formatted_results[:num_results]
            logging.info(f"Returning {len(formatted_results)} final results")
            
            return QueryResponse(
                results=formatted_results,
                has_results=len(formatted_results) > 0
            )
            
        except Exception as e:
            logging.error(f"Error querying documents: {str(e)}")
            logging.exception("Full traceback:")
            raise

    async def get_context_for_prompt(
        self, 
        prompt: str, 
        num_results: int = 3,
        min_similarity: float = 0.1
    ) -> str:
        """Get relevant context from the vector database for a given prompt"""
        try:
            # Search for relevant documents
            results = await self.query_documents(
                query=prompt,
                collection="context",
                num_results=num_results,
                min_similarity=min_similarity
            )
            
            if not results:
                logging.info("No relevant context found")
                return ""
            
            # Format context
            context_parts = []
            for i, result in enumerate(results, 1):
                similarity = result["metadata"]["similarity"]
                context_parts.append(
                    f"[Context {i} (similarity: {similarity:.2f})]: {result['text']}"
                )
            
            # Combine all context
            context = "\n\n".join(context_parts)
            logging.info(f"Found {len(results)} relevant context pieces")
            
            return context
            
        except Exception as e:
            logging.error(f"Error getting context: {str(e)}")
            logging.exception("Full traceback:")
            return ""

    async def add_memory(self, content: str, metadata: Dict = None) -> str:
        """Add a memory entry to the memory collection"""
        try:
            doc_id = str(uuid.uuid4())
            memory_doc = Document(
                page_content=content,
                metadata={
                    "source": f"memory_{doc_id}",
                    "full_document": content,
                    "collection": "memory",
                    **(metadata or {})
                }
            )
            
            self.memory_collection.add_documents([memory_doc])
            self.memory_collection.persist()
            
            logging.info(f"Successfully added memory with ID {doc_id}")
            return doc_id
            
        except Exception as e:
            logging.error(f"Error adding memory: {str(e)}")
            logging.exception("Full traceback:")
            raise

    async def query_memory(
        self, 
        query: str, 
        num_results: int = 3,
        min_similarity: float = 0.1
    ) -> QueryResponse:
        """Specifically query the memory collection"""
        return await self.query_documents(
            query=query,
            collection="memory",
            num_results=num_results,
            min_similarity=min_similarity
        )