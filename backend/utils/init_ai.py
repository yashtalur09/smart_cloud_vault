"""Make AI models optional to allow app to run without them."""
from ai_engine.detector import detector
import logging

logger = logging.getLogger(__name__)

try:
    detector.initialize()
    logger.info("AI models loaded successfully")
except Exception as e:
    logger.warning(f"AI models failed to load: {e}")
    logger.warning("Application will run with regex-only detection")
    detector.ai_detector.models_loaded = False
