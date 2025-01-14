from llama_cpp import Llama
from app.models.chat import ChatMessage
import os
from pathlib import Path
from typing import Generator, Optional, AsyncGenerator, List, Dict
import logging
import aiohttp
import joblib
import json

class LLMService:
    def __init__(self, docstore_url: str = "http://localhost:8001", db_service=None):
        self.docstore_url = docstore_url
        self.db_service = db_service
        model_path = os.getenv("MODEL_PATH")
        self.classifier_model = joblib.load("app/models/prompt_classifier.joblib")

        # Define base system prompt
        self.base_system_prompt = """You are a helpful AI assistant with access to previous conversation history. 

When given factual context:
1. Only use information explicitly stated in the provided context
2. Say "I don't have enough information" when no context is provided unless the the user has a factual question
3. Never make assumptions or infer details on questions or topics that are not factual
4. Quote relevant parts of the context when appropriate
5. Be concise and direct"""

        # Define reference-specific system prompt
        self.reference_system_prompt = """You are a helpful AI assistant with access to previous conversation history. 
When given context about previous conversations:
1. First acknowledge the previous conversation, mentioning when it happened
2. Briefly summarize what was discussed
3. Then use that context to answer the current question
4. End your response with: 'If you want to go back to our chat click here: <<<chat_history>>>CHAT_ID,INTERACTION_ID<<<chat_history>>>'
   (Replace CHAT_ID and INTERACTION_ID with the actual values from the memory)"""

        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please download a GGUF format model and place it in the models directory, "
                "or set the MODEL_PATH environment variable to point to your model file."
            )
        
        logging.getLogger('llama_cpp').setLevel(logging.ERROR)
        
        try:
            self.llm = Llama(
                model_path=model_path,
                n_gpu_layers=32,
                verbose=False,
                n_ctx=32000
            )
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise
    
    async def generate_response_stream(self, messages: list[ChatMessage], temperature: float = 0.15, max_tokens: int = 150, context: str = None, prediction_type: str = "New") -> AsyncGenerator[str, None]:
        try:
            formatted_messages = []
            
            # Only add base system prompt if there's no system message in the messages
            system_prompt = self.reference_system_prompt if prediction_type == "Reference" else self.base_system_prompt
            formatted_messages.append(f"System: {system_prompt}")
            
            if context:
                formatted_messages.append(f"\nContext:\n{context}\n")
            
            # Add conversation history
            for msg in messages:
                if msg.role == "user":
                    formatted_messages.append(f"User: {msg.content}")
                elif msg.role == "system":
                    formatted_messages.append(f"Context: {msg.content}")
                elif msg.role == "assistant":
                    formatted_messages.append(f"Assistant: {msg.content}")
            
            prompt = "\n".join(formatted_messages)
            prompt += "\nAssistant:"

            # Generate streaming response
            stream = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.76,
                top_k=10,
                repeat_penalty=1.2,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                stop=["User:", "System:", "Assistant:"],
                stream=True
            )
            
            for output in stream:
                if output and 'choices' in output and len(output['choices']) > 0:
                    text = output['choices'][0]['text']
                    if text:
                        yield text

        except Exception as e:
            logging.error(f"Error in generate_response_stream: {str(e)}")
            logging.exception("Full traceback:")
            yield f"Error generating response: {str(e)}"

    async def get_context(self, query: str) -> Optional[str]:
        try:
            # Make request to docstore with new query format
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.docstore_url}/query",
                    json={
                        "query": query,
                        "num_results": 3,
                        "min_similarity": 0.25
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Check if we have results using new response format
                        if result.get("has_results") and result.get("results"):
                            # Use dict to deduplicate by source
                            unique_contexts = {}
                            
                            for doc_result in result["results"]:
                                source = doc_result["metadata"]["source"]
                                # Only add if we haven't seen this source before
                                if source not in unique_contexts:
                                    full_doc = doc_result["metadata"]["full_document"]
                                    unique_contexts[source] = {
                                        'text': f"Source: {source}\n\n{full_doc}",
                                        'document_id': doc_result["metadata"].get("document_id"),
                                        'similarity': doc_result["metadata"]["similarity"]
                                    }
                            
                            if not unique_contexts:
                                return None,None

                            # Combine unique contexts with separators
                            context = "\n\n---\n\n".join(
                                context_info['text'] for context_info in unique_contexts.values()
                            )
                            logging.info(f"Found {len(unique_contexts)} unique documents for context")
                            return context, unique_contexts
                            
                        return None,None
                    else:
                        logging.error(f"Error fetching context: {response.status}")
                        return None,None

        except Exception as e:
            logging.error(f"Error getting context: {str(e)}", exc_info=True)
            return None,None

    async def process_prompt(self, prompt: str) -> str:
        """Process a prompt with context from the document store"""
        try:
            response = await self.get_context(prompt)
            context = response[0] if response else None
            if context:
                full_prompt = f"""{self.system_prompt}

Context:
{context}

Question: {prompt}
Answer (based strictly on the above context):"""
            else:
                full_prompt = f"""{self.system_prompt}

Question: {prompt}
Answer: I don't have any relevant information in my context to answer this question."""

            response = self.llm(
                full_prompt,
                max_tokens=150,
                temperature=0.1,
                top_p=0.1,
                top_k=10,
                repeat_penalty=1.2,
                stop=["Question:", "Context:", "System:"],
            )

            return response['choices'][0]['text'].strip()

        except Exception as e:
            logging.error(f"Error processing prompt: {str(e)}")
            return f"Error processing prompt: {str(e)}"

    async def generate_summary(self, text: str, instruction: str, temperature: float = 0.3, max_tokens: int = 50) -> str:
        """Generate a concise summary using the LLM."""
        try:
            # Create the prompt
            prompt = f"""System: You are a precise summarization assistant. Your task is to create clear brief short 10 to 15 word summary.
            
Instruction: {instruction}

Text to summarize:
{text}

Summary:"""

            # Generate summary
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.1,  # More focused sampling
                top_k=10,
                repeat_penalty=1.2,
                stop=["Text to summarize:", "System:", "Instruction:", "Assistant:"],
            )

            return response['choices'][0]['text'].strip()

        except Exception as e:
            logging.error(f"Error generating summary: {str(e)}")
            logging.exception("Full traceback:")
            return f"Error generating summary: {str(e)}"

    async def generate_coaching_response(self, 
                                      user_input: str, 
                                      learning_path: dict, 
                                      current_tutorial: dict,
                                      user_progress: dict,
                                      context_docs: List[str] = None) -> str:
        # Construct a prompt that includes the learning context
        system_prompt = f"""You are an AI coach helping a user through the learning path: {learning_path['title']}.
Current tutorial: {current_tutorial['title']}
Progress: {user_progress['completed_tutorials']}/{user_progress['total_tutorials']} tutorials completed.

Your role is to:
1. Guide the user through the current tutorial
2. Answer questions about the material
3. Provide encouragement and support
4. Reference relevant documentation when helpful
5. Suggest next steps based on progress

Tutorial content: {current_tutorial['content']}
"""

        if context_docs:
            system_prompt += f"\nRelevant documentation: {' '.join(context_docs)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        response = await self.get_completion(messages)
        return response

    async def generate_starter_questions(self, learning_path: dict) -> List[str]:
        prompt = f"""Given this learning path: {learning_path['title']}
Description: {learning_path['description']}
Category: {learning_path['category']}

Generate 5 relevant starter questions that a user might want to ask to begin their learning journey.
Return the questions as a JSON array."""

        messages = [
            {"role": "system", "content": "You are an AI coach helping users start their learning journey."},
            {"role": "user", "content": prompt}
        ]

        response = await self.get_completion(messages)
        try:
            questions = json.loads(response)
            return questions
        except:
            # Fallback in case response isn't valid JSON
            return response.split('\n')