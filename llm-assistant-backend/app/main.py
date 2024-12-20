from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
import logging
import json
from pydantic import BaseModel
from .memory.memory_manager import MemoryManager
import asyncio
from .services.db_service import DatabaseService
from typing import List
from datetime import datetime

# Configure logging at the top of main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Initialize LLM service
    llm_service = LLMService()
except FileNotFoundError as e:
    logging.error(str(e))
    llm_service = None

# Initialize memory manager (remove token)
memory_manager = MemoryManager()

# Initialize services
db_service = DatabaseService()

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Welcome to LLM Assistant API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": llm_service is not None
    }

async def generate_stream(request: ChatRequest, chat_id: int):
    full_response = ""
    try:
        last_message = request.messages[-1]
        user_message = last_message.content
        
        async for text in llm_service.generate_response_stream(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        ):
            full_response += text
            yield f"data: {json.dumps({'text': text})}\n\n"
        
        # Store the assistant's response
        db_service.add_message(chat_id, "assistant", full_response)
        
        # After stream ends, trigger summarization
        logger.info("Stream completed, triggering summarization...")
        task = asyncio.create_task(
            memory_manager.add_exchange(
                user_message,
                full_response
            )
        )
        task.add_done_callback(
            lambda t: logger.info("Summarization task completed")
        )
    except Exception as e:
        logger.error(f"Error in generate_stream: {str(e)}")
        logger.exception("Full traceback:")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, chat_id: int = Query(1, description="Chat ID")):
    if llm_service is None:
        raise HTTPException(
            status_code=503,
            detail="LLM model not loaded. Please check server logs for details."
        )

    # Get or create chat
    db_service.get_or_create_chat(
        chat_id, 
        default_title=f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Store the user's message
    db_service.add_message(chat_id, "user", request.messages[-1].content)
    
    # Return a StreamingResponse
    return StreamingResponse(
        generate_stream(request, chat_id),
        media_type="text/event-stream"
    )

@app.post("/prompt", response_model=PromptResponse)
async def process_prompt(request: PromptRequest):
    try:
        response = await llm_service.process_prompt(request.prompt)
        return PromptResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

class LLMAssistant:
    def __init__(self):
        # ... existing initialization ...
        self.memory_manager = MemoryManager()
    
    async def process_message(self, message: str) -> str:
        # Get current conversation summary
        current_summary = self.memory_manager.get_current_summary()
        
        # Process the message with the LLM (existing logic)
        response = await self._generate_response(message, current_summary)
        
        # Update conversation memory
        self.memory_manager.add_exchange(message, response)
        
        return response
    
    async def _generate_response(self, message: str, current_summary: str = None) -> str:
        # Modify your existing response generation to include the summary in the prompt
        context = f"Previous conversation summary: {current_summary}\n" if current_summary else ""
        context += f"User message: {message}\n"
        
        # ... rest of your response generation logic ... 

# New chat management endpoints
@app.post("/chats")
async def create_chat(title: str):
    chat = db_service.create_chat(title)
    return {"id": chat.id, "title": chat.title}

@app.get("/chats")
async def list_chats():
    chats = db_service.get_all_chats()
    return [{"id": chat.id, 
             "title": chat.title, 
             "updated_at": chat.updated_at,
             "summary": chat.summary} for chat in chats]

@app.get("/chats/{chat_id}")
async def get_chat(chat_id: int):
    chat = db_service.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {
        "id": chat.id,
        "title": chat.title,
        "messages": [{"role": msg.role, "content": msg.content} 
                    for msg in chat.messages],
        "summary": chat.summary
    }