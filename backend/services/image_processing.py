import cv2
import numpy as np
from PIL import Image
import io
import base64

class ImageProcessor:
    """Service for image enhancement and preprocessing"""

    @staticmethod
    def enhance_image(image_data, brightness=0, contrast=1.0, blur=0, threshold=None, sharpen=0):
        """
        Enhance image with various parameters

        Args:
            image_data: Image as numpy array or PIL Image
            brightness: Brightness adjustment (-100 to 100)
            contrast: Contrast multiplier (0.5 to 3.0)
            blur: Gaussian blur kernel size (0 = no blur, odd numbers only)
            threshold: Binary threshold value (0-255, None = no threshold)
            sharpen: Sharpening intensity (0 = no sharpen, 1-10)

        Returns:
            Enhanced image as numpy array
        """
        # Convert to numpy array if PIL Image
        if isinstance(image_data, Image.Image):
            img = np.array(image_data)
        else:
            img = image_data.copy()

        # Convert to grayscale if color
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Apply brightness and contrast
        img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)

        # Apply Gaussian blur for noise reduction
        if blur > 0:
            # Ensure kernel size is odd
            kernel_size = blur if blur % 2 == 1 else blur + 1
            img = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

        # Apply sharpening
        if sharpen > 0:
            kernel = np.array([[-1, -1, -1],
                             [-1, 9 + sharpen, -1],
                             [-1, -1, -1]])
            img = cv2.filter2D(img, -1, kernel)

        # Apply binary threshold
        if threshold is not None:
            _, img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)

        return img

    @staticmethod
    def load_image_from_path(image_path):
        """Load image from file path"""
        return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    @staticmethod
    def load_image_from_bytes(image_bytes):
        """Load image from bytes"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        return img

    @staticmethod
    def save_image(img, output_path):
        """Save image to file"""
        cv2.imwrite(output_path, img)

    @staticmethod
    def image_to_base64(img):
        """Convert numpy image to base64 string"""
        # Encode image to PNG
        success, buffer = cv2.imencode('.png', img)
        if not success:
            raise ValueError("Failed to encode image")

        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    @staticmethod
    def base64_to_image(base64_string):
        """Convert base64 string to numpy image"""
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        # Decode base64
        img_bytes = base64.b64decode(base64_string)
        return ImageProcessor.load_image_from_bytes(img_bytes)

    @staticmethod
    def resize_image(img, max_width=2000, max_height=2000):
        """Resize image while maintaining aspect ratio"""
        h, w = img.shape[:2]

        if w <= max_width and h <= max_height:
            return img

        # Calculate scaling factor
        scale = min(max_width / w, max_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def auto_rotate(img):
        """Auto-rotate image to correct orientation"""
        # Detect text orientation using OpenCV
        coords = np.column_stack(np.where(img > 0))
        if len(coords) == 0:
            return img

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = 90 + angle

        # Rotate image
        if abs(angle) > 1:  # Only rotate if angle is significant
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(img, M, (w, h),
                               flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)

        return img

    @staticmethod
    def remove_borders(img, border_threshold=240):
        """Remove white borders from image"""
        # Find non-white regions
        mask = img < border_threshold
        coords = np.argwhere(mask)

        if len(coords) == 0:
            return img

        # Get bounding box
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        # Crop image
        cropped = img[y_min:y_max+1, x_min:x_max+1]
        return cropped

    @staticmethod
    def denoise(img, strength=10):
        """Apply denoising to image"""
        return cv2.fastNlMeansDenoising(img, None, strength, 7, 21)

    @staticmethod
    def adaptive_threshold(img, block_size=11, c=2):
        """Apply adaptive thresholding"""
        return cv2.adaptiveThreshold(
            img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            c
        )

    @staticmethod
    def invert_if_needed(img):
        """Invert image if background is dark"""
        mean_val = np.mean(img)
        if mean_val < 127:  # Dark background
            return cv2.bitwise_not(img)
        return img
