from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse, ChatMessage
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
    db_service = DatabaseService()
    llm_service = LLMService(db_service=db_service)
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
    context_documents = []  # Store context document info
    try:
        last_message = request.messages[-1]
        user_message = last_message.content

        #only use last 5 messages for prompt
        prompt_messages = request.messages[-5:]

        try:
            # Now you can use model.predict on new text
            new_texts = [
                user_message
            ]
            predictions = llm_service.classifier_model.predict(new_texts)
            print(predictions)
        except Exception as e:
            logging.error(f"Error predicting prompt type: {str(e)}")
            logging.exception("Full traceback:")

        context = None

        if user_message:

            context_response = await llm_service.get_context(
                user_message
            )
            context = context_response[0]
            context_documents = context_response[1]
            if context:
                logging.info("Context found and will be used for response")
                logging.debug(f"Context preview: {context[:200]}...")
            else:
                logging.info("No relevant context found")

        async for text in llm_service.generate_response_stream(
            messages=prompt_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            context=context
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
                chat_id,
                db_service,
                context_documents  # Pass context documents to memory manager
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
async def chat_stream(request: ChatRequest, chat_id: int):
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
    message = db_service.add_message(chat_id, "user", request.messages[-1].content)
    
    # Create a new list of messages with the updated last message
    messages = list(request.messages[:-1])  # Convert to list and exclude last message
    messages.append(ChatMessage(
        role=request.messages[-1].role,
        content=request.messages[-1].content,
        chat_id=chat_id,
        interaction_id=message.interaction_id  # Use the interaction_id from the stored message
    ))
    
    # Create a new request with the updated messages
    updated_request = ChatRequest(
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )

    # Return a StreamingResponse
    return StreamingResponse(
        generate_stream(updated_request, chat_id),
        media_type="text/event-stream"
    )

@app.post("/prompt", response_model=PromptResponse)
async def process_prompt(request: PromptRequest):
    try:
        response = await llm_service.process_prompt(request.prompt)
        return PromptResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

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