"""Storage factory for initializing the appropriate storage backend."""
import logging
from storage.storage_interface import StorageManager
from storage.local_storage import LocalStorage
from storage.s3_storage import S3Storage
from config import settings

logger = logging.getLogger(__name__)


def create_storage_manager() -> StorageManager:
    """
    Create and configure the storage manager based on settings.
    
    Returns:
        StorageManager: Configured storage manager instance
    """
    if settings.use_s3_storage:
        # Initialize S3 storage
        logger.info("Initializing S3 storage backend...")
        
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("AWS credentials not configured. Falling back to local storage.")
            logger.warning("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables to use S3.")
            backend = LocalStorage()
        else:
            try:
                backend = S3Storage(
                    original_bucket=settings.s3_original_bucket,
                    masked_bucket=settings.s3_masked_bucket,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
                logger.info(f"S3 storage initialized successfully")
                logger.info(f"Original bucket: {settings.s3_original_bucket}")
                logger.info(f"Masked bucket: {settings.s3_masked_bucket}")
                logger.info(f"Region: {settings.aws_region}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 storage: {e}")
                logger.warning("Falling back to local storage")
                backend = LocalStorage()
    else:
        # Use local storage
        logger.info("Using local file storage backend")
        backend = LocalStorage()
    
    return StorageManager(backend)


# Create global storage manager instance
storage_manager = create_storage_manager()
