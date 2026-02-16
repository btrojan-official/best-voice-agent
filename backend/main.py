import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import chat, admin
from models import db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    logger.info("Starting Best Voice Agent application")
    
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    logger.info("Application startup complete")
    
    yield
    
    logger.info("Shutting down Best Voice Agent application")


app = FastAPI(
    title="Best Voice Agent API",
    description="Real-time streaming AI customer support agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://localhost",       # Docker nginx frontend
        "http://localhost:80"     # Explicit port 80
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Best Voice Agent",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        stats = await db.get_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_calls": stats.total_calls,
            "pending_calls": stats.pending_calls
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
