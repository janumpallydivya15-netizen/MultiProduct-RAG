from flask import Blueprint, request, jsonify
from core.rag_pipeline import RAGPipeline

api_rag = Blueprint('api_rag', __name__)
rag_pipeline = RAGPipeline()

@api_rag.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    product_id = data.get('product_id', 'all').strip()

    if not question:
        return jsonify({"success": False, "error": "Question field is required"}), 400

    try:
        result = rag_pipeline.query(question=question, product_id=product_id)

        return jsonify({
            "success": True,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "retrieved_chunks": result.get("retrieved_chunks", 0)
        }), 200

    except RuntimeError as e:
        # Gemini-specific errors (model unavailable, quota, etc.)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 503

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"RAG query failed: {str(e)}"
        }), 500
