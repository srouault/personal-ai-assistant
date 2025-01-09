import os
os.environ["LANGCHAIN_DISABLE_TELEMETRY"] = "true"

from app.services.document_service import DocumentService
import logging

def load_documents(documents_dir="documents"):
    # Initialize document service
    document_service = DocumentService()
    
    # Load documents from the documents directory
    loaded_sources = set()
    
    for filename in os.listdir(documents_dir):
        if filename.endswith(".txt"):
            source_name = os.path.basename(filename)
            
            if source_name in loaded_sources:
                logging.info(f"Document {source_name} already processed in this session, skipping")
                continue

            file_path = os.path.join(documents_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                # Use document service to add the document
                document_service.add_document(
                    filename=source_name,
                    content=text,
                    collection="context"
                )
                
                loaded_sources.add(source_name)
                logging.info(f"Loaded document: {source_name}")
            except Exception as e:
                logging.error(f"Error loading {source_name}: {str(e)}")

    logging.info("Finished loading documents")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_documents() 