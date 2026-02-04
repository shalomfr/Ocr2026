import numpy as np
import cv2
from sklearn.model_selection import train_test_split
from tensorflow import keras
import os
from typing import List, Dict, Tuple, Callable
import json

class DataAugmenter:
    """Data augmentation for character images"""

    @staticmethod
    def rotate(img, angle_range=(-15, 15)):
        """Rotate image by random angle"""
        angle = np.random.uniform(angle_range[0], angle_range[1])
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        return rotated

    @staticmethod
    def scale(img, scale_range=(0.8, 1.2)):
        """Scale image by random factor"""
        scale_factor = np.random.uniform(scale_range[0], scale_range[1])
        h, w = img.shape[:2]
        new_h, new_w = int(h * scale_factor), int(w * scale_factor)

        if new_h > 0 and new_w > 0:
            scaled = cv2.resize(img, (new_w, new_h))

            # Pad or crop to original size
            if new_h < h or new_w < w:
                # Pad
                pad_h = max(0, h - new_h)
                pad_w = max(0, w - new_w)
                scaled = cv2.copyMakeBorder(scaled, pad_h // 2, pad_h - pad_h // 2,
                                          pad_w // 2, pad_w - pad_w // 2,
                                          cv2.BORDER_REPLICATE)
            else:
                # Crop
                start_h = (new_h - h) // 2
                start_w = (new_w - w) // 2
                scaled = scaled[start_h:start_h + h, start_w:start_w + w]

            return scaled
        return img

    @staticmethod
    def add_noise(img, noise_level=10):
        """Add Gaussian noise to image"""
        noise = np.random.normal(0, noise_level, img.shape)
        noisy = img + noise
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        return noisy

    @staticmethod
    def adjust_brightness(img, brightness_range=(-30, 30)):
        """Adjust image brightness"""
        brightness = np.random.uniform(brightness_range[0], brightness_range[1])
        adjusted = cv2.convertScaleAbs(img, alpha=1.0, beta=brightness)
        return adjusted

    @staticmethod
    def adjust_contrast(img, contrast_range=(0.8, 1.2)):
        """Adjust image contrast"""
        contrast = np.random.uniform(contrast_range[0], contrast_range[1])
        adjusted = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
        return adjusted

    @staticmethod
    def augment(img, augmentations=['rotate', 'scale', 'noise']):
        """
        Apply multiple augmentations to image

        Args:
            img: Input image
            augmentations: List of augmentation types to apply

        Returns:
            Augmented image
        """
        aug_img = img.copy()

        if 'rotate' in augmentations:
            aug_img = DataAugmenter.rotate(aug_img)

        if 'scale' in augmentations:
            aug_img = DataAugmenter.scale(aug_img)

        if 'noise' in augmentations:
            aug_img = DataAugmenter.add_noise(aug_img)

        if 'brightness' in augmentations:
            aug_img = DataAugmenter.adjust_brightness(aug_img)

        if 'contrast' in augmentations:
            aug_img = DataAugmenter.adjust_contrast(aug_img)

        return aug_img


class TrainingDataset:
    """Prepare and manage training dataset"""

    def __init__(self, characters_data, char_encoder, image_size=(32, 32)):
        """
        Initialize dataset

        Args:
            characters_data: List of character dictionaries with 'image' and 'label'
            char_encoder: CharacterEncoder instance
            image_size: Target image size
        """
        self.characters_data = characters_data
        self.char_encoder = char_encoder
        self.image_size = image_size
        self.X = None
        self.y = None

    def prepare_data(self, augment=True, augment_factor=3):
        """
        Prepare training data

        Args:
            augment: Whether to apply data augmentation
            augment_factor: Number of augmented copies per image

        Returns:
            X (images), y (labels)
        """
        images = []
        labels = []

        for char_data in self.characters_data:
            img = char_data['image']
            label = char_data['label']

            # Encode label
            label_idx = self.char_encoder.encode(label)
            if label_idx == -1:
                continue  # Skip unknown characters

            # Preprocess image
            img_processed = self._preprocess_image(img)
            images.append(img_processed)
            labels.append(label_idx)

            # Augment
            if augment:
                for _ in range(augment_factor):
                    aug_img = DataAugmenter.augment(img)
                    aug_img_processed = self._preprocess_image(aug_img)
                    images.append(aug_img_processed)
                    labels.append(label_idx)

        self.X = np.array(images)
        self.y = np.array(labels)

        # Add channel dimension
        self.X = np.expand_dims(self.X, axis=-1)

        return self.X, self.y

    def _preprocess_image(self, img):
        """Preprocess single image"""
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Resize
        img = cv2.resize(img, self.image_size)

        # Normalize
        img = img.astype('float32') / 255.0

        return img

    def split_data(self, test_size=0.2, val_size=0.1, random_state=42):
        """
        Split data into train/val/test sets

        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        if self.X is None or self.y is None:
            raise ValueError("Data not prepared. Call prepare_data() first.")

        # Split train and test
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=random_state, stratify=self.y
        )

        # Split train and validation
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_ratio, random_state=random_state, stratify=y_train_val
        )

        return X_train, X_val, X_test, y_train, y_val, y_test

    def get_class_distribution(self):
        """Get distribution of classes in dataset"""
        if self.y is None:
            raise ValueError("Data not prepared. Call prepare_data() first.")

        unique, counts = np.unique(self.y, return_counts=True)
        distribution = {}

        for idx, count in zip(unique, counts):
            char = self.char_encoder.decode(idx)
            distribution[char] = int(count)

        return distribution


class TrainingCallback(keras.callbacks.Callback):
    """Custom callback for training progress"""

    def __init__(self, progress_callback: Callable = None):
        """
        Initialize callback

        Args:
            progress_callback: Function to call with progress updates
                              (epoch, logs) -> None
        """
        super().__init__()
        self.progress_callback = progress_callback

    def on_epoch_end(self, epoch, logs=None):
        """Called at end of each epoch"""
        if self.progress_callback:
            self.progress_callback(epoch, logs or {})


class ModelTrainer:
    """High-level trainer for OCR model"""

    def __init__(self, model, char_encoder):
        """
        Initialize trainer

        Args:
            model: HebrewOCRModel instance
            char_encoder: CharacterEncoder instance
        """
        self.model = model
        self.char_encoder = char_encoder
        self.history = None

    def train(self, characters_data, epochs=50, batch_size=32,
              learning_rate=0.001, augment=True,
              progress_callback=None):
        """
        Train model on character data

        Args:
            characters_data: List of character dictionaries
            epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            augment: Whether to augment data
            progress_callback: Callback for progress updates

        Returns:
            Training history and metrics
        """
        # Prepare dataset
        dataset = TrainingDataset(characters_data, self.char_encoder, self.model.image_size)
        X, y = dataset.prepare_data(augment=augment)

        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = dataset.split_data()

        print(f"Training set: {len(X_train)} samples")
        print(f"Validation set: {len(X_val)} samples")
        print(f"Test set: {len(X_test)} samples")

        # Compile model
        self.model.compile_model(learning_rate=learning_rate)

        # Callbacks
        callbacks = []

        # Early stopping
        callbacks.append(keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        ))

        # Learning rate reduction
        callbacks.append(keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7
        ))

        # Custom progress callback
        if progress_callback:
            callbacks.append(TrainingCallback(progress_callback))

        # Train
        history = self.model.train(
            X_train, y_train,
            X_val, y_val,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks
        )

        # Evaluate on test set
        test_metrics = self.model.evaluate(X_test, y_test)

        # Get class distribution
        class_dist = dataset.get_class_distribution()

        return {
            'history': history.history,
            'test_metrics': test_metrics,
            'num_samples': len(X_train),
            'class_distribution': class_dist
        }

    def incremental_train(self, new_characters_data, epochs=10, learning_rate=0.0001):
        """
        Incrementally train model on new data (fine-tuning)

        Args:
            new_characters_data: New character data
            epochs: Number of epochs
            learning_rate: Lower learning rate for fine-tuning

        Returns:
            Training results
        """
        # Prepare new dataset
        dataset = TrainingDataset(new_characters_data, self.char_encoder, self.model.image_size)
        X, y = dataset.prepare_data(augment=True, augment_factor=5)

        # Split data
        X_train, X_val, _, y_train, y_val, _ = dataset.split_data()

        # Recompile with lower learning rate
        self.model.compile_model(learning_rate=learning_rate)

        # Train
        history = self.model.train(
            X_train, y_train,
            X_val, y_val,
            epochs=epochs,
            batch_size=16
        )

        return {
            'history': history.history,
            'num_new_samples': len(X_train)
        }
