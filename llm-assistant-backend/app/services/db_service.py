from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..models.database import Base, Chat, Message, InteractionSummary
from typing import List, Optional
from datetime import datetime

class DatabaseService:
    def __init__(self, database_url: str = "sqlite:///./chats.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
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
            return message
    
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
    
    def add_interaction_summary(self, chat_id: int, interaction_id: int, summary: str) -> InteractionSummary:
        with self.get_session() as session:
            interaction_summary = InteractionSummary(
                chat_id=chat_id,
                interaction_id=interaction_id,
                summary=summary
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