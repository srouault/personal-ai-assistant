import logging
import aiohttp
from typing import Optional, Dict, List

class MemoryService:
    def __init__(self, docstore_url: str = "http://localhost:8001"):
        self.docstore_url = docstore_url

    async def query_memories(
        self, 
        query: str,
        num_results: int = 3,
        min_similarity: float = 0.001
    ) -> Optional[Dict]:
        """Query the memory collection in docstore"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.docstore_url}/recall",
                    json={
                        "query": query,
                        "num_results": num_results,
                        "min_similarity": min_similarity
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("has_results"):
                            logging.info(f"Found {len(result['results'])} memories")
                            return result
                        else:
                            logging.info("No relevant memories found")
                            return None
                    else:
                        logging.error(f"Error querying memories: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"Error in query_memories: {str(e)}")
            logging.exception("Full traceback:")
            return None

    async def get_chat_memories(
        self,
        chat_id: int,
        interaction_id: Optional[int] = None
    ) -> List[Dict]:
        """Get memories for a specific chat and optionally a specific interaction"""
        try:
            url = f"{self.docstore_url}/memories/chat/{chat_id}"
            if interaction_id is not None:
                url += f"/{interaction_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        logging.info(f"Retrieved {len(result)} memories for chat {chat_id}")
                        return result
                    else:
                        logging.error(f"Error getting chat memories: {response.status}")
                        return []

        except Exception as e:
            logging.error(f"Error in get_chat_memories: {str(e)}")
            logging.exception("Full traceback:")
            return [] 