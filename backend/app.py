from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database.db import db, init_db
import cloudinary
import os

# Import blueprints
from routes.upload import upload_bp
from routes.preprocessing import preprocessing_bp
from routes.segmentation import segmentation_bp
from routes.labeling import labeling_bp
from routes.training import training_bp


def create_app(config_class=Config):
    """Create and configure Flask application"""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database
    init_db(app)

    # Configure Cloudinary if using cloud storage
    if app.config['STORAGE_TYPE'] == 'cloudinary':
        cloudinary.config(
            cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=app.config['CLOUDINARY_API_KEY'],
            api_secret=app.config['CLOUDINARY_API_SECRET']
        )

    # Create upload folder if using local storage
    if app.config['STORAGE_TYPE'] == 'local':
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create model folder
    os.makedirs(app.config['MODEL_PATH'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(upload_bp)
    app.register_blueprint(preprocessing_bp)
    app.register_blueprint(segmentation_bp)
    app.register_blueprint(labeling_bp)
    app.register_blueprint(training_bp)

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Hebrew OCR Backend'
        }), 200

    # Root endpoint
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'message': 'Hebrew OCR Training System API',
            'version': '1.0.0',
            'endpoints': {
                'upload': '/api/upload',
                'enhance': '/api/enhance',
                'segment_characters': '/api/segment/characters',
                'segment_lines': '/api/segment/lines',
                'label_characters': '/api/label/characters',
                'transcribe_lines': '/api/transcribe/lines',
                'train': '/api/train',
                'train_status': '/api/train/status'
            }
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False') == 'True'

    print(f"Starting Hebrew OCR Backend on port {port}")
    print(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)
