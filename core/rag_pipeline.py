import os
from typing import Dict, Any, Optional
from core.doc_processor import DocumentProcessor
from core.embeddings import EmbeddingService
from core.vector_store import VectorStore
from core.gemini_client import GeminiClient
import config

class RAGPipeline:
    def __init__(self, doc_processor: DocumentProcessor = None, embedding_service: EmbeddingService = None, vector_store: VectorStore = None, gemini_client: GeminiClient = None):
        self.doc_processor = doc_processor or DocumentProcessor()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.gemini_client = gemini_client or GeminiClient()

    def ingest_document(self, file_path: str, doc_id: str, product_id: str = "general", original_filename: str = None) -> Dict[str, Any]:
        """Ingest document: extract text, chunk, compute embeddings, and index into ChromaDB."""
        filename = original_filename or os.path.basename(file_path)

        # Duplicate document check
        existing = self.vector_store.check_existing_document(filename, product_id)
        if existing:
            return {
                "status": "duplicate",
                "message": f"Document '{filename}' for product '{product_id}' is already indexed in ChromaDB.",
                "doc_id": existing["document_id"],
                "filename": filename,
                "product_id": product_id,
                "chunks": existing["chunks"],
                "indexed": True
            }

        # Step 1: Chunk document and extract page info
        processed_res = self.doc_processor.process_file(file_path, doc_id=doc_id, product_id=product_id, original_filename=filename)
        chunks = processed_res["chunks"]
        total_pages = processed_res["total_pages"]

        if not chunks:
            return {
                "status": "error",
                "message": "No text content could be extracted from document",
                "pages": total_pages,
                "chunks": 0,
                "indexed": False
            }

        # Step 2: Compute dense vector embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_service.generate_embeddings(texts)

        # Step 3: Index in ChromaDB
        self.vector_store.add_chunks(chunks, embeddings)

        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": filename,
            "product_id": product_id,
            "pages": total_pages,
            "chunks": len(chunks),
            "indexed": True
        }

    def query(self, question: str, product_id: Optional[str] = "all", top_k: int = None) -> Dict[str, Any]:
        """Retrieve relevant context from ChromaDB and generate grounded LLM answer."""
        k = top_k or config.TOP_K_RESULTS



        # Step 1: Embed query string
        query_vector = self.embedding_service.generate_single_embedding(question)

        # Step 2: Search ChromaDB vector store
        # Normalise product_id: treat 'all' or empty as global search
        search_product = product_id if (product_id and product_id.lower() != "all") else None
        context_chunks = self.vector_store.search(query_vector, top_k=k, product_id=search_product)


        for i, c in enumerate(context_chunks):
            meta = c.get("metadata", {})


        # Step 3: Generate grounded RAG answer with Gemini
        rag_response = self.gemini_client.generate_rag_response(
            question=question,
            contexts=context_chunks,
            product_id=product_id or "general"
        )

        return {
            "answer": rag_response.get("answer", ""),
            "sources": rag_response.get("sources", []),
            "retrieved_chunks": len(context_chunks)
        }

    def delete_document(self, doc_id: str) -> bool:
        """Remove document and its vector embeddings from ChromaDB."""
        try:
            return self.vector_store.delete_document(doc_id)
        except Exception as e:

            return False
    def diagnose(self, product_id: str, error_code: str, symptom: str, description: str, top_k: int = None) -> Dict[str, Any]:
        """Retrieve relevant context for troubleshooting and generate structured JSON response."""
        k = top_k or config.TOP_K_RESULTS
        
        query_parts = []
        if error_code: query_parts.append(f"Error {error_code}")
        if symptom: query_parts.append(symptom)
        if description: query_parts.append(description)
        
        query_str = " ".join(query_parts)
        if not query_str.strip():
            query_str = "troubleshooting guide"
            

        
        query_vector = self.embedding_service.generate_single_embedding(query_str)
        
        search_product = product_id if (product_id and product_id.lower() != "all") else None
        context_chunks = self.vector_store.search(query_vector, top_k=k, product_id=search_product)
        

        
        response = self.gemini_client.generate_troubleshooting_response(
            product_id=product_id or "general",
            error_code=error_code,
            symptom=symptom,
            description=description,
            contexts=context_chunks
        )
        
        return response
