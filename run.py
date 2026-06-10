#!/usr/bin/env python
"""
Ujima SACCO - Multi-Agent Microfinance Backend
Production-Ready Entry Point

This script loads environment configuration and starts the FastAPI application.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
RELOAD = os.getenv("RELOAD", "False").lower() == "true"

logger.info(f"Starting Ujima SACCO Backend - Environment: {APP_ENV}")

if __name__ == "__main__":
    import uvicorn
    from app.main import app

    # Log startup information
    logger.info(f"🚀 Starting server on {HOST}:{PORT}")
    logger.info(f"📊 Debug mode: {DEBUG}")
    logger.info(f"🔄 Auto-reload: {RELOAD}")
    logger.info(f"📁 Frontend served from: ./static/")

    # Run the application
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level=LOG_LEVEL.lower()
    )
