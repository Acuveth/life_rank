# backend/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import openai
import os
from datetime import datetime

from database import get_db
from schemas import ChatMessage, ChatResponse, UserStats
from services.chat_service import ChatService
from endpoints.auth import get_current_user
from models import User

router = APIRouter()

@router.post("/send", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to AI coach and get response"""
    try:
        # Get user's current stats for context
        user_stats = await ChatService.get_user_stats(db, current_user.id)
        
        # Generate AI response
        ai_response = await ChatService.generate_ai_response(
            message.message, 
            user_stats, 
            current_user
        )
        
        # Save chat history
        await ChatService.save_chat_message(db, current_user.id, message.message, "user")
        await ChatService.save_chat_message(db, current_user.id, ai_response, "ai")
        
        return ChatResponse(
            message=ai_response,
            timestamp=datetime.utcnow().isoformat(),
            sender="ai"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}"
        )

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history with AI coach"""
    try:
        messages = await ChatService.get_chat_history(db, current_user.id, limit)
        return messages
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's life rank stats"""
    try:
        stats = await ChatService.get_user_stats(db, current_user.id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user stats: {str(e)}"
        )

@router.post("/stats/update")
async def update_user_stats(
    stats: UserStats,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's life rank stats"""
    try:
        updated_stats = await ChatService.update_user_stats(db, current_user.id, stats)
        return {"message": "Stats updated successfully", "stats": updated_stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stats: {str(e)}"
        )