from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from datetime import datetime

from config import settings
from database import connect_to_mongo, close_mongo_connection
from routers import cases, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Legal Cases Search API...")
    try:
        await connect_to_mongo()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal Cases Search API...")
    try:
        await close_mongo_connection()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cases.router)
app.include_router(search.router)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Legal Cases Search API",
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "cases": "/cases",
            "search": "/search",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    from database import mongodb
    
    try:
        # Check database connection
        if mongodb.client:
            await mongodb.client.admin.command('ping')
            db_status = "connected"
        else:
            db_status = "offline"
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        db_status = "offline"
    
    # API is healthy even in offline mode
    health_status = "healthy"
    
    return {
        "status": health_status,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": settings.API_VERSION,
        "mode": "offline" if db_status == "offline" else "online"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
