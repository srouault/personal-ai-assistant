from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.services.document_service import DocumentService
from app.models.document import QueryRequest, QueryResponse, Memory, MemoryResponse
from app.models.database import SessionLocal, LearningPath, Tutorial, UserProgress, Step, Chapter
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from typing import List, Optional

import logging

from .services.learning_path_service import LearningPathService

app = FastAPI()
doc_service = DocumentService()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/learning-paths")
def get_learning_paths():
    """Get all learning paths"""
    db = SessionLocal()
    try:
        paths = db.query(LearningPath).all()
        return [
            {
                "id": path.id,
                "title": path.title,
                "description": path.description,
                "category": path.category,
                "path_metadata": path.path_metadata,
                "created_at": path.created_at
            }
            for path in paths
        ]
    finally:
        db.close()

@app.get("/learning-paths/{path_id}")
def get_learning_path(path_id: int):
    """Get a specific learning path"""
    db = SessionLocal()
    try:
        path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
        if not path:
            raise HTTPException(status_code=404, detail="Learning path not found")
        return {
            "id": path.id,
            "title": path.title,
            "description": path.description,
            "category": path.category,
            "path_metadata": path.path_metadata,
            "created_at": path.created_at
        }
    finally:
        db.close()

@app.get("/learning-paths/{path_id}/tutorials")
def get_tutorials(path_id: int):
    """Get tutorials for a specific learning path"""
    db = SessionLocal()
    try:
        tutorials = db.query(Tutorial)\
            .filter(Tutorial.learning_path_id == path_id)\
            .order_by(Tutorial.order)\
            .all()
        
        return [
            {
                "id": tutorial.id,
                "title": tutorial.title,
                "description": tutorial.description,
                "content": tutorial.content,
                "order": tutorial.order,
                "estimated_duration": tutorial.estimated_duration,
                "created_at": tutorial.created_at
            }
            for tutorial in tutorials
        ]
    finally:
        db.close()

@app.get("/tutorials/{tutorial_id}/chapters")
def get_tutorial_chapters(tutorial_id: int):
    """Get chapters for a specific tutorial"""
    db = SessionLocal()
    try:
        chapters = db.query(Chapter)\
            .filter(Chapter.tutorial_id == tutorial_id)\
            .order_by(Chapter.order)\
            .all()
        
        return [
            {
                "id": chapter.id,
                "title": chapter.title,
                "content": chapter.content,
                "order": chapter.order
            }
            for chapter in chapters
        ]
    finally:
        db.close()

@app.get("/progress/{chat_id}/{tutorial_id}")
def get_tutorial_progress(chat_id: str, tutorial_id: int):
    """Get user's progress for a specific tutorial"""
    db = SessionLocal()
    try:
        progress = db.query(UserProgress)\
            .filter(
                UserProgress.chat_id == chat_id,
                UserProgress.tutorial_id == tutorial_id
            ).all()
        
        return {
            "completed_chapters": [p.chapter_id for p in progress if p.completed]
        }
    finally:
        db.close()

@app.post("/progress/{chat_id}/{tutorial_id}/{chapter_id}")
def update_chapter_progress(chat_id: str, tutorial_id: int, chapter_id: int):
    """Mark a chapter as completed"""
    db = SessionLocal()
    try:
        progress = UserProgress(
            chat_id=chat_id,
            tutorial_id=tutorial_id,
            chapter_id=chapter_id,
            completed=True,
            completed_at=func.now()
        )
        db.add(progress)
        db.commit()
        return {"status": "success"}
    finally:
        db.close()

@app.put("/progress/{chat_id}/step/{step_id}/{completed}")
async def update_step_progress(
    chat_id: str,
    step_id: int,
    completed: bool
):
    """Mark a chapter as completed"""
    db = SessionLocal()
    """Update user's progress for a specific step"""
    logging.info(f"Updating progress for chat_id: {chat_id}, step_id: {step_id}")
    
    try:
        # Get the step to find its chapter and tutorial
        step = db.query(Step).join(Chapter).join(Tutorial).filter(
            Step.id == step_id
        ).first()

        if not step:
            logging.error(f"Step {step_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Step {step_id} not found"
            )

        logging.info(f"Found step: {step.id} in chapter {step.chapter_id}")

        # Create or update progress
        progress = db.query(UserProgress).filter(
            UserProgress.chat_id == str(chat_id),
            UserProgress.step_id == step_id
        ).first()

        if not progress:
            logging.info(f"Creating new progress entry for chat_id: {chat_id}, step_id: {step_id}")
            # Create new progress entry
            progress = UserProgress(
                chat_id=str(chat_id),
                tutorial_id=step.chapter.tutorial_id,
                chapter_id=step.chapter_id,
                step_id=step_id,
                completed=completed,
                completed_at=func.now()
            )
            db.add(progress)
        else:
            logging.info(f"Updating existing progress for chat_id: {chat_id}, step_id: {step_id}")
            # Update existing progress
            progress.completed = True
            progress.completed_at = func.now()

        try:
            db.commit()
            logging.info("Progress updated successfully")
            return {"status": "success", "message": "Progress updated"}
        except Exception as e:
            db.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/documents")
async def upload_document(file: UploadFile):
    try:
        content = await file.read()
        doc_id = await doc_service.async_add_document(file.filename, content)
        return {"message": "Document added successfully", "doc_id": doc_id}
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories")
async def upload_memory(memory: Memory):
    try:
        datetime_str = memory.timestamp.isoformat()

        content = f"""Interaction between user and assistant, {memory.user}. The assistant answered with: {memory.assistant}.
                This interaction occurred at {datetime_str}."""

        mem_id = await doc_service.add_memory(content, {'timestamp': datetime_str, 'chat_id' : memory.chat_id, 'interaction_id': memory.interaction_id})
        return {"message": "Memory added successfully", "doc_id": mem_id}
    except Exception as e:
        logging.error(f"Error uploading memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        results = await doc_service.query_documents(
            query=request.query,
            num_results=request.num_results,
            min_relevance=request.min_relevance,
            min_similarity=request.min_similarity
        )
        return results
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recall", response_model=MemoryResponse)
async def query_memory(request: QueryRequest):
    try:
        results = await doc_service.query_memory(
            query=request.query,
            num_results=request.num_results,
            min_similarity=request.min_similarity
        )
        return results
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Get document content by ID"""
    try:
        document = await doc_service.get_document_content(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"content": document}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tutorials/{tutorial_id}/chapters/{chapter_id}/steps")
async def get_chapter_steps(
    tutorial_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    steps = db.query(Step).join(Chapter).filter(
        Chapter.tutorial_id == tutorial_id,
        Chapter.id == chapter_id
    ).order_by(Step.order).all()
    
    return steps

@app.get("/tutorials/{tutorial_id}/chapters/{chapter_id}/context")
async def get_chapter_context(
    tutorial_id: int,
    chapter_id: int,
    chat_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    chapter = db.query(Chapter).filter(
        Chapter.tutorial_id == tutorial_id,
        Chapter.id == chapter_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    steps = db.query(Step).filter(
        Step.chapter_id == chapter_id
    ).order_by(Step.order).all()

    # Get completed steps if chat_id is provided
    completed_steps = []
    if chat_id:
        completed_steps = db.query(UserProgress.step_id).filter(
            UserProgress.chat_id == chat_id,
            UserProgress.chapter_id == chapter_id,
            UserProgress.completed == True
        ).all()
        completed_steps = [s[0] for s in completed_steps]
    
    return {
        "tutorial_title": chapter.tutorial.title,
        "chapter_title": chapter.title,
        "order": chapter.order,
        "total_chapters": db.query(Chapter).filter(
            Chapter.tutorial_id == tutorial_id
        ).count(),
        "content": chapter.content,
        "steps": [
            {
                "id": step.id,
                "order": step.order,
                "title": step.title,
                "content": step.content,
                "expected_result": step.expected_result,
                "validation_type": step.validation_type,
                "completed": step.id in completed_steps
            }
            for step in steps
        ]
    }

