import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import config
from core.gemini_client import GeminiClient
from core.ocr_engine import OCREngine

api_vision = Blueprint('api_vision', __name__)
gemini_client = GeminiClient()
ocr_engine = OCREngine()

@api_vision.route('/analyze', methods=['POST'])
def analyze_product_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided in request"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
    if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": f"Invalid image format. Allowed: {config.ALLOWED_IMAGE_EXTENSIONS}"}), 400

    temp_filename = f"img_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
    save_path = os.path.join(config.UPLOAD_FOLDER, temp_filename)
    file.save(save_path)

    try:
        # Run EasyOCR on image to extract any visible model labels or text tags
        ocr_text = ocr_engine.extract_text_from_image(save_path)
        ocr_error = ocr_engine.last_error

        # Run Gemini Vision analysis
        analysis_result = gemini_client.analyze_product_image(save_path, ocr_text=ocr_text)
        analysis_result["ocr_text_extracted"] = ocr_text
        analysis_result["ocr_error"] = ocr_error
        analysis_result["image_filename"] = temp_filename

        return jsonify({"status": "success", "data": analysis_result}), 200

    except Exception as e:
        print(f"Vision API Error: {str(e)}")
        return jsonify({
            "status": "error",
            "stage": "vision",
            "message": "Product image analysis failed. Check the Gemini API key and model configuration.",
            "ocr_warning": ocr_engine.last_error
        }), 500
