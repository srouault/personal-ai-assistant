from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database import LearningPath, Tutorial, UserProgress

class LearningPathService:
    def __init__(self, db: Session):
        self.db = db

    def create_learning_path(self, title: str, description: str, category: str, metadata: dict = None) -> LearningPath:
        learning_path = LearningPath(
            title=title,
            description=description,
            category=category,
            metadata=metadata or {}
        )
        self.db.add(learning_path)
        self.db.commit()
        self.db.refresh(learning_path)
        return learning_path

    def create_tutorial(self, 
                       learning_path_id: int, 
                       title: str, 
                       description: str, 
                       content: str,
                       order: int,
                       estimated_duration: int) -> Tutorial:
        tutorial = Tutorial(
            learning_path_id=learning_path_id,
            title=title,
            description=description,
            content=content,
            order=order,
            estimated_duration=estimated_duration
        )
        self.db.add(tutorial)
        self.db.commit()
        self.db.refresh(tutorial)
        return tutorial

    def get_learning_paths(self) -> List[LearningPath]:
        return self.db.query(LearningPath).all()

    def get_learning_path(self, path_id: int) -> Optional[LearningPath]:
        return self.db.query(LearningPath).filter(LearningPath.id == path_id).first()

    def get_tutorials_for_path(self, path_id: int) -> List[Tutorial]:
        return self.db.query(Tutorial)\
            .filter(Tutorial.learning_path_id == path_id)\
            .order_by(Tutorial.order)\
            .all()

    def track_progress(self, user_id: str, tutorial_id: int, completed: bool = False, notes: str = None):
        progress = self.db.query(UserProgress)\
            .filter(UserProgress.user_id == user_id, 
                   UserProgress.tutorial_id == tutorial_id)\
            .first()

        if not progress:
            progress = UserProgress(
                user_id=user_id,
                tutorial_id=tutorial_id,
                started_at=datetime.utcnow()
            )
            self.db.add(progress)

        if completed and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()

        if notes:
            progress.notes = notes

        self.db.commit()
        self.db.refresh(progress)
        return progress

    def get_user_progress(self, user_id: str, learning_path_id: int = None) -> List[UserProgress]:
        query = self.db.query(UserProgress).join(Tutorial)
        
        if learning_path_id:
            query = query.filter(Tutorial.learning_path_id == learning_path_id)
            
        return query.filter(UserProgress.user_id == user_id).all() 