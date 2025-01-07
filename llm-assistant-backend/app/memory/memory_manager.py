from .summarizer import ConversationSummarizer
import asyncio
import logging


logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, llm_service):
        logger.info("Initializing MemoryManager")
        self.summarizer = ConversationSummarizer(llm_service)
        self.conversation_history = []
        self.current_summary = None
        self.max_history_length = 5  # Maximum number of turns to keep
        
    async def add_exchange(self, user_message, assistant_response, chat_id=None, db_service=None, context_documents=None):
        """Add a new exchange to the conversation history."""
        logger.info(f"Adding new exchange - User: {user_message[:50]}...")
        
        # Get the current interaction_id
        if chat_id and db_service:
            interaction_id = db_service.get_latest_interaction_id(chat_id) + 1
        
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
            if chat_id is not None and db_service is not None:
                db_service.add_interaction_summary(
                    chat_id, 
                    interaction_id, 
                    user_summary,
                    assistant_summary
                )
                
            # Store context documents if provided
            if context_documents:
                for key in context_documents:
                    doc = context_documents[key]
                    db_service.add_interaction_context(
                        chat_id=chat_id,
                        interaction_id=interaction_id,
                        context_document_id=doc['document_id'],
                        similarity_score=doc['similarity']
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