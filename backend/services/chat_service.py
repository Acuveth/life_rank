# backend/services/chat_service.py - Updated with MCP integration
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging

from models import User, ChatHistory, UserLifeStats, UserGoals
from schemas import UserStats, ChatResponse
from liferank_mcp.client import mcp_client

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def generate_ai_response(message: str, user_stats: Dict, user: User) -> str:
        """Generate AI response using MCP integration"""
        try:
            # Use MCP client to generate coaching response
            response = await mcp_client.generate_coaching_response(user.id, message)
            return response
            
        except Exception as e:
            logger.error(f"MCP AI Response Error: {e}")
            # Fall back to rule-based response
            return ChatService._generate_rule_based_response(message, user_stats, user)
    
    @staticmethod
    def _generate_rule_based_response(message: str, user_stats: Dict, user: User) -> str:
        """Generate response using rule-based logic when MCP is not available"""
        message_lower = message.lower()
        overall_score = user_stats.get('overall_score', 7.0)
        categories = user_stats.get('categories', {})
        
        # Greeting responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return (f"Hello {user.full_name or 'there'}! I'm your Life Rank AI coach. "
                   f"Your current overall score is {overall_score}/10. "
                   f"What would you like to work on today?")
        
        # Health-related questions
        elif any(word in message_lower for word in ['health', 'fitness', 'exercise', 'workout']):
            health_score = categories.get('health', 7.0)
            if health_score >= 8:
                return (f"Your health score of {health_score}/10 is excellent! "
                       f"To maintain this level, focus on consistency in your routine "
                       f"and consider adding variety to prevent plateaus.")
            elif health_score >= 6:
                return (f"Your health score is {health_score}/10 - good progress! "
                       f"Try increasing your exercise frequency or intensity, "
                       f"and ensure you're getting quality sleep.")
            else:
                return (f"Your health score of {health_score}/10 has room for improvement. "
                       f"Start small: aim for 30 minutes of activity daily "
                       f"and focus on building sustainable habits.")
        
        # Career-related questions
        elif any(word in message_lower for word in ['career', 'work', 'job', 'professional']):
            career_score = categories.get('career', 7.0)
            momentum_text = 'Great momentum!' if career_score >= 7 else "Let's work on improving this."
            return (f"Your career score is {career_score}/10. {momentum_text} "
                   f"Consider networking, skill development, or seeking new challenges "
                   f"to boost this area.")
        
        # Finance-related questions
        elif any(word in message_lower for word in ['money', 'finance', 'financial', 'budget', 'save']):
            finance_score = categories.get('finances', 7.0)
            if finance_score >= 7:
                return (f"Your finance score of {finance_score}/10 is solid! "
                       f"Consider advanced strategies like investments "
                       f"or optimizing your budget for long-term goals.")
            else:
                return (f"Your finance score of {finance_score}/10 suggests there's room to improve. "
                       f"Start with budgeting basics and building an emergency fund.")
        
        # Goals and progress
        elif any(word in message_lower for word in ['goal', 'progress', 'achievement']):
            goals = user_stats.get('goals', [])
            if goals:
                completed_goals = sum(1 for g in goals if g.get('progress', 0) >= 90)
                return (f"You have {len(goals)} active goals, with {completed_goals} nearly complete! "
                       f"Focus on the goals with lower progress to maintain momentum across all areas.")
            else:
                return ("Setting clear, measurable goals is key to improving your Life Rank score. "
                       "What area would you like to set a goal for?")
        
        # Motivation and encouragement
        elif any(word in message_lower for word in ['motivate', 'encourage', 'help', 'improve']):
            if overall_score >= 8:
                return (f"You're doing fantastic with a {overall_score}/10 score! "
                       f"Focus on maintaining your strong areas while fine-tuning the rest.")
            elif overall_score >= 6:
                return (f"You're on the right track with {overall_score}/10. "
                       f"Small, consistent improvements in your weakest areas will have a big impact!")
            else:
                return (f"Every journey starts with a single step. "
                       f"Your {overall_score}/10 score shows potential for growth. "
                       f"Let's focus on one area at a time!")
        
        # Default response
        else:
            lowest_category = min(categories.items(), key=lambda x: x[1]) if categories else ("general wellness", 7.0)
            return (f"I'm here to help you improve your Life Rank! "
                   f"Your overall score is {overall_score}/10, "
                   f"with {lowest_category[0]} being an area for potential growth. "
                   f"What specific aspect would you like to discuss?")
    
    @staticmethod
    async def get_user_stats(db: Session, user_id: int) -> Dict:
        """Get user's life rank statistics from database"""
        try:
            # Get latest stats from database
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
            
            # Get user goals
            goals = db.query(UserGoals).filter(
                UserGoals.user_id == user_id
            ).order_by(UserGoals.created_at.desc()).limit(10).all()
            
            goals_data = []
            for goal in goals:
                goals_data.append({
                    "id": goal.id,
                    "title": goal.title,
                    "category": goal.category,
                    "progress": goal.progress,
                    "is_completed": goal.is_completed
                })
            
            # Calculate weekly progress (mock data for now - you can implement actual tracking)
            weekly_progress = [
                stats.overall_score - 0.4,
                stats.overall_score - 0.2,
                stats.overall_score - 0.1,
                stats.overall_score,
                stats.overall_score + 0.1,
                stats.overall_score,
                stats.overall_score
            ]
            
            return {
                "overall_score": stats.overall_score,
                "categories": {
                    "health": stats.health_score,
                    "career": stats.career_score,
                    "relationships": stats.relationship_score,
                    "finances": stats.finance_score,
                    "personal": stats.personal_score,
                    "social": stats.social_score
                },
                "goals": goals_data,
                "weekly_progress": weekly_progress
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            # Return default stats on error
            return {
                "overall_score": 7.0,
                "categories": {
                    "health": 7.0,
                    "career": 7.0,
                    "relationships": 7.0,
                    "finances": 7.0,
                    "personal": 7.0,
                    "social": 7.0
                },
                "goals": [],
                "weekly_progress": [6.8, 7.0, 6.9, 7.1, 7.2, 7.1, 7.2]
            }
    
    @staticmethod
    async def save_chat_message(db: Session, user_id: int, message: str, sender: str):
        """Save chat message to database"""
        try:
            chat_message = ChatHistory(
                user_id=user_id,
                message=message,
                sender=sender,
                timestamp=datetime.utcnow()
            )
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            return chat_message
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def get_chat_history(db: Session, user_id: int, limit: int) -> List[ChatResponse]:
        """Get user's chat history"""
        try:
            messages = db.query(ChatHistory).filter(
                ChatHistory.user_id == user_id
            ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
            
            chat_responses = []
            for msg in reversed(messages):  # Reverse to get chronological order
                chat_responses.append(ChatResponse(
                    message=msg.message,
                    sender=msg.sender,
                    timestamp=msg.timestamp.isoformat() if msg.timestamp else datetime.utcnow().isoformat()
                ))
            
            return chat_responses
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    @staticmethod
    async def update_user_stats(db: Session, user_id: int, stats: UserStats) -> Dict:
        """Update user's statistics"""
        try:
            # Get or create user stats
            db_stats = db.query(UserLifeStats).filter(
                UserLifeStats.user_id == user_id
            ).order_by(UserLifeStats.updated_at.desc()).first()
            
            if not db_stats:
                db_stats = UserLifeStats(user_id=user_id)
                db.add(db_stats)
            
            # Update scores
            db_stats.overall_score = stats.overall_score
            categories = stats.categories
            db_stats.health_score = categories.get('health', 7.0)
            db_stats.career_score = categories.get('career', 7.0)
            db_stats.relationship_score = categories.get('relationships', 7.0)
            db_stats.finance_score = categories.get('finances', 7.0)
            db_stats.personal_score = categories.get('personal', 7.0)
            db_stats.social_score = categories.get('social', 7.0)
            
            # Calculate overall score as average
            db_stats.overall_score = (
                db_stats.health_score + db_stats.career_score + 
                db_stats.relationship_score + db_stats.finance_score + 
                db_stats.personal_score + db_stats.social_score
            ) / 6
            
            db.commit()
            db.refresh(db_stats)
            
            return {
                "overall_score": db_stats.overall_score,
                "categories": {
                    "health": db_stats.health_score,
                    "career": db_stats.career_score,
                    "relationships": db_stats.relationship_score,
                    "finances": db_stats.finance_score,
                    "personal": db_stats.personal_score,
                    "social": db_stats.social_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def create_user_goal(db: Session, user_id: int, title: str, category: str, target_date=None) -> UserGoals:
        """Create a new goal for the user"""
        try:
            goal = UserGoals(
                user_id=user_id,
                title=title,
                category=category,
                progress=0.0,
                target_date=target_date,
                is_completed=False
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)
            return goal
        except Exception as e:
            logger.error(f"Error creating user goal: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def update_goal_progress(db: Session, goal_id: int, progress: float) -> UserGoals:
        """Update progress on a user's goal"""
        try:
            goal = db.query(UserGoals).filter(UserGoals.id == goal_id).first()
            if not goal:
                raise ValueError("Goal not found")
            
            goal.progress = max(0.0, min(100.0, progress))  # Ensure progress is between 0-100
            if goal.progress >= 100:
                goal.is_completed = True
            
            db.commit()
            db.refresh(goal)
            return goal
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            db.rollback()
            raise