# backend/endpoints/chat.py - Updated with MCP integration
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from database import get_db
from schemas import ChatMessage, ChatResponse, UserStats, Goal, GoalCreate, GoalUpdate
from services.chat_service import ChatService
from endpoints.auth import get_current_user
from models import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/send", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to AI coach and get response using MCP integration"""
    try:
        # Get user's current stats for context
        user_stats = await ChatService.get_user_stats(db, current_user.id)
        
        # Generate AI response using MCP-enhanced chat service
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
        logger.error(f"Chat service error: {str(e)}")
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
        logger.error(f"Failed to retrieve chat history: {str(e)}")
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
        stats_dict = await ChatService.get_user_stats(db, current_user.id)
        
        # Convert to UserStats schema format
        return UserStats(
            overall_score=stats_dict.get("overall_score", 7.0),
            categories=stats_dict.get("categories", {}),
            goals=[Goal(**goal) for goal in stats_dict.get("goals", [])],
            weekly_progress=stats_dict.get("weekly_progress", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve user stats: {str(e)}")
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
        logger.error(f"Failed to update stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stats: {str(e)}"
        )

# New MCP-enhanced endpoints for goals management
@router.post("/goals", response_model=Goal)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new goal for the user"""
    try:
        db_goal = await ChatService.create_user_goal(
            db=db,
            user_id=current_user.id,
            title=goal_data.title,
            category=goal_data.category,
            target_date=goal_data.target_date
        )
        
        return Goal(
            id=db_goal.id,
            title=db_goal.title,
            category=db_goal.category,
            progress=db_goal.progress,
            target_date=db_goal.target_date,
            is_completed=db_goal.is_completed
        )
        
    except Exception as e:
        logger.error(f"Failed to create goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create goal: {str(e)}"
        )

@router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a goal's progress or details"""
    try:
        # For now, only support progress updates
        if goal_update.progress is not None:
            db_goal = await ChatService.update_goal_progress(
                db=db,
                goal_id=goal_id,
                progress=goal_update.progress
            )
            
            return Goal(
                id=db_goal.id,
                title=db_goal.title,
                category=db_goal.category,
                progress=db_goal.progress,
                target_date=db_goal.target_date,
                is_completed=db_goal.is_completed
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid update data provided"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goal: {str(e)}"
        )

@router.post("/coach/suggest")
async def get_coaching_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI coaching suggestions based on user's current state"""
    try:
        # Get user stats for context
        user_stats = await ChatService.get_user_stats(db, current_user.id)
        
        # Generate suggestions using MCP
        suggestions_message = "Based on my current stats and goals, what should I focus on this week?"
        suggestions = await ChatService.generate_ai_response(
            suggestions_message,
            user_stats,
            current_user
        )
        
        return {
            "suggestions": suggestions,
            "based_on": {
                "overall_score": user_stats.get("overall_score"),
                "lowest_categories": [
                    category for category, score in user_stats.get("categories", {}).items() 
                    if score < 7.0
                ],
                "active_goals": len(user_stats.get("goals", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate coaching suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )

@router.get("/mcp/tools")
async def list_mcp_tools(current_user: User = Depends(get_current_user)):
    """List available MCP tools (for debugging/admin purposes)"""
    try:
        from mcp.client import mcp_client
        
        if not mcp_client.session:
            return {"error": "MCP client not connected", "tools": []}
        
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema.get("properties", {}) if hasattr(tool, 'inputSchema') else {}
            }
            for tool in mcp_client.available_tools
        ]
        
        return {
            "connected": True,
            "tools_count": len(tools),
            "tools": tools
        }
        
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {str(e)}")
        return {"error": str(e), "tools": []}