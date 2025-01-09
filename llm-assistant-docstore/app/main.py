from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.document_service import DocumentService
from app.models.document import QueryRequest, QueryResponse, Memory, MemoryResponse
import logging

app = FastAPI()
doc_service = DocumentService()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/documents")
async def upload_document(file: UploadFile):
    try:
        content = await file.read()
        doc_id = await doc_service.add_document(file.filename, content)
        return {"message": "Document added successfully", "doc_id": doc_id}
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories")
async def upload_memory(memory: Memory):
    try:
        datetime_str = memory.timestamp.isoformat()

        content = f"""Interaction between user and assistant, {memory.user}. The assistant answered with: {memory.assistant}.
                This interaction occurred at {datetime_str}."""

        mem_id = await doc_service.add_memory(content, {'timestamp': datetime_str, 'chat_id' : memory.chat_id, 'interaction_id': memory.interaction_id})
        return {"message": "Memory added successfully", "doc_id": mem_id}
    except Exception as e:
        logging.error(f"Error uploading memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        results = await doc_service.query_documents(
            query=request.query,
            num_results=request.num_results,
            min_relevance=request.min_relevance,
            min_similarity=request.min_similarity
        )
        return results
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recall", response_model=MemoryResponse)
async def query_memory(request: QueryRequest):
    try:
        results = await doc_service.query_memory(
            query=request.query,
            num_results=request.num_results,
            min_similarity=request.min_similarity
        )
        return results
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))