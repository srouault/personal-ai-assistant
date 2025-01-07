import os
os.environ["LANGCHAIN_DISABLE_TELEMETRY"] = "true"

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document as LangchainDocument
from app.models.database import Document, SessionLocal
import logging

def load_documents(documents_dir="documents"):
    # Use the same embedding model configuration as DocumentService
    embedding_model = HuggingFaceEmbeddings(
        model_name="models/embeddings",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Initialize ChromaDB with context collection
    persist_directory = "data/chromadb"
    context_db = Chroma(
        collection_name="context",
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )

    # Create DB session
    db = SessionLocal()
    
    # Load documents from the documents directory
    vector_documents = []
    loaded_sources = set()
    
    for filename in os.listdir(documents_dir):
        if filename.endswith(".txt"):
            source_name = os.path.basename(filename)
            
            # Check if document already exists in SQLite
            existing_doc = db.query(Document).filter_by(filename=source_name).first()
            if existing_doc:
                logging.info(f"Document {source_name} already exists in database, skipping")
                continue

            if source_name in loaded_sources:
                logging.info(f"Document {source_name} already processed in this session, skipping")
                continue

            file_path = os.path.join(documents_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                    # Store full document in SQLite
                    doc = Document(
                        filename=source_name,
                        content=text,
                        collection='context'
                    )
                    db.add(doc)
                    db.commit()
                    db.refresh(doc)
                    
                    # Create vector store document with reference to SQLite document
                    vector_documents.append(
                        LangchainDocument(
                            page_content=text,
                            metadata={
                                "source": source_name,
                                "document_id": doc.id,  # Reference to SQLite document
                                "collection": "context"
                            }
                        )
                    )
                loaded_sources.add(source_name)
                logging.info(f"Loaded document: {source_name}")
            except Exception as e:
                logging.error(f"Error loading {source_name}: {str(e)}")
                db.rollback()

    # Add documents to ChromaDB context collection
    if vector_documents:
        context_db.add_documents(vector_documents)
        context_db.persist()
        logging.info(f"Added {len(vector_documents)} documents to the context collection")
    else:
        logging.warning("No documents found to load")
    
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_documents() 