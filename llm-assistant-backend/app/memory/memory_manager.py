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
        
    async def add_exchange(self, user_message, assistant_response):
        """Add a new exchange to the conversation history."""
        logger.info(f"Adding new exchange - User: {user_message[:50]}...")
        logger.info(f"Current history length: {len(self.conversation_history)}")
        
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': assistant_response
        })
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_history_length * 2:
            logger.info("Trimming conversation history")
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
        
        # Run summarization in a thread to avoid blocking
        try:
            logger.info("Starting summarization process...")
            loop = asyncio.get_event_loop()
            self.current_summary = await loop.run_in_executor(
                None,
                self.summarizer.summarize,
                self.conversation_history
            )
            # Enhanced summary logging
            logger.info("=== New Conversation Summary ===")
            logger.info(f"{self.current_summary}")
            logger.info("==============================")
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            logger.exception("Full traceback:")
            self.current_summary = "Error generating summary"
        
    async def get_current_summary(self):
        """Get the current conversation summary."""
        return self.current_summary
    
    async def get_conversation_history(self):
        """Get the full conversation history."""
        return self.conversation_history 