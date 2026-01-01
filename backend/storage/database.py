"""MongoDB database connection and operations."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from typing import Optional
import logging
import ssl
from config import settings

# Try to use certifi for SSL certificates (handles Windows SSL issues)
try:
    import certifi
    CA_CERTS = certifi.where()
except ImportError:
    CA_CERTS = None

logger = logging.getLogger(__name__)


class Database:
    """Database manager for MongoDB."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB."""
        try:
            # Configure connection based on URL type
            connection_kwargs = {}
            
            # If using MongoDB Atlas, try SSL configuration
            if ("mongodb+srv://" in settings.mongodb_url or 
                "mongodb.net" in settings.mongodb_url):
                
                logger.info("Detected MongoDB Atlas connection")
                
                if CA_CERTS:
                    connection_kwargs['tlsCAFile'] = CA_CERTS
                    logger.info(f"Using certifi CA certificates: {CA_CERTS}")
                
                # Add TLS settings to help with OpenSSL compatibility
                connection_kwargs['tls'] = True
                connection_kwargs['tlsAllowInvalidCertificates'] = True  # For older OpenSSL
                connection_kwargs['tlsAllowInvalidHostnames'] = True     # For older OpenSSL
                
                logger.warning(
                    "Using TLS with relaxed certificate validation. "
                    "If connection fails, consider:\n"
                    "  1. Installing MongoDB locally (mongodb://localhost:27017)\n"
                    "  2. Upgrading to Python 3.11+ (includes newer OpenSSL)\n"
                    "  See MONGODB_CONNECTION_FIX.md for details."
                )
            else:
                logger.info("Using local MongoDB connection (no SSL required)")
            
            cls.client = AsyncIOMotorClient(settings.mongodb_url, **connection_kwargs)
            cls.db = cls.client[settings.mongodb_db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {settings.mongodb_db_name}")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            logger.error(
                "\n=== TROUBLESHOOTING ===\n"
                "If using MongoDB Atlas and getting SSL errors:\n"
                "  • Your Python's OpenSSL may be too old\n"
                "  • Quick fix: Install MongoDB locally\n"
                "  • See: MONGODB_CONNECTION_FIX.md\n"
                "======================="
            )
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
