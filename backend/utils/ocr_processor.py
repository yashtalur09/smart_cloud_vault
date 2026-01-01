"""OCR processing utilities for extracting text from images."""
import logging
from typing import Optional
from pathlib import Path
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Processes images to extract text using Tesseract OCR."""
    
    def __init__(self):
        """Initialize OCR processor."""
        # Tesseract path configuration (Windows default installation path)
        # Users can override this by setting TESSERACT_CMD environment variable
        import os
        tesseract_cmd = os.getenv('TESSERACT_CMD')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            logger.info(f"Using Tesseract from: {tesseract_cmd}")
    
    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image file using OCR.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Preprocess image for better OCR accuracy
            image = self._preprocess_image(image)
            
            # Extract text using Tesseract with custom configuration
            # PSM 6 = Assume a single uniform block of text
            # For government IDs, PSM 6 works better than default PSM 3
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=custom_config)
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from image: {image_path}")
                return ""
            
            logger.info(f"Successfully extracted {len(text)} characters from {Path(image_path).name}")
            return text.strip()
        
        except pytesseract.TesseractNotFoundError:
            logger.error(
                "Tesseract OCR is not installed or not found in PATH. "
                "Please install Tesseract OCR and set TESSERACT_CMD environment variable if needed."
            )
            raise Exception(
                "Tesseract OCR not found. Please install Tesseract OCR. "
                "See README for installation instructions."
            )
        
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
        
        Returns:
            Preprocessed PIL Image
        """
        try:
            import numpy as np
            from PIL import ImageEnhance, ImageFilter
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if image is too small (helps with low-resolution scans)
            width, height = image.size
            min_dimension = 1000
            if width < min_dimension or height < min_dimension:
                scale = max(min_dimension / width, min_dimension / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Increase contrast by 50%
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Apply slight denoising
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Convert to numpy array for thresholding
            img_array = np.array(image)
            
            # Apply adaptive thresholding to handle varying lighting
            # This converts image to pure black and white
            from PIL import ImageOps
            # Auto contrast helps normalize lighting
            image = ImageOps.autocontrast(image, cutoff=2)
            
            logger.debug("Image preprocessing completed")
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            # Fallback to simple grayscale conversion
            return image.convert('L')
    
    def is_image_file(self, file_extension: str) -> bool:
        """
        Check if file extension is a supported image format.
        
        Args:
            file_extension: File extension (e.g., '.jpg', '.png')
        
        Returns:
            True if supported image format, False otherwise
        """
        supported_formats = {'.jpg', '.jpeg', '.png'}
        return file_extension.lower() in supported_formats


# Create singleton instance
ocr_processor = OCRProcessor()
