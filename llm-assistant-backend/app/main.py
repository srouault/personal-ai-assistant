from fastapi import FastAPI, HTTPException, Depends, Query, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse, ChatMessage
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
import logging
import json
from pydantic import BaseModel
from .memory.memory_manager import MemoryManager
import asyncio
from .services.db_service import DatabaseService
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, Chat
import httpx

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
llm_service = LLMService(db_service=db_service)
memory_service = MemoryService()

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str

# Add database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# Add this with the other dependency functions
def get_llm_service():
    return llm_service

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

        # Get context based on query type
        context = None
        memory_assistant_msg = None
        prediction = "New"  # Default to new query type
        
        try:
            # Now you can use model.predict on new text
            new_texts = [user_message]
            predictions = llm_service.classifier_model.predict(new_texts)
            prediction = predictions[0]
            logging.info(f"Query classified as: {prediction}")
        except Exception as e:
            logging.error(f"Error predicting prompt type: {str(e)}")
            logging.exception("Full traceback:")

        if prediction == "Continuation":
            # Get context from the previous interaction
            previous_contexts = await db_service.get_last_interaction_contexts(chat_id)
            if previous_contexts:
                context = "\n\n---\n\n".join(
                    f"Source: Previous context\n\n{ctx['content']}"
                    for ctx in previous_contexts
                )
                context_documents = {
                    str(ctx['document_id']): {
                        'document_id': ctx['document_id'],
                        'similarity': ctx['similarity_score']
                    }
                    for ctx in previous_contexts
                }
                logging.info("Using context from previous interaction")
            else:
                context_response = await llm_service.get_context(user_message)
                context = context_response[0]
                context_documents = context_response[1]


        
        elif prediction == "Reference":
            # Query memory collection first
            memory_results = await memory_service.query_memories(
                query=user_message,
                num_results=2,
                min_similarity=0.001
            )
            
            if memory_results and memory_results.get("has_results"):
                # Format memory results for a more natural response
                memory_prompts = []
                for mem in memory_results["results"]:
                    mem_chat_id = mem['chat_id']
                    mem_interaction_id = mem['interaction_id']

                    memory_assistant_msg = await db_service.get_assistant_message_id_and_content_by_chat_id_interaction_id(chat_id=mem_chat_id, interaction_id=mem_interaction_id)

                    if len(memory_assistant_msg) > 0:
                        # Parse the timestamp to a more readable format
                        timestamp = datetime.fromisoformat(mem['timestamp'])
                        formatted_time = timestamp.strftime("%A the %d of %B at %I:%M %p")

                        memory_prompts.append(
                            f"""On {formatted_time}, the conversation was: {mem['content']} \n\nThe assistant responded with: {memory_assistant_msg[0]['content']}\n\nReference: {mem_chat_id},{mem_interaction_id}

If you want to go back to that conversation, click here: <<<chat_history>>>{mem_chat_id},{mem_interaction_id}<<<chat_history>>>"""
                        )
                
                # Create a special prompt for memory references
                memory_context = "\n\n".join(memory_prompts)
                context = f"""Previous conversation history:
{memory_context}

When responding, start by acknowledging that you recall the conversation, mentioning when it happened, 
and briefly summarize what was discussed. Then proceed to answer the current question using that context.
"""
                logging.info("Using memory reference format for response")
            else:
                # Create a special prompt for when no memories are found
                context = """I should respond by saying: "Sorry, I do not recall us having that conversation."
                Do not add any additional explanations or suggestions."""
                logging.info("No relevant memories found")
        
        elif prediction == "New":
            # Get fresh context for the current message
            context_response = await llm_service.get_context(user_message)
            context = context_response[0]
            context_documents = context_response[1]
            logging.info("Using fresh context for new query")
        
        if context:
            logging.info("Context found and will be used for response")
            logging.debug(f"Context preview: {context[:200]}...")
        else:
            logging.info("No relevant context found")

        async for text in llm_service.generate_response_stream(
            messages=prompt_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            context=context,
            prediction_type=prediction
        ):
            full_response += text
            yield f"data: {json.dumps({'text': text})}\n\n"
        
        # Store the assistant's response
        resp = db_service.add_message(chat_id, "assistant", full_response)
        chat_id = resp[1]
        interaction_id = resp[2]
        
        # After stream ends, trigger summarization
        logger.info("Stream completed, triggering summarization...")
        # Only store memory if it's not a reference-type query

        task = asyncio.create_task(
            memory_manager.add_exchange(
                user_message,
                full_response,
                chat_id,
                interaction_id,
                db_service,
                context_documents,
                prediction,
                memory_assistant_msg
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
async def chat_stream(
    request: Request,
    chat_id: int,
    tutorial_id: Optional[int] = None,
    chapter_id: Optional[int] = None
):
    try:
        body = await request.json()
        messages = body.get('messages', [])
        temperature = body.get('temperature', 0.7)
        max_tokens = body.get('max_tokens', 2000)
        
        # If this is a tutorial chat, fetch the tutorial context
        tutorial_context = None
        if tutorial_id and chapter_id:
            try:
                # Fetch chapter context
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:8001/tutorials/{tutorial_id}/chapters/{chapter_id}/context"
                    )
                    if response.status_code == 200:
                        tutorial_context = response.json()
                        
                    # Fetch progress information
                    progress_response = await client.get(
                        f"http://localhost:8001/progress/{chat_id}/{tutorial_id}"
                    )
                    if progress_response.status_code == 200:
                        progress = progress_response.json()
                        tutorial_context['completed_chapters'] = progress.get('completed_chapters', [])
                        
            except Exception as e:
                print(f"Error fetching tutorial context: {e}")

        # Add tutorial context to system message if available
        if tutorial_context:
            system_message = {
                "role": "system",
                "content": f"""You are a helpful teaching assistant guiding the user through a tutorial.

Current Tutorial Context:
- Tutorial: {tutorial_context['tutorial_title']}
- Current Chapter: {tutorial_context['chapter_title']} (Chapter {tutorial_context['order']} of {tutorial_context.get('total_chapters', 0)})
- Total Steps in Chapter: {len(tutorial_context['steps'])}

Chapter Overview:
{tutorial_context['content']}

Steps to Complete:
{chr(10).join(f"Step {step['order']}: {step['title']}" for step in tutorial_context['steps'])}


Instructions:
1. Guide the user through the current step
2. Provide clear explanations and help when needed
3. End your explanation with "||confirm||" to ask for step completion
4. When user confirms completion, move to the next step

Remember:
- Stay focused on the current step
- Provide detailed help when requested
- Always end step explanations with "||confirm||"

Begin by explaining the current step.
"""
            }
            messages.insert(0, system_message)

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
        resp = db_service.add_message(chat_id, "user", messages[-1]['content'])
        message = resp[0]
        chat_id = resp[1]
        interaction_id = resp[2]

        # Create a new list of messages with the updated last message
        messages.append(ChatMessage(
            role=messages[-1]['role'],
            content=messages[-1]['content'],
            chat_id=chat_id,
            interaction_id=message.interaction_id
        ))
        
        # Create a new request with the updated messages
        updated_request = ChatRequest(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Return a StreamingResponse
        return StreamingResponse(
            generate_stream(updated_request, chat_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in chat_stream: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

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
async def get_chats():
    """Get all chats with their tutorial status"""
    try:
        chats = db_service.get_all_chats()
        chat_list = []
        
        async with httpx.AsyncClient() as client:
            for chat in chats:
                # Check tutorial status and progress from docstore
                tutorial_info = None
                try:
                    progress_response = await client.get(f"http://localhost:8001/progress/{chat.id}")
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        if progress_data.get('tutorial_id'):
                            # Get tutorial details
                            tutorial_response = await client.get(
                                f"http://localhost:8001/tutorials/{progress_data['tutorial_id']}"
                            )
                            if tutorial_response.status_code == 200:
                                tutorial = tutorial_response.json()
                                tutorial_info = {
                                    "id": tutorial['id'],
                                    "title": tutorial['title'],
                                    "progress": {
                                        "total_steps": progress_data['total_steps'],
                                        "completed_steps": progress_data['completed_steps'],
                                        "current_chapter": progress_data['current_chapter'],
                                        "progress_percentage": progress_data['progress_percentage']
                                    }
                                }
                except Exception as e:
                    logger.error(f"Error fetching tutorial info for chat {chat.id}: {str(e)}")

                chat_list.append({
                    "id": chat.id,
                    "title": chat.title,
                    "summary": chat.summary,
                    "created_at": chat.created_at,
                    "updated_at": chat.updated_at,
                    "tutorial": tutorial_info
                })
            
        return chat_list
    except Exception as e:
        logger.error(f"Error fetching chat list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
                'assistant_summary': summaries.get('assistant_summary'),
                'created_at': msg.created_at.isoformat() if msg.created_at else None  # Add timestamp
            }
            interactions.append(current_interaction)
        current_interaction['messages'].append({
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat() if msg.created_at else None  # Add timestamp for each message
        })
    
    return {
        "id": chat.id,
        "title": chat.title,
        "interactions": interactions,
        "summary": chat.summary
    }

@app.get("/memories/query")
async def query_memories(
    query: str,
    num_results: int = Query(default=3, ge=1, le=10),
    min_similarity: float = Query(default=0.1, ge=0, le=1.0)
):
    """Query the memory collection for relevant memories"""
    result = await memory_service.query_memories(
        query=query,
        num_results=num_results,
        min_similarity=min_similarity
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No memories found")
    return result

@app.get("/memories/chat/{chat_id}")
async def get_chat_memories(
    chat_id: int,
    interaction_id: Optional[int] = None
):
    """Get memories for a specific chat"""
    memories = await memory_service.get_chat_memories(
        chat_id=chat_id,
        interaction_id=interaction_id
    )
    if not memories:
        raise HTTPException(status_code=404, detail="No memories found")
    return memories

