# backend/main.py - Simplified with minimal environment dependency
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import engine, Base
from endpoints import auth, users, chat
from liferank_mcp.client import initialize_mcp, shutdown_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Life Rank API with MCP integration...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize MCP client
    mcp_success = await initialize_mcp()
    if mcp_success:
        logger.info("MCP integration initialized successfully")
    else:
        logger.warning("MCP initialization failed - AI coaching will use fallback mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Life Rank API...")
    await shutdown_mcp()
    logger.info("MCP client disconnected")

# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Life Rank API",
    description="Personal life scoring platform with AI Coach using MCP",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware - hardcoded for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # React development
        "http://localhost:3001",     # Alternative React port
        "https://your-domain.com",   # Production (update as needed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["AI Chat"])

@app.get("/")
async def root():
    return {
        "message": "Life Rank API with MCP-powered AI Coach", 
        "version": "2.1.0",
        "features": ["auth", "users", "ai_chat", "mcp_integration"]
    }


@app.get("/mcp/status")
async def mcp_status():
    """Check MCP integration status"""
    from mcp.client import mcp_client
    
    return {
        "mcp_connected": mcp_client.session is not None,
        "available_tools": len(mcp_client.available_tools) if mcp_client.session else 0,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

if __name__ == "__main__":
    # Hardcoded development settings
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )