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
        
        # Create conversation for summarization
        conversation = [
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'content': assistant_response}
        ]
        
        try:
            # Generate summary for this interaction
            logger.info("Starting interaction summarization...")
            loop = asyncio.get_event_loop()
            summary_result = await loop.run_in_executor(
                None,
                self.summarizer.summarize,
                conversation  # Only summarize current interaction
            )
            interaction_summary, processing_time = summary_result
            
            # Store interaction summary if we have database access
            if chat_id is not None and db_service is not None:
                db_service.add_interaction_summary(chat_id, interaction_id, interaction_summary)
            
            logger.info(f"Interaction summary generated in {processing_time:.2f}s")
            
            # Now update the overall chat summary
            self.conversation_history.extend(conversation)
            if len(self.conversation_history) > self.max_history_length * 2:
                self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
            
            overall_summary_result = await loop.run_in_executor(
                None,
                self.summarizer.summarize,
                self.conversation_history
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