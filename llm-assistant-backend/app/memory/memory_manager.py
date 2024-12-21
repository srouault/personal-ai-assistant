from .summarizer import ConversationSummarizer
import asyncio
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        logger.info("Initializing MemoryManager")
        self.summarizer = ConversationSummarizer()
        self.conversation_history = []
        self.current_summary = None
        self.max_history_length = 10  # Maximum number of turns to keep
        
    async def add_exchange(self, user_message, assistant_response, chat_id=None, db_service=None):
        """Add a new exchange to the conversation history."""
        logger.info(f"Adding new exchange - User: {user_message[:50]}...")
        
        # Get the current interaction_id
        if chat_id and db_service:
            latest_message = db_service.get_chat_messages(chat_id)[-1]
            interaction_id = latest_message.interaction_id
        
        try:
            # Generate summary for user message
            logger.info("Starting user message summarization...")
            loop = asyncio.get_event_loop()
            user_summary_result = await loop.run_in_executor(
                None,
                self.summarizer.summarize,
                [{'role': 'user', 'content': user_message}],
                "Describe very briefly what the user says or asks:"
            )
            user_summary, user_time = user_summary_result
            logger.info(f"User summary generated in {user_time:.2f}s")
            
            # Generate summary for assistant response
            logger.info("Starting assistant response summarization...")
            assistant_summary_result = await loop.run_in_executor(
                None,
                self.summarizer.summarize,
                [{'role': 'assistant', 'content': assistant_response}],
                "Describe very briefly what the assistant answered:"
            )
            assistant_summary, assistant_time = assistant_summary_result
            
            # Store interaction summaries if we have database access
            if chat_id is not None and db_service is not None:
                db_service.add_interaction_summary(
                    chat_id, 
                    interaction_id, 
                    user_summary,
                    assistant_summary
                )
            
            # Update the overall chat summary
            self.conversation_history.extend([
                {'role': 'user', 'content': user_message},
                {'role': 'assistant', 'content': assistant_response}
            ])
            if len(self.conversation_history) > self.max_history_length * 2:
                self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
            
            overall_summary_result = await loop.run_in_executor(
                None,
                self.summarizer.summarize,
                self.conversation_history,
                "Summarize the entire conversation:"
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