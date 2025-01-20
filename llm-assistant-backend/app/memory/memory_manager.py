from datetime import datetime

from aiohttp.abc import HTTPException

from .summarizer import ConversationSummarizer
import asyncio
import aiohttp
import logging


logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, llm_service, docstore_url: str = "http://localhost:8001", ):
        logger.info("Initializing MemoryManager")
        self.docstore_url = docstore_url
        self.summarizer = ConversationSummarizer(llm_service)
        self.conversation_history = []
        self.current_summary = None
        self.max_history_length = 5  # Maximum number of turns to keep
        
    async def add_exchange(self, user_message, assistant_response, chat_id=None, interaction_id=None, db_service=None, context_documents=None, classification="New", memory_msg=None):
        """Add a new exchange to the conversation history."""
        logger.info(f"Adding new exchange - User: {user_message[:50]}...")

        try:
            # Generate summary for user message
            logger.info("Starting user message summarization...")
            user_summary_result = await self.summarizer.summarize(
                [{'role': 'user', 'content': user_message}],
                "User"
            )
            user_summary, user_time = user_summary_result
            logger.info(f"User summary generated in {user_time:.2f}s")
            
            # Generate summary for assistant response
            logger.info("Starting assistant response summarization...")
            assistant_summary_result = await self.summarizer.summarize(
                [{'role': 'assistant', 'content': assistant_response}],
                "Assistant"
            )
            assistant_summary, assistant_time = assistant_summary_result
            
            # Store interaction summaries if we have database access
            if chat_id is not None and db_service is not None and interaction_id is not None:
                db_service.add_interaction_summary(
                    chat_id, 
                    interaction_id, 
                    user_summary,
                    assistant_summary
                )
                # Create a DateTime object with current time (or any other specific date)
                current_time = datetime.now()

                # Format it to ISO 8601 format, which is commonly used for timestamps
                iso_formatted_timestamp = current_time.isoformat()

                memory_data = {
                    'user': user_summary,
                    'assistant': assistant_summary,
                    'timestamp': iso_formatted_timestamp,
                    'chat_id': chat_id,
                    'interaction_id': interaction_id
                }

                if classification != "Reference":
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url=self.docstore_url + "/memories", json=memory_data) as response:
                            if response.status == 200:
                                data = await response.json()  # convert bytes to dict

                                logging.info(f"Memory added successfully: {data}")
                            else:
                                logging.error(f"Error fetching context: {response.status}")
                else:
                    logger.info("Skipping memory storage for reference-type query")
                
            # Store context documents if provided
            if context_documents:
                memory_msg_id = None
                if memory_msg is not None:
                    memory_msg_id = memory_msg['message_id']
                for key in context_documents:
                    doc = context_documents[key]
                    db_service.add_interaction_context(
                        chat_id=chat_id,
                        interaction_id=interaction_id,
                        context_document_id=doc['document_id'],
                        similarity_score=doc['similarity'],
                        memory_msg_id=memory_msg_id
                    )
            elif memory_msg is not None:
                db_service.add_interaction_context(
                    chat_id=chat_id,
                    interaction_id=interaction_id,
                    memory_msg_id=memory_msg[0]['message_id']
                )

            # retrieve chat histroy from db
            chat_history = []
            if chat_id is not None and db_service is not None:
                # messages = db_service.get_chat_messages(chat_id)

                summaries = db_service.get_interaction_summaries(chat_id)

                # add last max 10 summaries to chat history
                for message in summaries[-self.max_history_length:]:
                    chat_history.append({
                        'role': "user",
                        'content': message.user_summary
                    })
                    chat_history.append({
                        'role': "assistant",
                        'content': message.assistant_summary
                    })


            # Generate overall summary
            overall_summary_result = await self.summarizer.summarize(
                chat_history
            )
            overall_summary, _ = overall_summary_result
            
            if chat_id is not None and db_service is not None:
                db_service.update_chat_summary(chat_id, overall_summary)
            
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            logger.exception("Full traceback:")
        
    async def get_current_summary(self):
        """Get the current conversation summary."""
        return self.current_summary
    
    async def get_conversation_history(self):
        """Get the full conversation history."""
        return self.conversation_history 

    async def add_tutorial_exchange(
        self,
        user_message: str,
        chat_id: int,
        interaction_id: int,
        tutorial_context: dict,
        db_service=None
    ) -> None:
        """
        Add a lightweight memory record for tutorial interactions.
        Focuses on tracking step completion and progress.
        """
        
        # Check if user confirmed step completion
        step_completed = "yes" in user_message.lower() and "completed" in user_message.lower()
        
        # Extract step information from assistant message
        current_step = tutorial_context['current_step']
        step_info = f"Step {current_step['order']}: {current_step['title']}"
        
        # Create a concise memory entry
        assistant_summary = f"""Assistant explained: {step_info}"""
        user_summary = f"""'User {'' if step_completed else 'has not '}completed the step."""

        # Store interaction summaries if we have database access
        if chat_id is not None and db_service is not None and interaction_id is not None:
            db_service.add_interaction_summary(
                chat_id,
                interaction_id,
                user_summary,
                assistant_summary
            )