from flask import Blueprint, request, jsonify, Response
from backend.database.db import db
from backend.database.models import Character, TrainingRun
from backend.models.ocr_model import HebrewOCRModel, CharacterEncoder
from backend.models.training import ModelTrainer, TrainingDataset
from backend.services.image_processing import ImageProcessor
from backend.config import Config
import cloudinary.utils
import os
import json
from datetime import datetime
import threading
import queue

training_bp = Blueprint('training', __name__)

# Global training status
training_status = {
    'is_training': False,
    'current_epoch': 0,
    'total_epochs': 0,
    'loss': 0.0,
    'accuracy': 0.0,
    'num_samples': 0,
    'progress': 0
}

# Queue for progress updates
progress_queue = queue.Queue()


def progress_callback(epoch, logs):
    """Callback for training progress"""
    global training_status

    training_status['current_epoch'] = epoch + 1
    training_status['loss'] = logs.get('loss', 0.0)
    training_status['accuracy'] = logs.get('accuracy', 0.0)
    training_status['progress'] = int((epoch + 1) / training_status['total_epochs'] * 100)

    # Add to queue for SSE
    progress_queue.put({
        'epoch': epoch + 1,
        'total_epochs': training_status['total_epochs'],
        'loss': training_status['loss'],
        'accuracy': training_status['accuracy'],
        'progress': training_status['progress']
    })


def train_model_thread(characters_data, epochs, batch_size, learning_rate):
    """Train model in separate thread"""
    global training_status

    try:
        # Create character encoder
        char_encoder = CharacterEncoder(Config.HEBREW_CHARS)

        # Create model
        model = HebrewOCRModel(
            num_classes=char_encoder.get_num_classes(),
            image_size=Config.IMAGE_SIZE
        )

        # Create trainer
        trainer = ModelTrainer(model, char_encoder)

        # Train
        result = trainer.train(
            characters_data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            augment=True,
            progress_callback=progress_callback
        )

        # Save model
        model_path = os.path.join(Config.MODEL_PATH, f"model_v{datetime.now().strftime('%Y%m%d_%H%M%S')}.keras")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        model.save_model(model_path)

        # Save training run to database
        training_run = TrainingRun(
            model_version=os.path.basename(model_path),
            num_samples=result['num_samples'],
            accuracy=result['test_metrics']['accuracy'],
            loss=result['test_metrics']['loss']
        )
        db.session.add(training_run)
        db.session.commit()

        # Update status
        training_status['is_training'] = False
        progress_queue.put({
            'status': 'completed',
            'test_accuracy': result['test_metrics']['accuracy'],
            'test_loss': result['test_metrics']['loss'],
            'model_path': model_path
        })

    except Exception as e:
        training_status['is_training'] = False
        progress_queue.put({
            'status': 'error',
            'error': str(e)
        })


@training_bp.route('/api/train', methods=['POST'])
def train():
    """
    Start model training

    Request JSON:
        {
            "epochs": int (optional, default=50),
            "batch_size": int (optional, default=32),
            "learning_rate": float (optional, default=0.001)
        }

    Returns:
        JSON with training status
    """
    global training_status

    try:
        if training_status['is_training']:
            return jsonify({'error': 'Training already in progress'}), 400

        data = request.get_json() or {}

        # Get parameters
        epochs = data.get('epochs', Config.EPOCHS)
        batch_size = data.get('batch_size', Config.BATCH_SIZE)
        learning_rate = data.get('learning_rate', Config.LEARNING_RATE)

        # Load all labeled characters from database
        characters = Character.query.filter(
            Character.label.isnot(None),
            Character.is_valid == True
        ).all()

        if len(characters) < 10:
            return jsonify({'error': 'Not enough labeled characters. Need at least 10.'}), 400

        print(f"Found {len(characters)} labeled characters")

        # Prepare character data
        characters_data = []

        for char in characters:
            # Load character image
            if Config.STORAGE_TYPE == 'cloudinary':
                import requests
                img_url = cloudinary.utils.cloudinary_url(char.image_path)[0]
                response = requests.get(img_url)
                img = ImageProcessor.load_image_from_bytes(response.content)
            else:
                img = ImageProcessor.load_image_from_path(char.image_path)

            if img is not None:
                characters_data.append({
                    'image': img,
                    'label': char.label
                })

        print(f"Loaded {len(characters_data)} character images")

        # Initialize training status
        training_status = {
            'is_training': True,
            'current_epoch': 0,
            'total_epochs': epochs,
            'loss': 0.0,
            'accuracy': 0.0,
            'num_samples': len(characters_data),
            'progress': 0
        }

        # Clear progress queue
        while not progress_queue.empty():
            progress_queue.get()

        # Start training in separate thread
        thread = threading.Thread(
            target=train_model_thread,
            args=(characters_data, epochs, batch_size, learning_rate)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Training started',
            'num_samples': len(characters_data),
            'epochs': epochs
        }), 200

    except Exception as e:
        training_status['is_training'] = False
        return jsonify({'error': str(e)}), 500


@training_bp.route('/api/train/status', methods=['GET'])
def get_training_status():
    """Get current training status"""
    return jsonify({
        'success': True,
        'status': training_status
    }), 200


@training_bp.route('/api/train/progress', methods=['GET'])
def training_progress_stream():
    """
    Server-Sent Events stream for training progress

    Returns:
        SSE stream with training updates
    """
    def generate():
        while True:
            try:
                # Wait for progress update (with timeout)
                progress = progress_queue.get(timeout=1)

                # Send progress as SSE
                yield f"data: {json.dumps(progress)}\n\n"

                # Check if training completed or errored
                if progress.get('status') in ['completed', 'error']:
                    break

            except queue.Empty:
                # Send heartbeat
                yield f"data: {json.dumps({'heartbeat': True})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break

    return Response(generate(), mimetype='text/event-stream')


@training_bp.route('/api/retrain', methods=['POST'])
def retrain():
    """
    Incremental training on new data

    Request JSON:
        {
            "document_ids": [int] (optional, if not provided uses all new data),
            "epochs": int (optional, default=10),
            "learning_rate": float (optional, default=0.0001)
        }

    Returns:
        JSON with training status
    """
    try:
        data = request.get_json() or {}

        # Get parameters
        document_ids = data.get('document_ids', [])
        epochs = data.get('epochs', 10)
        learning_rate = data.get('learning_rate', 0.0001)

        # Load new labeled characters
        query = Character.query.filter(
            Character.label.isnot(None),
            Character.is_valid == True
        )

        if document_ids:
            query = query.filter(Character.document_id.in_(document_ids))

        characters = query.all()

        if len(characters) < 5:
            return jsonify({'error': 'Not enough new labeled characters'}), 400

        # Prepare character data
        characters_data = []

        for char in characters:
            # Load character image
            if Config.STORAGE_TYPE == 'cloudinary':
                import requests
                img_url = cloudinary.utils.cloudinary_url(char.image_path)[0]
                response = requests.get(img_url)
                img = ImageProcessor.load_image_from_bytes(response.content)
            else:
                img = ImageProcessor.load_image_from_path(char.image_path)

            if img is not None:
                characters_data.append({
                    'image': img,
                    'label': char.label
                })

        # Create character encoder
        char_encoder = CharacterEncoder(Config.HEBREW_CHARS)

        # Load existing model
        model = HebrewOCRModel(
            num_classes=char_encoder.get_num_classes(),
            image_size=Config.IMAGE_SIZE
        )

        # Get latest model
        latest_run = TrainingRun.query.order_by(TrainingRun.trained_at.desc()).first()

        if latest_run:
            model_path = os.path.join(Config.MODEL_PATH, latest_run.model_version)
            if os.path.exists(model_path):
                model.load_model(model_path)
            else:
                return jsonify({'error': 'Existing model not found'}), 404
        else:
            return jsonify({'error': 'No existing model to retrain'}), 404

        # Create trainer
        trainer = ModelTrainer(model, char_encoder)

        # Incremental train
        result = trainer.incremental_train(
            characters_data,
            epochs=epochs,
            learning_rate=learning_rate
        )

        # Save updated model
        model_path = os.path.join(Config.MODEL_PATH, f"model_v{datetime.now().strftime('%Y%m%d_%H%M%S')}_retrained.keras")
        model.save_model(model_path)

        return jsonify({
            'success': True,
            'message': 'Retraining completed',
            'num_new_samples': result['num_new_samples'],
            'model_path': model_path
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@training_bp.route('/api/models', methods=['GET'])
def list_models():
    """List all trained models"""
    try:
        training_runs = TrainingRun.query.order_by(TrainingRun.trained_at.desc()).all()

        return jsonify({
            'success': True,
            'models': [run.to_dict() for run in training_runs],
            'total': len(training_runs)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@training_bp.route('/api/model/<int:model_id>', methods=['GET'])
def get_model(model_id):
    """Get model details"""
    try:
        training_run = TrainingRun.query.get(model_id)

        if not training_run:
            return jsonify({'error': 'Model not found'}), 404

        return jsonify({
            'success': True,
            'model': training_run.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
