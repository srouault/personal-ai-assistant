import os
import asyncio
from pathlib import Path
import logging
from app.services.document_service import DocumentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_documents():
    document_service = DocumentService()
    documents_dir = Path("documents")

    if not documents_dir.exists():
        logger.error(f"Documents directory not found: {documents_dir}")
        return

    # Supported file extensions
    supported_extensions = {'.txt', '.pdf'}

    for file_path in documents_dir.iterdir():
        if file_path.suffix.lower() in supported_extensions:
            try:
                logger.info(f"Processing file: {file_path}")
                with open(file_path, 'rb') as f:
                    content = f.read()
                await document_service.async_add_document(
                    filename=file_path.name,
                    content=content
                )
                logger.info(f"Successfully processed {file_path}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                logger.exception("Full traceback:")
        else:
            logger.warning(f"Skipping unsupported file: {file_path}")

if __name__ == "__main__":
    asyncio.run(load_documents()) 