# System Architecture

## High-level architecture
The Product AI RAG application is a standard decoupled architecture, relying on a lightweight JavaScript SPA frontend interacting with a Flask REST backend. The backend manages local disk states (ChromaDB, PDF processing) and offloads LLM processing to the Google Gemini API.

## Frontend architecture
Vanilla JavaScript handles dynamic DOM updates without full page reloads, relying on etch calls to backend endpoints.

## Flask backend architecture
A Blueprint-based modular Flask application routing specific RAG, Knowledge Base, and Vision responsibilities into discrete controllers.

## Multimodal Vision flow
Images uploaded bypass the vector database and stream directly to Gemini Vision, falling back to EasyOCR text mapping to provide maximal context to the prompt.

## Document ingestion flow
PDF -> PyMuPDF (text extraction) -> Fallback EasyOCR -> Chunking (500 tokens) -> SentenceTransformers (all-MiniLM-L6-v2) -> ChromaDB embedding persistence.

## ChromaDB architecture
Local chromadb.PersistentClient saving SQLite and Parquet states to data/chromadb.

## RAG flow
Questions mapped to dense vectors -> Cosine Similarity search on ChromaDB -> Gemini Flash Lite context injection -> Markdown answer with Citations.

## Error handling flow
All exceptions are intercepted, scrubbed of Python tracebacks, and streamed back as standard {"success": false, "error": "Reason"} JSON objects for clean frontend rendering.
