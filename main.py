from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(cases.router)
app.include_router(search.router)

@app.get("/", tags=["Root"])
async def root():
    """Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.get("/api", tags=["Root"])
async def api_info():
    """API information endpoint"""
    return {
        "message": "Legal Cases Search API",
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "cases": "/cases",
            "search": "/search",
            "docs": "/docs",
            "redoc": "/redoc",
            "dashboard": "/static/index.html"
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

@app.post("/load-sample-data", tags=["Admin"])
async def load_sample_data():
    """Load sample legal case data for testing"""
    from database import get_collection
    
    sample_cases = [
        {
            "case_number": "2025-CA-006779-O",
            "description": "AUGUSTE, LUCIE vs. SIMONET, CHARLENE M.",
            "location": "Div 48",
            "ucn": "482025CA006779A001OX",
            "case_type": "CA - Auto Negligence",
            "status": "Pending",
            "judge_name": "Brian Sandor",
            "filed_date": "2025-07-17",
            "parties": [
                {
                    "name": "LUCIE  AUGUSTE",
                    "type": "Plaintiff",
                    "attorney": "LINA LOPEZ-FULLAM",
                    "atty_phone": "386-281-6794"
                },
                {
                    "name": "CHARLENE M. SIMONET",
                    "type": "Defendant",
                    "attorney": "",
                    "atty_phone": ""
                }
            ],
            "documents": [
                {
                    "date": "07/17/2025",
                    "description": "Complaint",
                    "pages": "3",
                    "doc_link": "https://example.com/doc1.pdf",
                    "path": "orangecounty/2025-CA-006779-O/2025-07-18/Complaint0.pdf"
                }
            ],
            "actor-id": "202502",
            "county": "Orange",
            "court-id": "L6crt-202502-1685",
            "crawled_date": "2025-07-18 08:42:41"
        },
        {
            "case_number": "2025-CV-001234-B",
            "description": "SMITH, JOHN vs. ACME CORPORATION",
            "location": "Div 12",
            "ucn": "122025CV001234B001OX",
            "case_type": "CV - Contract Dispute",
            "status": "Active",
            "judge_name": "Maria Rodriguez",
            "filed_date": "2025-06-15",
            "parties": [
                {
                    "name": "JOHN SMITH",
                    "type": "Plaintiff",
                    "attorney": "MICHAEL JOHNSON",
                    "atty_phone": "407-555-0123"
                },
                {
                    "name": "ACME CORPORATION",
                    "type": "Defendant",
                    "attorney": "SARAH WILLIAMS",
                    "atty_phone": "407-555-0456"
                }
            ],
            "documents": [
                {
                    "date": "06/15/2025",
                    "description": "Initial Complaint",
                    "pages": "5",
                    "doc_link": "https://example.com/doc2.pdf",
                    "path": "orangecounty/2025-CV-001234-B/2025-06-15/Complaint0.pdf"
                }
            ],
            "actor-id": "202501",
            "county": "Orange",
            "court-id": "L6crt-202501-1234",
            "crawled_date": "2025-06-16 09:15:22"
        }
    ]
    
    try:
        collection = get_collection()
        if collection is None:
            return {"message": "Sample data loaded (offline mode)", "count": len(sample_cases)}
        
        # Clear existing data
        await collection.delete_many({})
        
        # Insert sample cases
        result = await collection.insert_many(sample_cases)
        return {
            "message": "Sample data loaded successfully",
            "count": len(result.inserted_ids),
            "inserted_ids": [str(id) for id in result.inserted_ids]
        }
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        return {"message": "Sample data loaded (offline mode)", "count": len(sample_cases)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
