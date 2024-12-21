from transformers import AutoTokenizer, BartForConditionalGeneration
import torch
import logging
import warnings
import time
from contextlib import nullcontext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress torch warnings about NumPy
warnings.filterwarnings("ignore", message="Failed to initialize NumPy")

class ConversationSummarizer:
    def __init__(self, model_name="sanjayuzu/facebook-bart-large-cnn-pretrained_text_summarization_samsum"):
        logger.info(f"Initializing summarizer with model: {model_name}")
        try:
            # Device selection for Apple Silicon
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
                logger.info("Using Apple Metal GPU (MPS)")
            else:
                self.device = torch.device("cpu")
                logger.info("MPS not available, using CPU")
            
            # Load model and tokenizer with device placement
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = BartForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.backends.mps.is_available() else torch.float32
            )
            self.model.to(self.device)
            logger.info(f"Model loaded successfully. Model device: {next(self.model.parameters()).device}")
        except Exception as e:
            logger.error(f"Error loading summarizer model: {str(e)}")
            raise
        
    def summarize(self, conversation_history):
        start_time = time.time()
        logger.info("Starting summarization process...")
        
        formatted_convo = self._format_conversation(conversation_history)
        format_time = time.time()
        logger.info(f"Conversation formatting took {format_time - start_time:.2f} seconds")

        # Add instructions as a separate prompt or use a system message if your pipeline supports it.
        instructions = "Describe very briefly what the assistant answered:"
        full_input = instructions + formatted_convo
            
        logger.info(f"Formatted conversation: {formatted_convo[:200]}...")

        # Tokenize and move to device immediately
        tokenize_start = time.time()
        inputs = self.tokenizer(
            full_input,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        tokenize_time = time.time()
        logger.info(f"Tokenization took {tokenize_time - tokenize_start:.2f} seconds")
        
        # Generate summary
        generate_start = time.time()
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=1024,
                min_length=5,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True,
            )
        generate_time = time.time()
        logger.info(f"Summary generation took {generate_time - generate_start:.2f} seconds")
        
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        decode_time = time.time()
        logger.info(f"Decoding took {decode_time - generate_time:.2f} seconds")
        
        total_time = time.time() - start_time
        logger.info(f"Total summarization process took {total_time:.2f} seconds")
        
        return summary, total_time  # Return both summary and timing
            
    
    def _format_conversation(self, conversation_history):
        # Only include the conversation text, not the instructions
        parts = []
        for turn in conversation_history:
            role = turn['role'].lower()
            content = turn['content'].strip()
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _log_gpu_memory():
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**2  # Convert to MB
            memory_reserved = torch.cuda.memory_reserved(0) / 1024**2
            logger.info(f"GPU Memory: Allocated: {memory_allocated:.2f}MB, Reserved: {memory_reserved:.2f}MB")