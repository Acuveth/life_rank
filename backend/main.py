# backend/main.py - Updated with chat endpoints and env loading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import engine, Base
from endpoints import auth, users, chat  # Added chat import

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Life Rank API",
    description="Personal life scoring platform with AI Coach",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["AI Chat"])  # New chat router

@app.get("/")
async def root():
    return {"message": "Life Rank API with AI Coach", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "features": ["auth", "users", "ai_chat"]}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )