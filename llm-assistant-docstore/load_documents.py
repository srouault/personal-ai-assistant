import os
os.environ["LANGCHAIN_DISABLE_TELEMETRY"] = "true"

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import logging

def load_documents(documents_dir="documents"):
    # Use the same embedding model configuration as DocumentService
    embedding_model = HuggingFaceEmbeddings(
        model_name="models/embeddings",  # Local path to model
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Initialize ChromaDB with context collection
    persist_directory = "data/chromadb"
    context_db = Chroma(
        collection_name="context",  # Specify the context collection
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )

    # Load documents from the documents directory
    documents = []
    loaded_sources = set()  # Track which files we've already loaded
    
    for filename in os.listdir(documents_dir):
        if filename.endswith(".txt"):  # Add more extensions if needed
            # Use just the filename without directory prefix for consistency
            source_name = os.path.basename(filename)
            
            # Check if document already exists in the DB
            existing_docs = context_db._collection.get(
                where={"source": source_name}
            )
            if existing_docs['ids']:
                logging.info(f"Document {source_name} already exists in context collection, skipping")
                continue

            if source_name in loaded_sources:
                logging.info(f"Document {source_name} already processed in this session, skipping")
                continue

            file_path = os.path.join(documents_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": source_name,  # Use normalized filename
                                "full_document": text,
                                "collection": "context"  # Add collection metadata
                            }
                        )
                    )
                loaded_sources.add(source_name)
                logging.info(f"Loaded document: {source_name}")
            except Exception as e:
                logging.error(f"Error loading {source_name}: {str(e)}")

    # Add documents to ChromaDB context collection
    if documents:
        context_db.add_documents(documents)
        context_db.persist()
        logging.info(f"Added {len(documents)} documents to the context collection")
    else:
        logging.warning("No documents found to load")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_documents() 