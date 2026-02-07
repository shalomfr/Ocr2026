import os
from dotenv import load_dotenv

load_dotenv()

# Base directory for resolving relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    """Application configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'

    # Database settings - SQLite by default for local, PostgreSQL for production
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "hebrew_ocr.db")}')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp'}

    # Storage settings - local by default
    STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))

    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

    # Model settings
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/saved')
    IMAGE_SIZE = (32, 32)  # Character image size for model input
    BATCH_SIZE = 32
    EPOCHS = 50
    LEARNING_RATE = 0.001

    # Hebrew alphabet + space + common punctuation
    HEBREW_CHARS = [
        'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י',
        'כ', 'ך', 'ל', 'מ', 'ם', 'נ', 'ן', 'ס', 'ע', 'פ',
        'ף', 'צ', 'ץ', 'ק', 'ר', 'ש', 'ת',
        ' ', '.', ',', '!', '?', '-', '"', "'"
    ]
    NUM_CLASSES = len(HEBREW_CHARS)

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass
