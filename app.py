import os
from flask import Flask, render_template, jsonify
import config

from routes.api_vision import api_vision
from routes.api_documents import api_documents
from routes.api_rag import api_rag
from routes.api_system import api_system
from routes.api_troubleshooting import api_troubleshooting

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Register API blueprints
    app.register_blueprint(api_vision, url_prefix='/api/v1/vision')
    app.register_blueprint(api_documents, url_prefix='/api/v1/documents')
    app.register_blueprint(api_rag, url_prefix='/api/v1/rag')
    app.register_blueprint(api_system, url_prefix='/api/v1/system')
    app.register_blueprint(api_troubleshooting, url_prefix='/api/v1/troubleshooting')

    # Main Single Page App (SPA) view route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Multimodal Product Knowledge RAG server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
