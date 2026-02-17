import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import db
from routers import admin, chat
from utils.precomputed_audio import precomputed_audio_manager
from utils.tts import text_to_speech_stream

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


async def _precompute_audio():
    """
    Precompute greeting and acknowledgment audio files.
    This reduces latency during conversations.
    """
    try:
        if not os.getenv("ELEVENLABS_API_KEY"):
            logger.warning(
                "ELEVENLABS_API_KEY not found - skipping audio precomputation"
            )
            return

        greeting_text = "Hello! Thank you for contacting customer support. How can I help you today?"
        logger.info(f"Generating greeting audio: '{greeting_text}'")
        greeting_audio = await text_to_speech_stream(greeting_text)
        if greeting_audio:
            precomputed_audio_manager.save_greeting_audio(greeting_text, greeting_audio)
            logger.info(f"✓ Greeting audio saved ({len(greeting_audio)} bytes)")
        else:
            logger.warning("Failed to generate greeting audio")

        acknowledgments = [
            "Let me think...",
            "Okay...",
            "I see...",
            "Alright...",
            "Got it...",
        ]

        for ack_text in acknowledgments:
            logger.info(f"Generating acknowledgment audio: '{ack_text}'")
            ack_audio = await text_to_speech_stream(ack_text)
            if ack_audio:
                precomputed_audio_manager.save_acknowledgment_audio(ack_text, ack_audio)
                logger.info(f"✓ '{ack_text}' saved ({len(ack_audio)} bytes)")
            else:
                logger.warning(f"Failed to generate '{ack_text}'")

        logger.info("✓ All precomputed audio files generated successfully!")

    except Exception as e:
        logger.error(f"Error precomputing audio: {e}")
        logger.warning(
            "Continuing without precomputed audio - will generate on-the-fly"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    logger.info("Starting Best Voice Agent application")

    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    logger.info("Precomputing audio files...")
    await _precompute_audio()

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down Best Voice Agent application")


app = FastAPI(
    title="Best Voice Agent API",
    description="Real-time streaming AI customer support agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Get CORS origins from environment variable
cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost,http://localhost:80"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Best Voice Agent", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        stats = await db.get_stats()

        return {
            "status": "healthy",
            "database": "connected",
            "total_calls": stats.total_calls,
            "pending_calls": stats.pending_calls,
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
