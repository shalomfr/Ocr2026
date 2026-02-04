from flask import Blueprint, request, jsonify
from database.db import db
from database.models import Document
from services.image_processing import ImageProcessor
import cloudinary.uploader
from config import Config
from datetime import datetime
import os

preprocessing_bp = Blueprint('preprocessing', __name__)


@preprocessing_bp.route('/api/enhance', methods=['POST'])
def enhance_image():
    """
    Enhance image with various parameters

    Request JSON:
        {
            "document_id": int,
            "brightness": int (-100 to 100),
            "contrast": float (0.5 to 3.0),
            "blur": int (0 = no blur, odd numbers),
            "threshold": int (0-255, null = no threshold),
            "sharpen": int (0-10)
        }

    Returns:
        JSON with enhanced image as base64
    """
    try:
        data = request.get_json()

        if not data or 'document_id' not in data:
            return jsonify({'error': 'document_id required'}), 400

        document_id = data['document_id']
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Load original image
        if Config.STORAGE_TYPE == 'cloudinary':
            # Download from Cloudinary
            import requests
            img_url = cloudinary.utils.cloudinary_url(document.original_image_path)[0]
            response = requests.get(img_url)
            img = ImageProcessor.load_image_from_bytes(response.content)
        else:
            img = ImageProcessor.load_image_from_path(document.original_image_path)

        if img is None:
            return jsonify({'error': 'Failed to load image'}), 500

        # Get enhancement parameters
        brightness = data.get('brightness', 0)
        contrast = data.get('contrast', 1.0)
        blur = data.get('blur', 0)
        threshold = data.get('threshold', None)
        sharpen = data.get('sharpen', 0)

        # Apply enhancements
        enhanced_img = ImageProcessor.enhance_image(
            img,
            brightness=brightness,
            contrast=contrast,
            blur=blur,
            threshold=threshold,
            sharpen=sharpen
        )

        # Convert to base64 for preview
        img_base64 = ImageProcessor.image_to_base64(enhanced_img)

        return jsonify({
            'success': True,
            'image': img_base64,
            'document_id': document_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@preprocessing_bp.route('/api/enhance/save', methods=['POST'])
def save_enhanced_image():
    """
    Save enhanced image permanently

    Request JSON:
        {
            "document_id": int,
            "brightness": int,
            "contrast": float,
            "blur": int,
            "threshold": int,
            "sharpen": int
        }

    Returns:
        JSON with saved image URL
    """
    try:
        data = request.get_json()

        if not data or 'document_id' not in data:
            return jsonify({'error': 'document_id required'}), 400

        document_id = data['document_id']
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Load original image
        if Config.STORAGE_TYPE == 'cloudinary':
            import requests
            img_url = cloudinary.utils.cloudinary_url(document.original_image_path)[0]
            response = requests.get(img_url)
            img = ImageProcessor.load_image_from_bytes(response.content)
        else:
            img = ImageProcessor.load_image_from_path(document.original_image_path)

        if img is None:
            return jsonify({'error': 'Failed to load image'}), 500

        # Apply enhancements
        brightness = data.get('brightness', 0)
        contrast = data.get('contrast', 1.0)
        blur = data.get('blur', 0)
        threshold = data.get('threshold', None)
        sharpen = data.get('sharpen', 0)

        enhanced_img = ImageProcessor.enhance_image(
            img,
            brightness=brightness,
            contrast=contrast,
            blur=blur,
            threshold=threshold,
            sharpen=sharpen
        )

        # Save enhanced image
        if Config.STORAGE_TYPE == 'cloudinary':
            import cv2
            import io
            # Encode to bytes
            success, buffer = cv2.imencode('.png', enhanced_img)
            if not success:
                return jsonify({'error': 'Failed to encode image'}), 500

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                io.BytesIO(buffer),
                folder='hebrew_ocr/enhanced',
                public_id=f"enhanced_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            image_url = result['secure_url']
            image_path = result['public_id']
        else:
            upload_folder = Config.UPLOAD_FOLDER
            os.makedirs(upload_folder, exist_ok=True)

            image_path = os.path.join(
                upload_folder,
                f"enhanced_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            ImageProcessor.save_image(enhanced_img, image_path)
            image_url = f"/uploads/{os.path.basename(image_path)}"

        # Update document
        document.enhanced_image_path = image_path
        document.status = 'enhanced'
        db.session.commit()

        return jsonify({
            'success': True,
            'image_url': image_url,
            'document_id': document_id,
            'enhanced_path': image_path
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@preprocessing_bp.route('/api/preprocess/auto', methods=['POST'])
def auto_preprocess():
    """
    Automatically preprocess image with default settings

    Request JSON:
        {
            "document_id": int
        }

    Returns:
        JSON with preprocessed image
    """
    try:
        data = request.get_json()

        if not data or 'document_id' not in data:
            return jsonify({'error': 'document_id required'}), 400

        document_id = data['document_id']
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Load image
        if Config.STORAGE_TYPE == 'cloudinary':
            import requests
            img_url = cloudinary.utils.cloudinary_url(document.original_image_path)[0]
            response = requests.get(img_url)
            img = ImageProcessor.load_image_from_bytes(response.content)
        else:
            img = ImageProcessor.load_image_from_path(document.original_image_path)

        if img is None:
            return jsonify({'error': 'Failed to load image'}), 500

        # Apply automatic preprocessing pipeline
        # 1. Denoise
        img = ImageProcessor.denoise(img, strength=10)

        # 2. Auto-rotate if needed
        img = ImageProcessor.auto_rotate(img)

        # 3. Invert if needed
        img = ImageProcessor.invert_if_needed(img)

        # 4. Remove borders
        img = ImageProcessor.remove_borders(img)

        # 5. Adaptive threshold
        img = ImageProcessor.adaptive_threshold(img)

        # Convert to base64
        img_base64 = ImageProcessor.image_to_base64(img)

        return jsonify({
            'success': True,
            'image': img_base64,
            'document_id': document_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
