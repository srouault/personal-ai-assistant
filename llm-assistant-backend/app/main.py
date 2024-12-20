from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
import logging
import json
from pydantic import BaseModel
from .memory.memory_manager import MemoryManager
import asyncio

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

async def generate_stream(request: ChatRequest):
    full_response = ""
    try:
        # Get the last user message from the messages list
        last_message = request.messages[-1]
        user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        async for text in llm_service.generate_response_stream(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        ):
            full_response += text
            yield f"data: {json.dumps({'text': text})}\n\n"
        
        # After stream ends, trigger summarization in background
        logger.info("Stream completed, triggering summarization...")
        task = asyncio.create_task(
            memory_manager.add_exchange(
                user_message,  # Use the extracted user message
                full_response
            )
        )
        # Add a callback to log when the task completes
        task.add_done_callback(
            lambda t: logger.info("Summarization task completed")
        )
    except Exception as e:
        logger.error(f"Error in generate_stream: {str(e)}")
        logger.exception("Full traceback:")  # This will log the full stack trace
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if llm_service is None:
        raise HTTPException(
            status_code=503,
            detail="LLM model not loaded. Please check server logs for details."
        )
    
    return StreamingResponse(
        generate_stream(request),
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