"""AWS S3 storage backend with dual-bucket architecture.

This module implements S3 storage with separate buckets for:
- Original (unmasked) documents
- Masked/encrypted documents
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict
from pathlib import Path
import logging
from io import BytesIO

from storage.storage_interface import StorageBackend
from config import settings

logger = logging.getLogger(__name__)


class S3Storage(StorageBackend):
    """
    AWS S3 storage backend with dual-bucket support.
    
    Architecture:
    - Bucket 1: smartcloud-vault-original (original/unmasked documents)
    - Bucket 2: smartcloud-vault-masked (masked/encrypted documents)
    
    S3 Key Format: {company}/{file_id}/{filename}
    """
    
    def __init__(
        self,
        original_bucket: str,
        masked_bucket: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize S3 storage client.
        
        Args:
            original_bucket: S3 bucket name for original documents
            masked_bucket: S3 bucket name for masked documents
            aws_access_key_id: AWS access key (uses env var if None)
            aws_secret_access_key: AWS secret key (uses env var if None)
            region_name: AWS region (uses env var if None)
        """
        self.original_bucket = original_bucket
        self.masked_bucket = masked_bucket
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id or settings.aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key or settings.aws_secret_access_key,
                region_name=region_name or settings.aws_region
            )
            logger.info(f"S3 client initialized for region: {region_name or settings.aws_region}")
            logger.info(f"Original bucket: {original_bucket}, Masked bucket: {masked_bucket}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _generate_s3_key(self, file_id: str, filename: str, company: Optional[str] = None) -> str:
        """
        Generate S3 key for file storage.
        
        Format: {company}/{file_id}/{filename}
        If company is not provided, use: files/{file_id}/{filename}
        
        Args:
            file_id: Unique file identifier
            filename: Original filename
            company: Company name (optional)
        
        Returns:
            str: S3 object key
        """
        if company:
            return f"{company}/{file_id}/{filename}"
        return f"files/{file_id}/{filename}"
    
    async def save_original(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """
        Upload original file to S3 original bucket.
        
        Args:
            file_content: File binary content
            file_id: Unique file identifier
            filename: Original filename
            company: Company name (optional, for organizing files)
        
        Returns:
            dict: Storage metadata
        """
        try:
            s3_key = self._generate_s3_key(file_id, filename, company)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.original_bucket,
                Key=s3_key,
                Body=file_content,
                ServerSideEncryption='AES256',  # Enable encryption at rest
                Metadata={
                    'file-id': file_id,
                    'original-filename': filename
                }
            )
            
            logger.info(f"Uploaded original file to S3: {self.original_bucket}/{s3_key}")
            
            return {
                'storage_type': 's3',
                'bucket': self.original_bucket,
                's3_key': s3_key,
                'file_id': file_id,
                'filename': filename,
                'size': len(file_content)
            }
        
        except ClientError as e:
            logger.error(f"Failed to upload original file to S3: {e}")
            raise Exception(f"S3 upload failed: {e}")
    
    async def save_masked(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """
        Upload masked file to S3 masked bucket.
        
        Args:
            file_content: Masked file binary content
            file_id: Unique file identifier
            filename: Original filename (will be stored as {filename}_masked)
            company: Company name (optional)
        
        Returns:
            dict: Storage metadata
        """
        try:
            # Add _masked suffix to filename
            file_parts = filename.rsplit('.', 1)
            if len(file_parts) == 2:
                masked_filename = f"{file_parts[0]}_masked.{file_parts[1]}"
            else:
                masked_filename = f"{filename}_masked"
            
            s3_key = self._generate_s3_key(file_id, masked_filename, company)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.masked_bucket,
                Key=s3_key,
                Body=file_content,
                ServerSideEncryption='AES256',  # Enable encryption at rest
                Metadata={
                    'file-id': file_id,
                    'original-filename': filename,
                    'masked': 'true'
                }
            )
            
            logger.info(f"Uploaded masked file to S3: {self.masked_bucket}/{s3_key}")
            
            return {
                'storage_type': 's3',
                'bucket': self.masked_bucket,
                's3_key': s3_key,
                'file_id': file_id,
                'filename': masked_filename,
                'size': len(file_content)
            }
        
        except ClientError as e:
            logger.error(f"Failed to upload masked file to S3: {e}")
            raise Exception(f"S3 upload failed: {e}")
    
    async def get_original(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """
        Download original file from S3.
        
        Args:
            file_id: File identifier
            storage_key: S3 key (required for S3 storage)
        
        Returns:
            bytes: File content or None if not found
        """
        if not storage_key:
            logger.error(f"S3 key required to fetch original file for {file_id}")
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.original_bucket,
                Key=storage_key
            )
            
            content = response['Body'].read()
            logger.info(f"Downloaded original file from S3: {self.original_bucket}/{storage_key}")
            return content
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Original file not found in S3: {storage_key}")
            else:
                logger.error(f"Failed to download original file from S3: {e}")
            return None
    
    async def get_masked(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """
        Download masked file from S3.
        
        Args:
            file_id: File identifier
            storage_key: S3 key (required for S3 storage)
        
        Returns:
            bytes: File content or None if not found
        """
        if not storage_key:
            logger.error(f"S3 key required to fetch masked file for {file_id}")
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.masked_bucket,
                Key=storage_key
            )
            
            content = response['Body'].read()
            logger.info(f"Downloaded masked file from S3: {self.masked_bucket}/{storage_key}")
            return content
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Masked file not found in S3: {storage_key}")
            else:
                logger.error(f"Failed to download masked file from S3: {e}")
            return None
    
    def get_original_path(self, file_id: str, storage_key: Optional[str] = None) -> Optional[Path]:
        """
        S3 storage does not have local paths.
        
        Returns:
            None (always, as S3 files are not local)
        """
        return None
    
    async def delete_original(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """
        Delete original file from S3.
        
        Args:
            file_id: File identifier
            storage_key: S3 key
        
        Returns:
            bool: True if deleted, False otherwise
        """
        if not storage_key:
            logger.error(f"S3 key required to delete original file for {file_id}")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.original_bucket,
                Key=storage_key
            )
            logger.info(f"Deleted original file from S3: {self.original_bucket}/{storage_key}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to delete original file from S3: {e}")
            return False
    
    async def delete_masked(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """
        Delete masked file from S3.
        
        Args:
            file_id: File identifier
            storage_key: S3 key
        
        Returns:
            bool: True if deleted, False otherwise
        """
        if not storage_key:
            logger.error(f"S3 key required to delete masked file for {file_id}")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.masked_bucket,
                Key=storage_key
            )
            logger.info(f"Deleted masked file from S3: {self.masked_bucket}/{storage_key}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to delete masked file from S3: {e}")
            return False
    
    def generate_presigned_url(self, bucket: str, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate pre-signed URL for temporary file access.
        
        Args:
            bucket: S3 bucket name
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Pre-signed URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            logger.info(f"Generated pre-signed URL for {bucket}/{s3_key}")
            return url
        
        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL: {e}")
            return None
