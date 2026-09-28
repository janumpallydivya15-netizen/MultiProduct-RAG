# Product AI RAG — Multimodal Product Knowledge Assistant

## 1. Project Overview
A sophisticated, multimodal Retrieval-Augmented Generation (RAG) system built to serve as an intelligent product assistant. It ingests product manuals, processes multimodal context, and uses Google's Gemini models to provide grounded, highly accurate answers and troubleshooting steps with explicit page citations.

## 2. Problem Statement
Users often struggle to locate specific troubleshooting steps, configuration parameters, or error code meanings buried in lengthy product manuals. This project solves that problem by semantically indexing documentation and leveraging Gemini to instantly synthesize answers anchored to verified manual pages.

## 3. Key Features
- **Multimodal Image Analysis**: Analyze product images using Gemini Vision.
- **Knowledge Base Ingestion**: Automatic PDF parsing (PyMuPDF) and OCR fallback (EasyOCR).
- **Grounded AI Assistant**: Strict anti-hallucination prompts guarantee answers are derived solely from indexed context.
- **Step-by-Step Troubleshooting**: Dedicated AI diagnostic workflow for error codes and symptoms.
- **Source Citations**: Every generated fact includes direct references to the source file and page number.
- **Persistent Vector DB**: Uses ChromaDB to locally store semantic embeddings.

## 4. System Architecture
The application runs as a lightweight Single Page Application (SPA) interfacing with a Flask API. 

## 5. Technology Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python, Flask
- **LLM**: Google Gemini API (gemini-3.5-flash-lite / gemini-3.8-flash)
- **Vector Store**: ChromaDB (Local Persistent)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Extraction**: PyMuPDF, EasyOCR

## 6. Application Workflow
**Ingestion Flow:**
Product Documentation -> PyMuPDF / OCR -> Chunking -> SentenceTransformers -> ChromaDB

**RAG Workflow:**
Semantic Retrieval -> Gemini Generation -> Grounded Answer -> Page Citations

**Troubleshooting Workflow:**
User Problem -> Product Context -> ChromaDB Retrieval -> Relevant Manual Chunks -> Gemini Grounded Generation -> Diagnosis + Resolution Steps + Citations

## 7. Project Structure
\\\
project-root/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── core/
│   ├── doc_processor.py
│   ├── embeddings.py
│   ├── gemini_client.py
│   ├── ocr_engine.py
│   ├── rag_pipeline.py
│   └── vector_store.py
├── routes/
├── templates/
├── static/
└── data/
\\\

## 8. Installation
1. Clone repository
2. Create virtual environment: \python -m venv .venv\
3. Activate virtual environment: \.\.venv\Scripts\activate\
4. Install requirements: \pip install -r requirements.txt\

## 9. Environment Configuration
Copy \.env.example\ to \.env\ and configure your Google Gemini API key.

## 10. Running the Application
Run the Flask development server:
\python app.py\
Open \http://localhost:5000\ in your browser.

## 11. API Endpoints
- \POST /api/v1/vision/analyze\: Analyzes an uploaded product image.
- \POST /api/v1/documents/upload\: Ingests and indexes a document.
- \GET /api/v1/documents\: Lists indexed documents.
- \DELETE /api/v1/documents/<doc_id>\: Deletes an indexed document.
- \POST /api/v1/rag/ask\: Generates a grounded RAG response to a question.
- \POST /api/v1/troubleshooting/diagnose\: Generates a structured json diagnosis.
- \GET /api/v1/system/health\: Returns API health status.

## 12. Security Notes
Do NOT commit your \.env\ file. The application requires an active Gemini API key.

## 13. Limitations
- Requires a valid Gemini API key.
- Gemini usage is subject to API quotas/rate limits.
- ChromaDB is currently local/persistent.
- Authentication/multi-user access is not implemented.
- Answers depend entirely on the quality and coverage of the indexed documentation.

## 14. Author/Project Information
Developed as part of the Advanced Agentic Coding initiative.
