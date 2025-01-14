from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.document_service import DocumentService
from app.models.document import QueryRequest, QueryResponse, Memory, MemoryResponse
from app.models.database import SessionLocal, LearningPath, Tutorial, TutorialChapter, UserProgress
from sqlalchemy.sql import func
import logging

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
        chapters = db.query(TutorialChapter)\
            .filter(TutorialChapter.tutorial_id == tutorial_id)\
            .order_by(TutorialChapter.order)\
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
                UserProgress.user_id == chat_id,
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
            user_id=chat_id,
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

@app.get("/tutorials/{tutorial_id}/chapters/{chapter_id}/context")
def get_tutorial_chapter_context(tutorial_id: int, chapter_id: int):
    """Get the context for a specific tutorial chapter"""
    db = SessionLocal()
    try:
        chapter = db.query(TutorialChapter)\
            .filter(
                TutorialChapter.tutorial_id == tutorial_id,
                TutorialChapter.id == chapter_id
            ).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
            
        tutorial = db.query(Tutorial)\
            .filter(Tutorial.id == tutorial_id)\
            .first()
            
        # Get total number of chapters
        total_chapters = db.query(TutorialChapter)\
            .filter(TutorialChapter.tutorial_id == tutorial_id)\
            .count()
            
        return {
            "tutorial_id": tutorial_id,
            "tutorial_title": tutorial.title,
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "content": chapter.content,
            "order": chapter.order,
            "total_chapters": total_chapters
        }
    finally:
        db.close()