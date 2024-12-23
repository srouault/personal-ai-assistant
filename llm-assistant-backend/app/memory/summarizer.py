import logging
import time
from keybert import KeyBERT


logger = logging.getLogger(__name__)

class ConversationSummarizer:
    def __init__(self, llm_service):
        logger.info("Initializing summarizer")
        try:
            # Initialize the KeyBERT model with specific embedding model
            self.kw_model = KeyBERT(model='all-MiniLM-L6-v2')  # or any other model you prefer

            self.llm_service = llm_service
            logger.info("Summarizer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing summarizer: {str(e)}")
            raise

    async def summarize(self, conversation_history, prompt=None):
        start_time = time.time()
        logger.info("Starting summarization process...")
        
        formatted_convo = self._format_conversation(conversation_history)
        format_time = time.time()
        logger.info(f"Conversation formatting took {format_time - start_time:.2f} seconds")

        # Create a more explicit prompt for the LLM
        if prompt is not None:
            if prompt == "User":
                instruction = (
                    "Your task is to describe in a clear, concise way what the user is asking or saying. "
                    "Focus on their main point or question. "
                    "Use third person perspective. "
                    "Keep it brief but informative. "
                    "Example format: 'The user asks about...' or 'The user explains that...'"
                )

            elif prompt == "Assistant":
                instruction = (
                    "Your task is to describe in a clear, concise way how the assistant responded. "
                    "Focus on the main points of the answer. "
                    "Use third person perspective. "
                    "Keep it brief, state whether or not the assistant was able to provide an answer "
                    "Example format: 'The assistant was able to explain about...' or 'The assistant could not provide information about...'"
                )

            try:
                # Use dedicated summary generation method
                generate_start = time.time()
                summary = await self.llm_service.generate_summary(
                    text=formatted_convo,
                    instruction=instruction,
                    temperature=0.3,
                    max_tokens=50
                )

                generate_time = time.time()
                logger.info(f"Summary generation took {generate_time - generate_start:.2f} seconds")

                total_time = time.time() - start_time
                logger.info(f"Total summarization process took {total_time:.2f} seconds")

                return summary.strip(), total_time

            except Exception as e:
                logger.error(f"Error during summarization: {str(e)}")
                logger.exception("Full traceback:")
                return "Error generating summary", time.time() - start_time

        else:  # For overall conversation summary
            try:
                # Use dedicated summary generation method
                generate_start = time.time()
                # Extract keywords
                keywords = self.kw_model.extract_keywords(formatted_convo, top_n=3)

                # log keywords
                logger.info(f"Extracted keywords: {keywords}")

                generate_time = time.time()
                logger.info(f"Summary generation took {generate_time - generate_start:.2f} seconds")

                total_time = time.time() - start_time
                logger.info(f"Total summarization process took {total_time:.2f} seconds")
                # keywords is a list of tuples, first attribute of the tuple is the string, join all by comma
                summary = ", ".join([keyword[0] for keyword in keywords])
                # remove 'assistant,' and 'assistant' from the summary
                summary = summary.replace('assistant,', '').replace(',assistant', '')
                return summary, total_time
            except Exception as e:
                logger.error(f"Error during summarization: {str(e)}")
                logger.exception("Full traceback:")
                return "Error generating summary", time.time() - start_time
        

    
    def _format_conversation(self, conversation_history):
        parts = []
        for turn in conversation_history:
            role = turn['role'].lower()
            content = turn['content'].strip()
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _format_user_message(self, conversation_history):
        for turn in conversation_history:
            if turn['role'].lower() == 'user':
                return turn['content'].strip()
        return ""