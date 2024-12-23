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
    # Initialize LLM service once
    llm_service = LLMService()
except FileNotFoundError as e:
    logging.error(str(e))
    llm_service = None

# Initialize memory manager with the LLM service
memory_manager = MemoryManager(llm_service)

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

        #only use last 5 messages for prompt
        prompt_messages = request.messages[-5:]

        async for text in llm_service.generate_response_stream(
            messages=prompt_messages,
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
                full_response,
                chat_id,  # Pass chat_id to memory manager
                db_service  # Pass db_service to memory manager
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

@app.get("/chat/latest/id")
async def get_latest_chat_id():
    chat_id = db_service.get_latest_chat_id()
    return {"id": chat_id}

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int):
    success = db_service.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

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
    
    # Get messages and organize them by interaction
    messages = db_service.get_chat_messages(chat_id)
    interaction_summaries = db_service.get_interaction_summaries(chat_id)
    
    # Create a dictionary of interaction summaries for easy lookup
    summaries_dict = {s.interaction_id: {
        'user_summary': s.user_summary,
        'assistant_summary': s.assistant_summary
    } for s in interaction_summaries}
    
    # Group messages by interaction_id
    interactions = []
    current_interaction = None
    
    for msg in messages:
        if current_interaction is None or msg.interaction_id != current_interaction['interaction_id']:
            summaries = summaries_dict.get(msg.interaction_id, {})
            current_interaction = {
                'interaction_id': msg.interaction_id,
                'messages': [],
                'user_summary': summaries.get('user_summary'),
                'assistant_summary': summaries.get('assistant_summary')
            }
            interactions.append(current_interaction)
        current_interaction['messages'].append({
            'role': msg.role,
            'content': msg.content
        })
    
    return {
        "id": chat.id,
        "title": chat.title,
        "interactions": interactions,
        "summary": chat.summary  # Overall chat summary
    }