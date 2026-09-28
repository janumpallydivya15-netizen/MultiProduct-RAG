import os
import uuid
import glob
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import config
from core.rag_pipeline import RAGPipeline
from core.vector_store import VectorStore

api_documents = Blueprint('api_documents', __name__)
rag_pipeline = RAGPipeline()
vector_store = rag_pipeline.vector_store

@api_documents.route('/upload', methods=['POST'])
def upload_document():
    if 'document' not in request.files:
        return jsonify({"error": "No document file provided in upload request"}), 400

    file = request.files['document']
    product_id = request.form.get('product_id', 'general').strip()

    if file.filename == '':
        return jsonify({"error": "No file selected for upload"}), 400

    ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
    if ext not in config.ALLOWED_DOC_EXTENSIONS:
        return jsonify({"error": f"Invalid document format .{ext}. Allowed extensions: {config.ALLOWED_DOC_EXTENSIONS}"}), 400

    # Validate non-empty file
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size == 0:
        return jsonify({"error": "Uploaded file is empty (0 bytes)"}), 400

    clean_filename = secure_filename(file.filename)

    # Check for duplicate document before generating new doc_id & saving
    existing = vector_store.check_existing_document(clean_filename, product_id)
    if existing:
        return jsonify({
            "status": "duplicate",
            "message": f"Document '{clean_filename}' for product '{product_id}' is already indexed in ChromaDB.",
            "data": {
                "doc_id": existing["document_id"],
                "filename": clean_filename,
                "product_id": product_id,
                "chunks": existing["chunks"],
                "indexed": True
            }
        }), 200

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    save_path = os.path.join(config.UPLOAD_FOLDER, f"{doc_id}_{clean_filename}")
    file.save(save_path)

    try:
        res = rag_pipeline.ingest_document(save_path, doc_id=doc_id, product_id=product_id, original_filename=clean_filename)

        if res.get("status") == "duplicate":
            # Remove temporary uploaded duplicate file
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify({
                "status": "duplicate",
                "message": res.get("message"),
                "data": {
                    "doc_id": res.get("doc_id"),
                    "filename": clean_filename,
                    "product_id": product_id,
                    "chunks": res.get("chunks", 0),
                    "indexed": True
                }
            }), 200

        if res.get("status") == "error":
            return jsonify({"error": res.get("message")}), 400

        return jsonify({
            "status": "success",
            "data": {
                "doc_id": doc_id,
                "filename": clean_filename,
                "product_id": product_id,
                "pages": res.get("pages", 0),
                "chunks": res.get("chunks", 0),
                "indexed": True
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Document ingestion failed: {str(e)}"}), 500


@api_documents.route('', methods=['GET'])
def list_documents():
    try:
        documents = vector_store.list_indexed_documents()
        return jsonify({"status": "success", "documents": documents}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to list documents: {str(e)}"}), 500


@api_documents.route('/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):

    try:
        # Step 1: Look up document metadata BEFORE deletion (to find local file)
        docs = vector_store.list_indexed_documents()
        doc_meta = next((d for d in docs if d["doc_id"] == doc_id), None)

        if doc_meta:
            pass



        # Step 2: Check how many matching chunks exist in ChromaDB
        try:
            chunk_check = vector_store.collection.get(where={"document_id": doc_id}, include=[])
            matching_chunk_ids = chunk_check.get("ids", [])

        except Exception as e:
            matching_chunk_ids = []


        # If no chunks AND no metadata, the doc truly doesn't exist
        if not matching_chunk_ids and not doc_meta:

            return jsonify({
                "success": False,
                "message": f"Document '{doc_id}' not found in the knowledge base"
            }), 404

        # Step 3: Delete from ChromaDB (only if chunks are present)
        if matching_chunk_ids:

            try:
                vector_store.collection.delete(where={"document_id": doc_id})

            except Exception as e:

                return jsonify({
                    "success": False,
                    "message": f"ChromaDB deletion failed: {str(e)}"
                }), 500
        else:
            pass


        # Step 4: Delete local uploaded file using glob (handles doc_id_ prefix)
        upload_dir = config.UPLOAD_FOLDER
        pattern = os.path.join(upload_dir, f"{doc_id}_*")
        matched_files = glob.glob(pattern)

        for fpath in matched_files:
            try:
                os.remove(fpath)

            except Exception as e:
                pass



        return jsonify({
            "success": True,
            "message": "Document deleted successfully",
            "doc_id": doc_id
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Delete document failed: {str(e)}"
        }), 500
