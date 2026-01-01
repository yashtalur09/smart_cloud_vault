"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from storage.database import Database
from ai_engine.detector import detector
from ai_engine.context_aware_engine import context_engine

# Import routers
from api import upload, protection, analysis, recommendations, reports, download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting SmartCloud Vault...")
    
    # Connect to database
    await Database.connect_db()
    logger.info("Connected to MongoDB")
    
    # Initialize AI models
    logger.info("Loading AI models (this may take a few minutes)...")
    try:
        detector.initialize()
        logger.info("Legacy detector AI models loaded successfully")
    except Exception as e:
        logger.warning(f"Legacy AI model loading failed: {e}")
        logger.warning("Legacy detector will use regex-only detection")
        detector.ai_detector.models_loaded = False
    
    # Initialize context-aware engine
    logger.info("Initializing context-aware intelligence engine...")
    try:
        context_engine.initialize()
        logger.info("Context-aware engine initialized successfully")
    except Exception as e:
        logger.warning(f"Context-aware engine initialization failed: {e}")
        logger.warning("Will fall back to pattern-based detection only")

    
    yield
    
    # Shutdown
    logger.info("Shutting down SmartCloud Vault...")
    await Database.close_db()


# Create FastAPI app
app = FastAPI(
    title="SmartCloud Vault API",
    description="Sensitive Data Detection and Management System with Context-Aware Intelligence",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(protection.router)
app.include_router(analysis.router)
app.include_router(recommendations.router)
app.include_router(reports.router)
app.include_router(download.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to SmartCloud Vault API",
        "version": "2.0.0",
        "features": [
            "Context-aware document classification",
            "Semantic field detection",
            "Intelligent masking with explainability",
            "OCR processing",
            "Email-based access control"
        ],
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected" if Database.db is not None else "disconnected",
        "legacy_ai_models": "loaded" if detector.ai_detector.models_loaded else "not loaded",
        "context_aware_engine": "initialized" if context_engine.initialized else "not initialized"
    }


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    try:
        db = Database.get_db()
        
        total_files = await db.files.count_documents({})
        total_scans = await db.detections.count_documents({})
        total_companies = len(await db.files.distinct("company"))
        
        return {
            "total_files": total_files,
            "total_scans": total_scans,
            "total_companies": total_companies
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_files": 0,
            "total_scans": 0,
            "total_companies": 0
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
