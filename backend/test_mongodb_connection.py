"""Test MongoDB connection with SSL/TLS fix."""
import asyncio
import sys
import os
import ssl

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from motor.motor_asyncio import AsyncIOMotorClient
import certifi

# MongoDB connection string from .env
MONGODB_URL = "mongodb+srv://taluryash4_db_user:Yash2006@cluster0.yotltcq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

async def test_connection():
    """Test MongoDB connection."""
    print("🔍 Testing MongoDB Connection with SSL/TLS Fix")
    print("-" * 60)
    
    try:
        print(f"\n1️⃣  Connection String: {MONGODB_URL[:50]}...")
        print(f"2️⃣  Python SSL Version: {ssl.OPENSSL_VERSION}")
        print(f"3️⃣  Using certifi CA bundle: {certifi.where()}")
        
        # Create custom SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # For testing only
        
        # Connect with custom SSL context
        print("\n4️⃣  Connecting to MongoDB Atlas with custom SSL context...")
        client = AsyncIOMotorClient(
            MONGODB_URL,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For testing
            tlsAllowInvalidHostnames=True      # For testing
        )
        
        # Test connection
        print("5️⃣  Testing connection (ping)...")
        await client.admin.command('ping')
        
        print("\n✅ ✅ ✅ CONNECTION SUCCESSFUL! ✅ ✅ ✅")
        print("-" * 60)
        
        # Get database info
        db = client['smartcloud_vault']
        collections = await db.list_collection_names()
        print(f"\n📊 Database: smartcloud_vault")
        print(f"📁 Collections: {len(collections)}")
        if collections:
            print(f"   - {', '.join(collections[:5])}")
            if len(collections) > 5:
                print(f"   - ... and {len(collections) - 5} more")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print(f"\nError type: {type(e).__name__}")
        print("-" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
