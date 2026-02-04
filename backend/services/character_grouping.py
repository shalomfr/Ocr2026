import cv2
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from skimage.feature import hog
from typing import List, Dict, Tuple

class CharacterSegmenter:
    """Service for character segmentation and grouping"""

    @staticmethod
    def segment_characters(img, min_area=20, max_area=10000):
        """
        Segment individual characters using connected components

        Args:
            img: Binary image (grayscale)
            min_area: Minimum area for valid character
            max_area: Maximum area for valid character

        Returns:
            List of character dictionaries with bbox and image
        """
        # Ensure binary image (white text on black background)
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )

        characters = []
        char_id = 0

        # Skip label 0 (background)
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]

            # Filter by area
            if min_area <= area <= max_area:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]

                # Extract character image
                char_img = img[y:y+h, x:x+w]

                characters.append({
                    'id': char_id,
                    'bbox': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)},
                    'image': char_img,
                    'area': int(area),
                    'centroid': (float(centroids[i][0]), float(centroids[i][1]))
                })
                char_id += 1

        return characters

    @staticmethod
    def extract_hog_features(char_img, orientations=9, pixels_per_cell=(8, 8)):
        """
        Extract HOG features from character image

        Args:
            char_img: Character image
            orientations: Number of orientation bins
            pixels_per_cell: Size of cell

        Returns:
            HOG feature vector
        """
        # Resize to standard size
        char_img_resized = cv2.resize(char_img, (32, 32))

        # Ensure grayscale
        if len(char_img_resized.shape) == 3:
            char_img_resized = cv2.cvtColor(char_img_resized, cv2.COLOR_BGR2GRAY)

        # Extract HOG features
        features = hog(
            char_img_resized,
            orientations=orientations,
            pixels_per_cell=pixels_per_cell,
            cells_per_block=(2, 2),
            visualize=False,
            feature_vector=True
        )

        return features

    @staticmethod
    def extract_simple_features(char_img):
        """
        Extract simple visual features for clustering

        Returns:
            Feature vector with aspect ratio, density, etc.
        """
        h, w = char_img.shape[:2]

        # Aspect ratio
        aspect_ratio = w / h if h > 0 else 0

        # Density (ratio of black pixels)
        _, binary = cv2.threshold(char_img, 127, 255, cv2.THRESH_BINARY_INV)
        density = np.sum(binary > 0) / (h * w) if h * w > 0 else 0

        # Resize for pixel-based features
        resized = cv2.resize(char_img, (16, 16))
        pixel_features = resized.flatten() / 255.0

        # Combine features
        features = np.concatenate([
            [aspect_ratio, density],
            pixel_features
        ])

        return features

    @staticmethod
    def cluster_characters_kmeans(characters, n_clusters=None, max_clusters=50):
        """
        Cluster characters using K-means

        Args:
            characters: List of character dictionaries
            n_clusters: Number of clusters (None = auto-detect)
            max_clusters: Maximum number of clusters if auto-detecting

        Returns:
            List of characters with assigned group_id
        """
        if not characters:
            return []

        # Extract features
        features = []
        for char in characters:
            feat = CharacterSegmenter.extract_hog_features(char['image'])
            features.append(feat)

        features = np.array(features)

        # Auto-detect number of clusters if not specified
        if n_clusters is None:
            n_clusters = min(len(characters) // 3, max_clusters)
            n_clusters = max(n_clusters, 1)

        # Perform clustering
        if len(characters) < n_clusters:
            n_clusters = len(characters)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features)

        # Assign group IDs
        for i, char in enumerate(characters):
            char['group_id'] = int(labels[i])

        return characters

    @staticmethod
    def cluster_characters_dbscan(characters, eps=0.5, min_samples=2):
        """
        Cluster characters using DBSCAN

        Args:
            characters: List of character dictionaries
            eps: Maximum distance between samples
            min_samples: Minimum samples in neighborhood

        Returns:
            List of characters with assigned group_id
        """
        if not characters:
            return []

        # Extract features
        features = []
        for char in characters:
            feat = CharacterSegmenter.extract_hog_features(char['image'])
            features.append(feat)

        features = np.array(features)

        # Normalize features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        features_normalized = scaler.fit_transform(features)

        # Perform clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(features_normalized)

        # Assign group IDs (-1 = noise/outlier)
        for i, char in enumerate(characters):
            char['group_id'] = int(labels[i])

        return characters

    @staticmethod
    def group_characters_by_similarity(characters, method='kmeans', **kwargs):
        """
        Group characters by visual similarity

        Args:
            characters: List of character dictionaries
            method: Clustering method ('kmeans' or 'dbscan')
            **kwargs: Additional arguments for clustering method

        Returns:
            Dictionary mapping group_id to list of characters
        """
        if method == 'kmeans':
            clustered = CharacterSegmenter.cluster_characters_kmeans(characters, **kwargs)
        elif method == 'dbscan':
            clustered = CharacterSegmenter.cluster_characters_dbscan(characters, **kwargs)
        else:
            raise ValueError(f"Unknown clustering method: {method}")

        # Group by group_id
        groups = {}
        for char in clustered:
            group_id = char['group_id']
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(char)

        # Sort groups by size (largest first)
        sorted_groups = dict(sorted(groups.items(), key=lambda x: len(x[1]), reverse=True))

        return sorted_groups

    @staticmethod
    def draw_character_boxes(img, characters, with_labels=False):
        """
        Draw bounding boxes around characters

        Args:
            img: Original image
            characters: List of character dictionaries
            with_labels: Whether to draw group labels

        Returns:
            Image with drawn boxes
        """
        # Convert to color if grayscale
        if len(img.shape) == 2:
            img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            img_color = img.copy()

        # Color palette for different groups
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (128, 0, 0), (0, 128, 0), (0, 0, 128)
        ]

        for char in characters:
            bbox = char['bbox']
            x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']

            # Choose color based on group_id
            group_id = char.get('group_id', 0)
            color = colors[group_id % len(colors)]

            # Draw rectangle
            cv2.rectangle(img_color, (x, y), (x + w, y + h), color, 2)

            # Draw label if requested
            if with_labels and 'label' in char:
                label = char['label']
                cv2.putText(img_color, label, (x, y - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return img_color

    @staticmethod
    def sort_characters_reading_order(characters, rtl=True):
        """
        Sort characters in reading order (right-to-left for Hebrew)

        Args:
            characters: List of character dictionaries
            rtl: Right-to-left reading order (True for Hebrew)

        Returns:
            Sorted list of characters
        """
        if not characters:
            return []

        # Sort by y-coordinate (top to bottom) then x-coordinate
        sorted_chars = sorted(characters,
                            key=lambda c: (c['bbox']['y'], -c['bbox']['x'] if rtl else c['bbox']['x']))

        return sorted_chars

    @staticmethod
    def merge_character_groups(groups, group_id1, group_id2):
        """
        Merge two character groups

        Args:
            groups: Dictionary of groups
            group_id1: First group ID
            group_id2: Second group ID to merge into first

        Returns:
            Updated groups dictionary
        """
        if group_id1 in groups and group_id2 in groups:
            groups[group_id1].extend(groups[group_id2])
            del groups[group_id2]

            # Update group_id for all characters in merged group
            for char in groups[group_id1]:
                char['group_id'] = group_id1

        return groups
