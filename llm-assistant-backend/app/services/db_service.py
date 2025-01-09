from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..models.database import Base, Chat, Message, InteractionSummary, InteractionContext
from typing import List, Optional, Dict
from datetime import datetime
import aiohttp
import logging

class DatabaseService:
    def __init__(self, database_url: str = "sqlite:///./chats.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.docstore_url = "http://localhost:8001"  # Docstore service URL
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def create_chat(self, title: str) -> Chat:
        with self.get_session() as session:
            chat = Chat(title=title)
            session.add(chat)
            session.commit()
            session.refresh(chat)
            return chat
    
    def get_chat(self, chat_id: int) -> Optional[Chat]:
        with self.get_session() as session:
            return session.query(Chat).filter(Chat.id == chat_id).first()

    def get_interaction_summaries(self, chat_id: int) -> List[InteractionSummary]:
        with self.get_session() as session:
            return session.query(InteractionSummary)\
                .filter(InteractionSummary.chat_id == chat_id)\
                .order_by(InteractionSummary.interaction_id)\
                .all()
    
    def get_all_chats(self) -> List[Chat]:
        with self.get_session() as session:
            return session.query(Chat).order_by(Chat.updated_at.desc()).all()
    
    def add_message(self, chat_id: int, role: str, content: str) -> Message:
        with self.get_session() as session:
            # Get the latest interaction_id for this chat
            latest_message = session.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.interaction_id.desc())\
                .first()
            
            # If this is a user message, increment the interaction_id
            # If it's an assistant message, use the current interaction_id
            if role == 'user':
                interaction_id = (latest_message.interaction_id + 1) if latest_message else 1
            else:  # assistant
                interaction_id = latest_message.interaction_id if latest_message else 1
            
            message = Message(
                chat_id=chat_id,
                role=role,
                content=content,
                interaction_id=interaction_id
            )
            session.add(message)
            
            # Update chat's updated_at timestamp
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            chat.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(message)
            return message, chat_id, interaction_id
    
    def get_chat_messages(self, chat_id: int) -> List[Message]:
        with self.get_session() as session:
            return session.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.interaction_id, Message.role)\
                .all()
    
    def update_chat_summary(self, chat_id: int, summary: str):
        with self.get_session() as session:
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            chat.summary = summary
            session.commit() 

    def delete_chat(self, chat_id: int):
        with self.get_session() as session:
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                session.delete(chat)
                session.commit()
                return True
            return False

    def get_or_create_chat(self, chat_id: int, default_title: str = None) -> Chat:
        with self.get_session() as session:
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                # If chat doesn't exist, create it with a default title
                title = default_title or f"Chat {chat_id}"
                chat = Chat(id=chat_id, title=title)
                session.add(chat)
                session.commit()
                session.refresh(chat)
            return chat
    
    def add_interaction_summary(
        self, 
        chat_id: int, 
        interaction_id: int, 
        user_summary: str,
        assistant_summary: str
    ) -> InteractionSummary:
        with self.get_session() as session:
            interaction_summary = InteractionSummary(
                chat_id=chat_id,
                interaction_id=interaction_id,
                user_summary=user_summary,
                assistant_summary=assistant_summary
            )
            session.add(interaction_summary)
            session.commit()
            session.refresh(interaction_summary)
            return interaction_summary
    
    def get_interaction_summaries(self, chat_id: int) -> List[InteractionSummary]:
        with self.get_session() as session:
            return session.query(InteractionSummary)\
                .filter(InteractionSummary.chat_id == chat_id)\
                .order_by(InteractionSummary.interaction_id)\
                .all()
    
    def get_interaction_summary(self, chat_id: int, interaction_id: int) -> Optional[InteractionSummary]:
        with self.get_session() as session:
            return session.query(InteractionSummary)\
                .filter(
                    InteractionSummary.chat_id == chat_id,
                    InteractionSummary.interaction_id == interaction_id
                ).first()

    def get_latest_chat_id(self) -> Optional[int]:
        with self.get_session() as session:
            latest_chat = session.query(Chat).order_by(Chat.id.desc()).first()
            return latest_chat.id if latest_chat else None

    def get_latest_interaction_id(self, chat_id: int) -> Optional[int]:
        with self.get_session() as session:
            latest_interaction = session.query(Message)\
                .filter(Message.chat_id == chat_id)\
                .order_by(Message.interaction_id.desc())\
                .first()
            return latest_interaction.interaction_id if latest_interaction else None

    def add_interaction_context(
        self,
        chat_id: int,
        interaction_id: int,
        context_document_id: Optional[int] = None,
        similarity_score: Optional[float] = None,
        memory_msg_id: Optional[int] = None
    ) -> InteractionContext:
        with self.get_session() as session:
            context = InteractionContext(
                chat_id=chat_id,
                interaction_id=interaction_id,
                context_document_id=context_document_id,
                similarity_score=similarity_score,
                context_memory_message_id=memory_msg_id
            )
            session.add(context)
            session.commit()
            session.refresh(context)
            return context

    async def get_document_content(self, document_id: int) -> Optional[str]:
        """Retrieve document content from docstore service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.docstore_url}/documents/{document_id}") as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("content")
                    else:
                        logging.error(f"Error fetching document {document_id}: {response.status}")
                        return None
        except Exception as e:
            logging.error(f"Error getting document content: {str(e)}")
            logging.exception("Full traceback:")
            return None

    async def get_interaction_contexts(self, chat_id: int, interaction_id: int) -> List[Dict]:
        """
        Retrieve context documents for a specific chat interaction
        Returns a list of dicts containing document content and metadata
        """
        with self.get_session() as session:
            contexts = session.query(InteractionContext)\
                .filter(
                    InteractionContext.chat_id == chat_id,
                    InteractionContext.interaction_id == interaction_id
                )\
                .all()
            
            result = []
            for context in contexts:
                if context.context_document_id is not None:


                    # Get the full document content from docstore service
                    document_content = await self.get_document_content(
                        context.context_document_id
                    )
                elif context.context_memory_message_id is not None:
                    # Get the assistant message content from the database
                    document_content = await self.get_message_by_id(context.context_memory_message_id)
                
                if document_content:
                    result.append({
                        'document_id': context.context_document_id,
                        'message_id': context.context_memory_message_id,
                        'content': document_content,
                        'similarity_score': context.similarity_score,
                        'created_at': context.created_at
                    })
            
            return result

    async def get_last_interaction_contexts(self, chat_id: int) -> List[Dict]:
        """
        Retrieve context documents for the most recent interaction of a chat
        Returns a list of dicts containing document content and metadata
        """
        with self.get_session() as session:
            # First get the latest interaction_id for this chat
            latest_interaction = session.query(InteractionContext)\
                .filter(InteractionContext.chat_id == chat_id)\
                .order_by(InteractionContext.interaction_id.desc())\
                .first()
            
            if not latest_interaction:
                return []
            
            # Then get all contexts for this interaction
            return await self.get_interaction_contexts(
                chat_id=chat_id,
                interaction_id=latest_interaction.interaction_id
            )

    async def get_assistant_message_id_and_content_by_chat_id_interaction_id(self, chat_id: int, interaction_id: int, role: str = "assistant") -> List[Dict]:
        with self.get_session() as session:
            messages = session.query(Message)\
                .filter(
                    Message.chat_id == chat_id,
                    Message.interaction_id == interaction_id,
                    Message.role == role
                )\
                .all()

            result = []
            for message in messages:
                result.append({
                    'message_id': message.id,
                    'content': message.content
                })

            return result

    async def get_message_by_id(self, message_id: int) -> Optional[str]:
        with self.get_session() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            return message.content if message else None