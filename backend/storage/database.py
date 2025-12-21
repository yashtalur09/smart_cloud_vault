"""MongoDB database connection and operations."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database manager for MongoDB."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            cls.db = cls.client[settings.mongodb_db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")
    
    @classmethod
    async def create_indexes(cls):
        """Create database indexes for performance."""
        if cls.db is None:
            return
        
        # Files collection indexes
        await cls.db.files.create_index("file_id")
        await cls.db.files.create_index([("company", 1), ("department", 1)])
        await cls.db.files.create_index("classification")
        await cls.db.files.create_index("upload_date")
        
        # Detections collection indexes
        await cls.db.detections.create_index("file_id")
        await cls.db.detections.create_index("detection_type")
        
        # Analysis collection indexes
        await cls.db.analysis.create_index([("company", 1), ("department", 1)])
        await cls.db.analysis.create_index("timestamp")
        
        logger.info("Created database indexes")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.db is None:
            raise RuntimeError("Database not initialized")
        return cls.db


# Singleton instance
db = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database."""
    return Database.get_db()
