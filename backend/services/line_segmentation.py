import cv2
import numpy as np
from typing import List, Tuple

class LineSegmenter:
    """Service for segmenting text lines from images"""

    @staticmethod
    def segment_lines(img, min_line_height=10, max_gap=15):
        """
        Segment image into text lines using horizontal projection

        Args:
            img: Grayscale image (numpy array)
            min_line_height: Minimum height for a valid line
            max_gap: Maximum gap between lines to consider them separate

        Returns:
            List of tuples (y_start, y_end, line_image)
        """
        # Ensure binary image (white text on black background)
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

        # Calculate horizontal projection (sum of white pixels per row)
        h_projection = np.sum(binary, axis=1)

        # Find line boundaries
        lines = []
        in_line = False
        line_start = 0

        for i, value in enumerate(h_projection):
            if value > 0 and not in_line:
                # Start of a line
                line_start = i
                in_line = True
            elif value == 0 and in_line:
                # End of a line
                line_end = i
                line_height = line_end - line_start

                if line_height >= min_line_height:
                    lines.append((line_start, line_end))

                in_line = False

        # Handle last line if image ends with text
        if in_line:
            lines.append((line_start, len(h_projection)))

        # Merge lines that are too close
        merged_lines = LineSegmenter._merge_close_lines(lines, max_gap)

        # Extract line images
        result = []
        for idx, (y_start, y_end) in enumerate(merged_lines):
            line_img = img[y_start:y_end, :]
            result.append({
                'line_order': idx,
                'y_start': int(y_start),
                'y_end': int(y_end),
                'image': line_img
            })

        return result

    @staticmethod
    def _merge_close_lines(lines, max_gap):
        """Merge lines that are closer than max_gap"""
        if not lines:
            return []

        merged = [lines[0]]

        for current_start, current_end in lines[1:]:
            last_start, last_end = merged[-1]

            # Check gap between last line end and current line start
            gap = current_start - last_end

            if gap <= max_gap:
                # Merge lines
                merged[-1] = (last_start, current_end)
            else:
                # Add as new line
                merged.append((current_start, current_end))

        return merged

    @staticmethod
    def segment_lines_advanced(img, min_line_height=10):
        """
        Advanced line segmentation using contours and morphological operations

        Args:
            img: Grayscale image
            min_line_height: Minimum height for a valid line

        Returns:
            List of line information dictionaries
        """
        # Ensure binary image
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

        # Apply morphological operations to connect text in lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        dilated = cv2.dilate(binary, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get bounding boxes and sort by y-coordinate
        line_boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h >= min_line_height:
                line_boxes.append((y, y + h, x, w))

        # Sort lines from top to bottom
        line_boxes.sort(key=lambda box: box[0])

        # Extract line images
        result = []
        for idx, (y_start, y_end, x_start, width) in enumerate(line_boxes):
            line_img = img[y_start:y_end, :]
            result.append({
                'line_order': idx,
                'y_start': int(y_start),
                'y_end': int(y_end),
                'image': line_img
            })

        return result

    @staticmethod
    def draw_line_separators(img, lines):
        """
        Draw horizontal lines on image to visualize line segmentation

        Args:
            img: Original image
            lines: List of line dictionaries with y_start and y_end

        Returns:
            Image with drawn lines
        """
        # Convert to color if grayscale
        if len(img.shape) == 2:
            img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            img_color = img.copy()

        # Draw lines
        for line in lines:
            y_start = line['y_start']
            y_end = line['y_end']

            # Draw top border (red)
            cv2.line(img_color, (0, y_start), (img.shape[1], y_start), (0, 0, 255), 2)

            # Draw bottom border (blue)
            cv2.line(img_color, (0, y_end), (img.shape[1], y_end), (255, 0, 0), 2)

        return img_color

    @staticmethod
    def get_line_spacing_stats(lines):
        """
        Calculate statistics about line spacing

        Args:
            lines: List of line dictionaries

        Returns:
            Dictionary with spacing statistics
        """
        if len(lines) < 2:
            return {'mean_gap': 0, 'median_gap': 0, 'mean_height': 0}

        gaps = []
        heights = []

        for i in range(len(lines) - 1):
            gap = lines[i + 1]['y_start'] - lines[i]['y_end']
            gaps.append(gap)

        for line in lines:
            height = line['y_end'] - line['y_start']
            heights.append(height)

        return {
            'mean_gap': np.mean(gaps) if gaps else 0,
            'median_gap': np.median(gaps) if gaps else 0,
            'std_gap': np.std(gaps) if gaps else 0,
            'mean_height': np.mean(heights) if heights else 0,
            'median_height': np.median(heights) if heights else 0,
            'num_lines': len(lines)
        }
