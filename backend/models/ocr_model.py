import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
import numpy as np
import cv2
import os
from typing import List, Tuple

class HebrewOCRModel:
    """TensorFlow/Keras model for Hebrew character recognition"""

    def __init__(self, num_classes, image_size=(32, 32)):
        """
        Initialize OCR model

        Args:
            num_classes: Number of character classes
            image_size: Input image size (width, height)
        """
        self.num_classes = num_classes
        self.image_size = image_size
        self.model = None

    def build_model(self):
        """Build CNN architecture for character recognition"""
        model = models.Sequential([
            # First convolutional block
            layers.Conv2D(32, (3, 3), activation='relu',
                         input_shape=(*self.image_size, 1),
                         padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),

            # Second convolutional block
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),

            # Third convolutional block
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),

            # Fully connected layers
            layers.Flatten(),
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.5),

            # Output layer
            layers.Dense(self.num_classes, activation='softmax')
        ])

        self.model = model
        return model

    def compile_model(self, learning_rate=0.001):
        """Compile model with optimizer and loss function"""
        if self.model is None:
            self.build_model()

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

    def train(self, X_train, y_train, X_val=None, y_val=None,
              epochs=50, batch_size=32, callbacks=None):
        """
        Train the model

        Args:
            X_train: Training images
            y_train: Training labels
            X_val: Validation images (optional)
            y_val: Validation labels (optional)
            epochs: Number of training epochs
            batch_size: Batch size
            callbacks: List of Keras callbacks

        Returns:
            Training history
        """
        if self.model is None:
            self.compile_model()

        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)

        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        return history

    def predict(self, images):
        """
        Predict character classes for images

        Args:
            images: Array of images (N, H, W) or (N, H, W, 1)

        Returns:
            Array of predicted class indices and confidence scores
        """
        if self.model is None:
            raise ValueError("Model not built or loaded")

        # Ensure correct shape
        if len(images.shape) == 3:
            images = np.expand_dims(images, axis=-1)

        predictions = self.model.predict(images)
        predicted_classes = np.argmax(predictions, axis=1)
        confidences = np.max(predictions, axis=1)

        return predicted_classes, confidences

    def predict_single(self, image):
        """
        Predict single character

        Args:
            image: Single image (H, W) or (H, W, 1)

        Returns:
            Predicted class index and confidence
        """
        # Prepare image
        img = self.preprocess_image(image)
        img = np.expand_dims(img, axis=0)

        # Predict
        classes, confidences = self.predict(img)

        return classes[0], confidences[0]

    def preprocess_image(self, img):
        """
        Preprocess image for model input

        Args:
            img: Input image

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Resize to model input size
        img = cv2.resize(img, self.image_size)

        # Normalize to [0, 1]
        img = img.astype('float32') / 255.0

        # Add channel dimension
        img = np.expand_dims(img, axis=-1)

        return img

    def save_model(self, filepath):
        """Save model to file"""
        if self.model is None:
            raise ValueError("No model to save")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.model.save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """Load model from file"""
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")

    def save_weights(self, filepath):
        """Save model weights only"""
        if self.model is None:
            raise ValueError("No model to save")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save_weights(filepath)

    def load_weights(self, filepath):
        """Load model weights"""
        if self.model is None:
            self.build_model()

        self.model.load_weights(filepath)

    def get_summary(self):
        """Get model architecture summary"""
        if self.model is None:
            self.build_model()

        return self.model.summary()

    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test data

        Returns:
            Dictionary with loss and accuracy
        """
        if self.model is None:
            raise ValueError("Model not built or loaded")

        loss, accuracy = self.model.evaluate(X_test, y_test, verbose=0)

        return {
            'loss': float(loss),
            'accuracy': float(accuracy)
        }


class CharacterEncoder:
    """Encode/decode characters to/from integer labels"""

    def __init__(self, characters):
        """
        Initialize encoder with character list

        Args:
            characters: List of characters (e.g., Hebrew alphabet)
        """
        self.characters = characters
        self.char_to_idx = {char: idx for idx, char in enumerate(characters)}
        self.idx_to_char = {idx: char for idx, char in enumerate(characters)}
        self.num_classes = len(characters)

    def encode(self, char):
        """Convert character to integer label"""
        return self.char_to_idx.get(char, -1)

    def decode(self, idx):
        """Convert integer label to character"""
        return self.idx_to_char.get(idx, '')

    def encode_batch(self, chars):
        """Encode list of characters"""
        return [self.encode(char) for char in chars]

    def decode_batch(self, indices):
        """Decode list of indices"""
        return [self.decode(idx) for idx in indices]

    def get_num_classes(self):
        """Get number of character classes"""
        return self.num_classes
