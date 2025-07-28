# backend/mcp/server.py
import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, UserLifeStats, UserGoals, ChatHistory
from services.user_service import UserService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LifeRankMCPServer:
    def __init__(self):
        self.server = Server("life-rank-coach")
        self.setup_tools()
        self.setup_resources()
        
    def setup_tools(self):
        """Define MCP tools for the AI coach"""
        
        @self.server.call_tool()
        async def get_user_profile(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get user profile information"""
            try:
                user_id = arguments.get("user_id")
                if not user_id:
                    return [types.TextContent(
                        type="text",
                        text="Error: user_id is required"
                    )]
                
                db = SessionLocal()
                try:
                    user = UserService.get_user_by_id(db, user_id)
                    if not user:
                        return [types.TextContent(
                            type="text",
                            text="User not found"
                        )]
                    
                    profile_data = {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "age": user.age,
                        "gender": user.gender,
                        "location": user.location,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    }
                    
                    return [types.TextContent(
                        type="text",
                        text=f"User Profile: {json.dumps(profile_data, indent=2)}"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error getting user profile: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error retrieving user profile: {str(e)}"
                )]

        @self.server.call_tool()
        async def get_user_stats(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get user's life rank statistics"""
            try:
                user_id = arguments.get("user_id")
                if not user_id:
                    return [types.TextContent(
                        type="text",
                        text="Error: user_id is required"
                    )]
                
                db = SessionLocal()
                try:
                    # Get latest stats
                    stats = db.query(UserLifeStats).filter(
                        UserLifeStats.user_id == user_id
                    ).order_by(UserLifeStats.updated_at.desc()).first()
                    
                    if not stats:
                        # Create default stats if none exist
                        stats = UserLifeStats(
                            user_id=user_id,
                            overall_score=7.0,
                            health_score=7.0,
                            career_score=7.0,
                            relationship_score=7.0,
                            finance_score=7.0,
                            personal_score=7.0,
                            social_score=7.0
                        )
                        db.add(stats)
                        db.commit()
                        db.refresh(stats)
                    
                    stats_data = {
                        "overall_score": stats.overall_score,
                        "categories": {
                            "health": stats.health_score,
                            "career": stats.career_score,
                            "relationships": stats.relationship_score,
                            "finances": stats.finance_score,
                            "personal": stats.personal_score,
                            "social": stats.social_score
                        },
                        "last_updated": stats.updated_at.isoformat() if stats.updated_at else None
                    }
                    
                    return [types.TextContent(
                        type="text",
                        text=f"User Life Stats: {json.dumps(stats_data, indent=2)}"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error retrieving user stats: {str(e)}"
                )]

        @self.server.call_tool()
        async def update_user_stats(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Update user's life rank statistics"""
            try:
                user_id = arguments.get("user_id")
                updates = arguments.get("updates", {})
                
                if not user_id:
                    return [types.TextContent(
                        type="text",
                        text="Error: user_id is required"
                    )]
                
                db = SessionLocal()
                try:
                    # Get or create stats
                    stats = db.query(UserLifeStats).filter(
                        UserLifeStats.user_id == user_id
                    ).order_by(UserLifeStats.updated_at.desc()).first()
                    
                    if not stats:
                        stats = UserLifeStats(user_id=user_id)
                        db.add(stats)
                    
                    # Update scores
                    if "overall_score" in updates:
                        stats.overall_score = float(updates["overall_score"])
                    if "health_score" in updates:
                        stats.health_score = float(updates["health_score"])
                    if "career_score" in updates:
                        stats.career_score = float(updates["career_score"])
                    if "relationship_score" in updates:
                        stats.relationship_score = float(updates["relationship_score"])
                    if "finance_score" in updates:
                        stats.finance_score = float(updates["finance_score"])
                    if "personal_score" in updates:
                        stats.personal_score = float(updates["personal_score"])
                    if "social_score" in updates:
                        stats.social_score = float(updates["social_score"])
                    
                    db.commit()
                    db.refresh(stats)
                    
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully updated user stats. New overall score: {stats.overall_score}"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error updating user stats: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error updating user stats: {str(e)}"
                )]

        @self.server.call_tool()
        async def get_user_goals(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get user's goals"""
            try:
                user_id = arguments.get("user_id")
                if not user_id:
                    return [types.TextContent(
                        type="text",
                        text="Error: user_id is required"
                    )]
                
                db = SessionLocal()
                try:
                    goals = db.query(UserGoals).filter(
                        UserGoals.user_id == user_id
                    ).order_by(UserGoals.created_at.desc()).all()
                    
                    goals_data = []
                    for goal in goals:
                        goals_data.append({
                            "id": goal.id,
                            "title": goal.title,
                            "category": goal.category,
                            "progress": goal.progress,
                            "target_date": goal.target_date.isoformat() if goal.target_date else None,
                            "is_completed": goal.is_completed,
                            "created_at": goal.created_at.isoformat() if goal.created_at else None
                        })
                    
                    return [types.TextContent(
                        type="text",
                        text=f"User Goals: {json.dumps(goals_data, indent=2)}"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error getting user goals: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error retrieving user goals: {str(e)}"
                )]

        @self.server.call_tool()
        async def create_user_goal(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Create a new goal for the user"""
            try:
                user_id = arguments.get("user_id")
                title = arguments.get("title")
                category = arguments.get("category")
                target_date = arguments.get("target_date")
                
                if not user_id or not title:
                    return [types.TextContent(
                        type="text",
                        text="Error: user_id and title are required"
                    )]
                
                db = SessionLocal()
                try:
                    from datetime import datetime
                    
                    goal = UserGoals(
                        user_id=user_id,
                        title=title,
                        category=category,
                        progress=0.0,
                        target_date=datetime.fromisoformat(target_date) if target_date else None,
                        is_completed=False
                    )
                    
                    db.add(goal)
                    db.commit()
                    db.refresh(goal)
                    
                    return [types.TextContent(
                        type="text",
                        text=f"Successfully created goal: {title} (ID: {goal.id})"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error creating user goal: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error creating goal: {str(e)}"
                )]

        @self.server.call_tool()
        async def update_goal_progress(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Update progress on a user's goal"""
            try:
                goal_id = arguments.get("goal_id")
                progress = arguments.get("progress")
                
                if not goal_id or progress is None:
                    return [types.TextContent(
                        type="text",
                        text="Error: goal_id and progress are required"
                    )]
                
                db = SessionLocal()
                try:
                    goal = db.query(UserGoals).filter(UserGoals.id == goal_id).first()
                    if not goal:
                        return [types.TextContent(
                            type="text",
                            text="Goal not found"
                        )]
                    
                    goal.progress = float(progress)
                    if goal.progress >= 100:
                        goal.is_completed = True
                    
                    db.commit()
                    db.refresh(goal)
                    
                    return [types.TextContent(
                        type="text",
                        text=f"Updated goal '{goal.title}' progress to {goal.progress}%"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error updating goal progress: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error updating goal progress: {str(e)}"
                )]

        @self.server.call_tool()
        async def get_chat_history(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get user's recent chat history"""
            try:
                user_id = arguments.get("user_id")
                limit = arguments.get("limit", 10)
                
                if not user_id:
                    return [types.TextContent(
                        type="text",
                        text="Error: user_id is required"
                    )]
                
                db = SessionLocal()
                try:
                    messages = db.query(ChatHistory).filter(
                        ChatHistory.user_id == user_id
                    ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
                    
                    chat_data = []
                    for msg in reversed(messages):  # Reverse to get chronological order
                        chat_data.append({
                            "sender": msg.sender,
                            "message": msg.message,
                            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                        })
                    
                    return [types.TextContent(
                        type="text",
                        text=f"Recent Chat History: {json.dumps(chat_data, indent=2)}"
                    )]
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error getting chat history: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error retrieving chat history: {str(e)}"
                )]

    def setup_resources(self):
        """Define MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available resources"""
            return [
                types.Resource(
                    uri="liferank://user-guide",
                    name="Life Rank User Guide",
                    description="Guide for helping users improve their life scores",
                    mimeType="text/plain"
                ),
                types.Resource(
                    uri="liferank://coaching-tips",
                    name="Coaching Tips",
                    description="Tips and strategies for life coaching",
                    mimeType="text/plain"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "liferank://user-guide":
                return """Life Rank User Guide:
                
1. Life Rank Scoring System:
   - Overall Score: Average of all category scores
   - Categories: Health, Career, Relationships, Finances, Personal Growth, Social Life
   - Scale: 1-10 (10 being excellent)

2. Coaching Approach:
   - Be encouraging and supportive
   - Provide specific, actionable advice
   - Focus on small, achievable improvements
   - Celebrate progress and milestones
   - Help users set SMART goals

3. Key Areas to Focus On:
   - Health: Exercise, nutrition, sleep, mental health
   - Career: Skills, networking, job satisfaction, growth
   - Relationships: Family, romantic, friendships
   - Finances: Budgeting, saving, investing, debt management
   - Personal: Hobbies, learning, self-improvement
   - Social: Community involvement, social connections
"""
            elif uri == "liferank://coaching-tips":
                return """Coaching Tips:

1. Active Listening:
   - Pay attention to user's specific concerns
   - Ask clarifying questions
   - Acknowledge their feelings and challenges

2. Goal Setting:
   - Help break down large goals into smaller steps
   - Set specific deadlines and milestones
   - Focus on process goals vs. outcome goals

3. Motivation Techniques:
   - Use positive reinforcement
   - Help users visualize success
   - Connect goals to their values and desires
   - Provide accountability and check-ins

4. Problem-Solving:
   - Help identify obstacles and barriers
   - Brainstorm solutions together
   - Encourage experimentation and learning from failures
"""
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="life-rank-coach",
                    server_version="1.0.0"
                )
            )

# For running as standalone server
async def main():
    server = LifeRankMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())