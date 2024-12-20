from transformers import AutoTokenizer, BartForConditionalGeneration
import torch
import logging
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress torch warnings about NumPy
warnings.filterwarnings("ignore", message="Failed to initialize NumPy")

class ConversationSummarizer:
    def __init__(self, model_name="sanjayuzu/facebook-bart-large-cnn-pretrained_text_summarization_samsum"):
        logger.info(f"Initializing summarizer with model: {model_name}")
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = BartForConditionalGeneration.from_pretrained(model_name)
            self.model.to(self.device)
            logger.info("Summarizer model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading summarizer model: {str(e)}")
            raise
        
    def summarize(self, conversation_history):
        formatted_convo = self._format_conversation(conversation_history)

        # Add instructions as a separate prompt or use a system message if your pipeline supports it.
        instructions = "Summarize the following conversation, focus only on key points. Make sure the summary is in third person."
        full_input = instructions + formatted_convo
            
        logger.info(f"Formatted conversation: {formatted_convo[:200]}...")

        # Tokenize
        inputs = self.tokenizer(
            formatted_convo,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=60,
                min_length=5,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True,
            )
        
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        logger.info("=== Generated Summary ===")
        logger.info(f"{summary}")
        logger.info("=======================")
        return summary
            
    
    def _format_conversation(self, conversation_history):
        # Only include the conversation text, not the instructions
        parts = []
        for turn in conversation_history:
            role = turn['role'].lower()
            content = turn['content'].strip()
            parts.append(f"{role}: {content}")
        return "\n".join(parts)