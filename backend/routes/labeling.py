from flask import Blueprint, request, jsonify
from database.db import db
from database.models import Character, Line, Document

labeling_bp = Blueprint('labeling', __name__)


@labeling_bp.route('/api/label/characters', methods=['POST'])
def label_characters():
    """
    Save character labels

    Request JSON:
        {
            "labels": [
                {
                    "character_id": int,
                    "label": str,
                    "group_id": int (optional)
                },
                ...
            ]
        }

    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()

        if not data or 'labels' not in data:
            return jsonify({'error': 'labels required'}), 400

        labels = data['labels']
        updated_count = 0

        for label_data in labels:
            character_id = label_data.get('character_id')
            label = label_data.get('label')

            if not character_id or not label:
                continue

            # Update character
            character = Character.query.get(character_id)
            if character:
                character.label = label

                # Update group_id if provided
                if 'group_id' in label_data:
                    character.group_id = label_data['group_id']

                updated_count += 1

        db.session.commit()

        # Update document status
        if labels:
            first_char = Character.query.get(labels[0]['character_id'])
            if first_char:
                document = Document.query.get(first_char.document_id)
                if document and document.status == 'segmented':
                    document.status = 'labeled'
                    db.session.commit()

        return jsonify({
            'success': True,
            'updated_count': updated_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/label/group', methods=['POST'])
def label_group():
    """
    Apply label to all characters in a group

    Request JSON:
        {
            "document_id": int,
            "group_id": int,
            "label": str
        }

    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()

        document_id = data.get('document_id')
        group_id = data.get('group_id')
        label = data.get('label')

        if document_id is None or group_id is None or not label:
            return jsonify({'error': 'document_id, group_id, and label required'}), 400

        # Update all characters in group
        characters = Character.query.filter_by(
            document_id=document_id,
            group_id=group_id
        ).all()

        for character in characters:
            character.label = label

        db.session.commit()

        return jsonify({
            'success': True,
            'updated_count': len(characters)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/transcribe/lines', methods=['POST'])
def transcribe_lines():
    """
    Save line transcriptions

    Request JSON:
        {
            "transcriptions": [
                {
                    "line_id": int,
                    "text": str
                },
                ...
            ]
        }

    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()

        if not data or 'transcriptions' not in data:
            return jsonify({'error': 'transcriptions required'}), 400

        transcriptions = data['transcriptions']
        updated_count = 0

        for trans_data in transcriptions:
            line_id = trans_data.get('line_id')
            text = trans_data.get('text')

            if not line_id or text is None:
                continue

            # Update line
            line = Line.query.get(line_id)
            if line:
                line.text = text
                updated_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'updated_count': updated_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/character/<int:character_id>', methods=['PATCH'])
def update_character(character_id):
    """
    Update individual character

    Request JSON:
        {
            "label": str (optional),
            "group_id": int (optional),
            "is_valid": bool (optional)
        }

    Returns:
        JSON with updated character
    """
    try:
        character = Character.query.get(character_id)

        if not character:
            return jsonify({'error': 'Character not found'}), 404

        data = request.get_json()

        if 'label' in data:
            character.label = data['label']

        if 'group_id' in data:
            character.group_id = data['group_id']

        if 'is_valid' in data:
            character.is_valid = data['is_valid']

        db.session.commit()

        return jsonify({
            'success': True,
            'character': character.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/character/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    """Mark character as invalid"""
    try:
        character = Character.query.get(character_id)

        if not character:
            return jsonify({'error': 'Character not found'}), 404

        character.is_valid = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Character marked as invalid'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/character/move', methods=['POST'])
def move_character():
    """
    Move character to different group

    Request JSON:
        {
            "character_id": int,
            "new_group_id": int
        }

    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()

        character_id = data.get('character_id')
        new_group_id = data.get('new_group_id')

        if not character_id or new_group_id is None:
            return jsonify({'error': 'character_id and new_group_id required'}), 400

        character = Character.query.get(character_id)

        if not character:
            return jsonify({'error': 'Character not found'}), 404

        old_group_id = character.group_id
        character.group_id = new_group_id
        db.session.commit()

        return jsonify({
            'success': True,
            'character_id': character_id,
            'old_group_id': old_group_id,
            'new_group_id': new_group_id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/line/<int:line_id>', methods=['PATCH'])
def update_line(line_id):
    """
    Update individual line transcription

    Request JSON:
        {
            "text": str
        }

    Returns:
        JSON with updated line
    """
    try:
        line = Line.query.get(line_id)

        if not line:
            return jsonify({'error': 'Line not found'}), 404

        data = request.get_json()

        if 'text' in data:
            line.text = data['text']

        db.session.commit()

        return jsonify({
            'success': True,
            'line': line.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labeling_bp.route('/api/labels/export/<int:document_id>', methods=['GET'])
def export_labels(document_id):
    """
    Export all labels for a document

    Returns:
        JSON with all character labels and line transcriptions
    """
    try:
        document = Document.query.get(document_id)

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Get all labeled characters
        characters = Character.query.filter_by(
            document_id=document_id,
            is_valid=True
        ).filter(Character.label.isnot(None)).all()

        char_labels = [
            {
                'id': char.id,
                'label': char.label,
                'group_id': char.group_id,
                'bbox': {
                    'x': char.bbox_x,
                    'y': char.bbox_y,
                    'w': char.bbox_w,
                    'h': char.bbox_h
                }
            }
            for char in characters
        ]

        # Get all line transcriptions
        lines = Line.query.filter_by(document_id=document_id).order_by(Line.line_order).all()

        line_transcriptions = [
            {
                'id': line.id,
                'line_order': line.line_order,
                'text': line.text,
                'y_start': line.bbox_y_start,
                'y_end': line.bbox_y_end
            }
            for line in lines
        ]

        return jsonify({
            'success': True,
            'document_id': document_id,
            'filename': document.filename,
            'characters': char_labels,
            'lines': line_transcriptions,
            'total_characters': len(char_labels),
            'total_lines': len(line_transcriptions)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
