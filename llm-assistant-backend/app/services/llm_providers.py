from abc import ABC, abstractmethod
from typing import AsyncGenerator, List
from app.models.chat import ChatMessage
import os
import logging
from llama_cpp import Llama
import openai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_stream(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def generate_completion(self, prompt: str, temperature: float, max_tokens: int) -> str:
        pass

class LocalLLMProvider(BaseLLMProvider):
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please download a GGUF format model and set MODEL_PATH correctly."
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

    async def generate_stream(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
        formatted_messages = []
        for msg in messages:
            role_prefix = "User: " if msg.role == "user" else "Assistant: " if msg.role == "assistant" else "System: "
            formatted_messages.append(f"{role_prefix}{msg.content}")
        
        prompt = "\n".join(formatted_messages) + "\nAssistant:"

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

    async def generate_completion(self, prompt: str, temperature: float, max_tokens: int) -> str:
        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.1,
            top_k=10,
            repeat_penalty=1.2,
            stop=["Question:", "Context:", "System:"],
        )
        return response['choices'][0]['text'].strip()

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_stream(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_completion(self, prompt: str, temperature: float, max_tokens: int) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content 

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate_stream(self, messages: List[ChatMessage], temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
        # Convert our messages format to Anthropic's format
        formatted_messages = []
        for msg in messages:
            if msg.role == "user":
                formatted_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "system":
                # Anthropic doesn't have a system role, so we prepend it to the first user message
                if formatted_messages and formatted_messages[0]["role"] == "user":
                    formatted_messages[0]["content"] = f"{msg.content}\n\n{formatted_messages[0]['content']}"
                else:
                    formatted_messages.insert(0, {"role": "user", "content": msg.content})

        try:
            stream = await self.client.messages.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.text:
                    yield chunk.delta.text

        except Exception as e:
            logging.error(f"Error in Claude stream generation: {str(e)}")
            raise

    async def generate_completion(self, prompt: str, temperature: float, max_tokens: int) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text

        except Exception as e:
            logging.error(f"Error in Claude completion: {str(e)}")
            raise 