from flask import Blueprint, request, jsonify
from core.rag_pipeline import RAGPipeline

api_troubleshooting = Blueprint('api_troubleshooting', __name__)
rag_pipeline = RAGPipeline()

@api_troubleshooting.route('/diagnose', methods=['POST'])
def diagnose_issue():
    data = request.get_json() or {}
    product_id = data.get('product_id', 'all').strip()
    error_code = data.get('error_code', '').strip()
    symptom = data.get('symptom', '').strip()
    description = data.get('description', '').strip()

    if not error_code and not symptom and not description:
        return jsonify({"success": False, "error": "Please provide an error code, symptom, or description."}), 400

    try:
        result = rag_pipeline.diagnose(
            product_id=product_id,
            error_code=error_code,
            symptom=symptom,
            description=description
        )

        return jsonify({
            "success": True,
            "product_id": product_id,
            "problem": error_code or symptom or description,
            "diagnosis": result.get("diagnosis", ""),
            "severity": result.get("severity", "Unknown"),
            "resolution_steps": result.get("resolution_steps", []),
            "prevention_or_notes": result.get("prevention_or_notes", []),
            "sources": result.get("sources", []),
            "chunks_retrieved": result.get("chunks_retrieved", 0)
        }), 200

    except RuntimeError as e:
        print(f"[TROUBLESHOOTING ERROR] {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 503

    except Exception as e:
        print(f"[TROUBLESHOOTING ERROR] Unhandled: {type(e).__name__}: {e}")
        return jsonify({
            "success": False,
            "error": f"Diagnosis failed: {str(e)}"
        }), 500
