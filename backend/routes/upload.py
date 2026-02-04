from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from database.db import db
from database.models import Document
from services.image_processing import ImageProcessor
import cloudinary
import cloudinary.uploader
from config import Config
from datetime import datetime

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@upload_bp.route('/api/upload', methods=['POST'])
def upload_image():
    """
    Upload a single image

    Returns:
        JSON with document_id and image URL
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        # Read file
        file_bytes = file.read()
        filename = secure_filename(file.filename)

        # Load and validate image
        img = ImageProcessor.load_image_from_bytes(file_bytes)
        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400

        # Resize if too large
        img = ImageProcessor.resize_image(img)

        # Save image
        if Config.STORAGE_TYPE == 'cloudinary':
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_bytes,
                folder='hebrew_ocr/originals',
                public_id=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            )
            image_url = result['secure_url']
            image_path = result['public_id']

        else:
            # Save locally
            upload_folder = Config.UPLOAD_FOLDER
            os.makedirs(upload_folder, exist_ok=True)

            image_path = os.path.join(upload_folder, f"original_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
            ImageProcessor.save_image(img, image_path)
            image_url = f"/uploads/{os.path.basename(image_path)}"

        # Save to database
        document = Document(
            filename=filename,
            original_image_path=image_path,
            status='uploaded'
        )
        db.session.add(document)
        db.session.commit()

        return jsonify({
            'success': True,
            'document_id': document.id,
            'image_url': image_url,
            'filename': filename
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/batch/upload', methods=['POST'])
def batch_upload():
    """
    Upload multiple images

    Returns:
        JSON with list of uploaded documents
    """
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')

        if not files:
            return jsonify({'error': 'No files selected'}), 400

        uploaded_documents = []
        errors = []

        for file in files:
            try:
                if file.filename == '':
                    continue

                if not allowed_file(file.filename):
                    errors.append(f"{file.filename}: File type not allowed")
                    continue

                # Read file
                file_bytes = file.read()
                filename = secure_filename(file.filename)

                # Load and validate image
                img = ImageProcessor.load_image_from_bytes(file_bytes)
                if img is None:
                    errors.append(f"{filename}: Invalid image file")
                    continue

                # Resize if too large
                img = ImageProcessor.resize_image(img)

                # Save image
                if Config.STORAGE_TYPE == 'cloudinary':
                    result = cloudinary.uploader.upload(
                        file_bytes,
                        folder='hebrew_ocr/originals',
                        public_id=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    )
                    image_url = result['secure_url']
                    image_path = result['public_id']
                else:
                    upload_folder = Config.UPLOAD_FOLDER
                    os.makedirs(upload_folder, exist_ok=True)

                    image_path = os.path.join(upload_folder, f"original_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
                    ImageProcessor.save_image(img, image_path)
                    image_url = f"/uploads/{os.path.basename(image_path)}"

                # Save to database
                document = Document(
                    filename=filename,
                    original_image_path=image_path,
                    status='uploaded'
                )
                db.session.add(document)
                db.session.commit()

                uploaded_documents.append({
                    'document_id': document.id,
                    'image_url': image_url,
                    'filename': filename
                })

            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
                continue

        return jsonify({
            'success': True,
            'uploaded': uploaded_documents,
            'errors': errors,
            'total_uploaded': len(uploaded_documents),
            'total_errors': len(errors)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get document details"""
    try:
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        return jsonify({
            'success': True,
            'document': document.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/documents', methods=['GET'])
def list_documents():
    """List all documents"""
    try:
        documents = Document.query.order_by(Document.upload_date.desc()).all()

        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents],
            'total': len(documents)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete document"""
    try:
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Delete from database (cascade will delete related records)
        db.session.delete(document)
        db.session.commit()

        # TODO: Delete from storage (Cloudinary or local)

        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
