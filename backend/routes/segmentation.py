from flask import Blueprint, request, jsonify
from backend.database.db import db
from backend.database.models import Document, Character, Line
from backend.services.image_processing import ImageProcessor
from backend.services.character_grouping import CharacterSegmenter
from backend.services.line_segmentation import LineSegmenter
import cloudinary.uploader
from backend.config import Config
import os
import cv2
import io
from datetime import datetime

segmentation_bp = Blueprint('segmentation', __name__)


@segmentation_bp.route('/api/segment/characters', methods=['POST'])
def segment_characters():
    """
    Segment characters from document and group by similarity

    Request JSON:
        {
            "document_id": int,
            "min_area": int (optional, default=20),
            "max_area": int (optional, default=10000),
            "clustering_method": str (optional, "kmeans" or "dbscan")
        }

    Returns:
        JSON with character groups
    """
    try:
        data = request.get_json()

        if not data or 'document_id' not in data:
            return jsonify({'error': 'document_id required'}), 400

        document_id = data['document_id']
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Load enhanced image (or original if not enhanced)
        image_path = document.enhanced_image_path or document.original_image_path

        if Config.STORAGE_TYPE == 'cloudinary':
            import requests
            img_url = cloudinary.utils.cloudinary_url(image_path)[0]
            response = requests.get(img_url)
            img = ImageProcessor.load_image_from_bytes(response.content)
        else:
            img = ImageProcessor.load_image_from_path(image_path)

        if img is None:
            return jsonify({'error': 'Failed to load image'}), 500

        # Segment characters
        min_area = data.get('min_area', 20)
        max_area = data.get('max_area', 10000)
        characters = CharacterSegmenter.segment_characters(img, min_area, max_area)

        print(f"Found {len(characters)} characters")

        # Cluster characters
        clustering_method = data.get('clustering_method', 'kmeans')
        groups = CharacterSegmenter.group_characters_by_similarity(
            characters,
            method=clustering_method
        )

        print(f"Grouped into {len(groups)} clusters")

        # Save characters to database and prepare response
        result_groups = {}

        for group_id, group_chars in groups.items():
            result_groups[str(group_id)] = []

            for char in group_chars:
                # Save character image
                char_img = char['image']

                if Config.STORAGE_TYPE == 'cloudinary':
                    # Upload to Cloudinary
                    success, buffer = cv2.imencode('.png', char_img)
                    if success:
                        result = cloudinary.uploader.upload(
                            io.BytesIO(buffer),
                            folder=f'hebrew_ocr/characters/{document_id}',
                            public_id=f"char_{char['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        )
                        char_image_path = result['public_id']
                        char_image_url = result['secure_url']
                    else:
                        continue
                else:
                    char_folder = os.path.join(Config.UPLOAD_FOLDER, f'characters/{document_id}')
                    os.makedirs(char_folder, exist_ok=True)

                    char_image_path = os.path.join(
                        char_folder,
                        f"char_{char['id']}.png"
                    )
                    ImageProcessor.save_image(char_img, char_image_path)
                    char_image_url = f"/uploads/characters/{document_id}/char_{char['id']}.png"

                # Save to database
                character = Character(
                    document_id=document_id,
                    image_path=char_image_path,
                    bbox_x=char['bbox']['x'],
                    bbox_y=char['bbox']['y'],
                    bbox_w=char['bbox']['w'],
                    bbox_h=char['bbox']['h'],
                    group_id=group_id,
                    is_valid=True
                )
                db.session.add(character)
                db.session.flush()

                # Add to result
                result_groups[str(group_id)].append({
                    'id': character.id,
                    'image_url': char_image_url,
                    'bbox': char['bbox']
                })

        db.session.commit()

        # Update document status
        document.status = 'segmented'
        db.session.commit()

        return jsonify({
            'success': True,
            'document_id': document_id,
            'groups': result_groups,
            'total_characters': len(characters),
            'total_groups': len(groups)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@segmentation_bp.route('/api/segment/lines', methods=['POST'])
def segment_lines():
    """
    Segment text lines from document

    Request JSON:
        {
            "document_id": int,
            "min_line_height": int (optional, default=10),
            "method": str (optional, "projection" or "advanced")
        }

    Returns:
        JSON with line images
    """
    try:
        data = request.get_json()

        if not data or 'document_id' not in data:
            return jsonify({'error': 'document_id required'}), 400

        document_id = data['document_id']
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Load enhanced image
        image_path = document.enhanced_image_path or document.original_image_path

        if Config.STORAGE_TYPE == 'cloudinary':
            import requests
            img_url = cloudinary.utils.cloudinary_url(image_path)[0]
            response = requests.get(img_url)
            img = ImageProcessor.load_image_from_bytes(response.content)
        else:
            img = ImageProcessor.load_image_from_path(image_path)

        if img is None:
            return jsonify({'error': 'Failed to load image'}), 500

        # Segment lines
        min_line_height = data.get('min_line_height', 10)
        method = data.get('method', 'projection')

        if method == 'advanced':
            lines = LineSegmenter.segment_lines_advanced(img, min_line_height)
        else:
            lines = LineSegmenter.segment_lines(img, min_line_height)

        print(f"Found {len(lines)} lines")

        # Save lines to database
        result_lines = []

        for line_data in lines:
            line_img = line_data['image']

            # Save line image
            if Config.STORAGE_TYPE == 'cloudinary':
                success, buffer = cv2.imencode('.png', line_img)
                if success:
                    result = cloudinary.uploader.upload(
                        io.BytesIO(buffer),
                        folder=f'hebrew_ocr/lines/{document_id}',
                        public_id=f"line_{line_data['line_order']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    )
                    line_image_path = result['public_id']
                    line_image_url = result['secure_url']
                else:
                    continue
            else:
                line_folder = os.path.join(Config.UPLOAD_FOLDER, f'lines/{document_id}')
                os.makedirs(line_folder, exist_ok=True)

                line_image_path = os.path.join(
                    line_folder,
                    f"line_{line_data['line_order']}.png"
                )
                ImageProcessor.save_image(line_img, line_image_path)
                line_image_url = f"/uploads/lines/{document_id}/line_{line_data['line_order']}.png"

            # Save to database
            line = Line(
                document_id=document_id,
                image_path=line_image_path,
                line_order=line_data['line_order'],
                bbox_y_start=line_data['y_start'],
                bbox_y_end=line_data['y_end']
            )
            db.session.add(line)
            db.session.flush()

            result_lines.append({
                'id': line.id,
                'line_order': line_data['line_order'],
                'image_url': line_image_url,
                'y_start': line_data['y_start'],
                'y_end': line_data['y_end']
            })

        db.session.commit()

        return jsonify({
            'success': True,
            'document_id': document_id,
            'lines': result_lines,
            'total_lines': len(lines)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@segmentation_bp.route('/api/characters/<int:document_id>', methods=['GET'])
def get_characters(document_id):
    """Get all characters for a document"""
    try:
        characters = Character.query.filter_by(document_id=document_id).all()

        # Group by group_id
        groups = {}
        for char in characters:
            group_id = char.group_id
            if group_id not in groups:
                groups[group_id] = []

            # Get image URL
            if Config.STORAGE_TYPE == 'cloudinary':
                image_url = cloudinary.utils.cloudinary_url(char.image_path)[0]
            else:
                # Remove UPLOAD_FOLDER prefix to get relative path
                relative_path = char.image_path.replace(Config.UPLOAD_FOLDER, '').lstrip('/')
                image_url = f"/uploads/{relative_path}"

            groups[group_id].append({
                'id': char.id,
                'image_url': image_url,
                'bbox': {
                    'x': char.bbox_x,
                    'y': char.bbox_y,
                    'w': char.bbox_w,
                    'h': char.bbox_h
                },
                'label': char.label
            })

        return jsonify({
            'success': True,
            'groups': groups
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@segmentation_bp.route('/api/lines/<int:document_id>', methods=['GET'])
def get_lines(document_id):
    """Get all lines for a document"""
    try:
        lines = Line.query.filter_by(document_id=document_id).order_by(Line.line_order).all()

        result_lines = []
        for line in lines:
            # Get image URL
            if Config.STORAGE_TYPE == 'cloudinary':
                image_url = cloudinary.utils.cloudinary_url(line.image_path)[0]
            else:
                # Remove UPLOAD_FOLDER prefix to get relative path
                relative_path = line.image_path.replace(Config.UPLOAD_FOLDER, '').lstrip('/')
                image_url = f"/uploads/{relative_path}"

            result_lines.append({
                'id': line.id,
                'line_order': line.line_order,
                'image_url': image_url,
                'text': line.text,
                'y_start': line.bbox_y_start,
                'y_end': line.bbox_y_end
            })

        return jsonify({
            'success': True,
            'lines': result_lines
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
