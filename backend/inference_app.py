"""
Hebrew OCR Inference API - Cloud Deployment
Lightweight Flask app that loads a trained model and performs OCR.
No database needed, no training - just inference.
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import cv2
import os
import glob

# Import model and services
from backend.models.ocr_model import HebrewOCRModel, CharacterEncoder
from backend.services.image_processing import ImageProcessor
from backend.services.character_grouping import CharacterSegmenter
from backend.services.line_segmentation import LineSegmenter

# Hebrew characters
HEBREW_CHARS = [
    'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י',
    'כ', 'ך', 'ל', 'מ', 'ם', 'נ', 'ן', 'ס', 'ע', 'פ',
    'ף', 'צ', 'ץ', 'ק', 'ר', 'ש', 'ת',
    ' ', '.', ',', '!', '?', '-', '"', "'"
]

# Initialize
char_encoder = CharacterEncoder(HEBREW_CHARS)
ocr_model = HebrewOCRModel(num_classes=len(HEBREW_CHARS))

# Load the latest trained model
MODEL_DIR = os.getenv('MODEL_PATH', os.path.join(os.path.dirname(__file__), 'models', 'saved'))


def load_latest_model():
    """Find and load the latest trained model"""
    model_files = glob.glob(os.path.join(MODEL_DIR, '*.keras'))
    if not model_files:
        print("WARNING: No trained model found. OCR will not work until a model is uploaded.")
        return False

    latest_model = max(model_files, key=os.path.getmtime)
    ocr_model.load_model(latest_model)
    print(f"Loaded model: {latest_model}")
    return True


def create_inference_app():
    app = Flask(__name__)
    CORS(app)

    model_loaded = load_latest_model()

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'message': 'Hebrew OCR API',
            'version': '1.0.0',
            'model_loaded': model_loaded,
            'endpoints': {
                'ocr': 'POST /api/ocr - Upload image, get text',
                'ocr_lines': 'POST /api/ocr/lines - Upload image, get text per line',
                'health': 'GET /health'
            }
        })

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy', 'model_loaded': model_loaded})

    @app.route('/api/ocr', methods=['POST'])
    def ocr():
        """
        Upload an image and get OCR text back.

        Request: multipart/form-data with 'file' field
        Response: { "text": "...", "characters": [...], "confidence": 0.95 }
        """
        if not model_loaded:
            return jsonify({'error': 'No model loaded. Please upload a trained model.'}), 503

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        file_bytes = file.read()

        # Load image
        img = ImageProcessor.load_image_from_bytes(file_bytes)
        if img is None:
            return jsonify({'error': 'Invalid image'}), 400

        # Resize if too large
        img = ImageProcessor.resize_image(img)

        # Segment characters
        characters = CharacterSegmenter.segment_characters(img, min_area=20, max_area=10000)

        if not characters:
            return jsonify({'text': '', 'characters': [], 'confidence': 0})

        # Sort in reading order (right-to-left for Hebrew)
        characters = CharacterSegmenter.sort_characters_reading_order(characters, rtl=True)

        # Predict each character
        results = []
        total_confidence = 0

        for char in characters:
            char_img = char['image']
            predicted_idx, confidence = ocr_model.predict_single(char_img)
            predicted_char = char_encoder.decode(int(predicted_idx))

            results.append({
                'char': predicted_char,
                'confidence': float(confidence),
                'bbox': char['bbox']
            })
            total_confidence += confidence

        # Build text
        text = ''.join([r['char'] for r in results])
        avg_confidence = total_confidence / len(results) if results else 0

        return jsonify({
            'text': text,
            'characters': results,
            'confidence': round(avg_confidence, 4),
            'total_characters': len(results)
        })

    @app.route('/api/ocr/lines', methods=['POST'])
    def ocr_lines():
        """
        Upload an image and get OCR text organized by lines.

        Request: multipart/form-data with 'file' field
        Response: { "lines": [{"text": "...", "line_order": 0}, ...] }
        """
        if not model_loaded:
            return jsonify({'error': 'No model loaded'}), 503

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        file_bytes = file.read()

        img = ImageProcessor.load_image_from_bytes(file_bytes)
        if img is None:
            return jsonify({'error': 'Invalid image'}), 400

        img = ImageProcessor.resize_image(img)

        # Segment lines
        lines = LineSegmenter.segment_lines(img, min_line_height=10)

        result_lines = []
        for line_data in lines:
            line_img = line_data['image']

            # Segment characters from this line
            chars = CharacterSegmenter.segment_characters(line_img, min_area=10, max_area=5000)
            chars = CharacterSegmenter.sort_characters_reading_order(chars, rtl=True)

            # Predict each character
            line_text = ''
            line_confidence = 0
            for char in chars:
                predicted_idx, confidence = ocr_model.predict_single(char['image'])
                line_text += char_encoder.decode(int(predicted_idx))
                line_confidence += confidence

            avg_conf = line_confidence / len(chars) if chars else 0

            result_lines.append({
                'line_order': line_data['line_order'],
                'text': line_text,
                'confidence': round(avg_conf, 4),
                'num_characters': len(chars)
            })

        # Combine all lines
        full_text = '\n'.join([l['text'] for l in result_lines])

        return jsonify({
            'text': full_text,
            'lines': result_lines,
            'total_lines': len(result_lines)
        })

    @app.route('/api/model/upload', methods=['POST'])
    def upload_model():
        """Upload a trained model (.keras file)"""
        if 'model' not in request.files:
            return jsonify({'error': 'No model file provided'}), 400

        model_file = request.files['model']
        if not model_file.filename.endswith('.keras'):
            return jsonify({'error': 'Model must be a .keras file'}), 400

        os.makedirs(MODEL_DIR, exist_ok=True)
        filepath = os.path.join(MODEL_DIR, model_file.filename)
        model_file.save(filepath)

        # Reload model
        nonlocal model_loaded
        try:
            ocr_model.load_model(filepath)
            model_loaded = True
            return jsonify({'success': True, 'message': f'Model loaded: {model_file.filename}'})
        except Exception as e:
            return jsonify({'error': f'Failed to load model: {str(e)}'}), 500

    return app


# Create app instance for Gunicorn
app = create_inference_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
