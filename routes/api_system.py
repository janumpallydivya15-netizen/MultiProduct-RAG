from flask import Blueprint, jsonify
import config
from core.vector_store import VectorStore

api_system = Blueprint('api_system', __name__)
vector_store = VectorStore()

@api_system.route('/health', methods=['GET'])
def get_system_health():
    try:
        docs = vector_store.list_indexed_documents()
        has_gemini_key = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here")

        return jsonify({
            "status": "healthy",
            "gemini_api_configured": has_gemini_key,
            "vector_store_status": "connected",
            "indexed_documents_count": len(docs),
            "embedding_model": config.EMBEDDING_MODEL_NAME,
            "gemini_model": config.GEMINI_MODEL
        }), 200

    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 500
