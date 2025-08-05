# backend/services/chat_service.py - Updated with file reading and separate tables
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from models import User, ChatHistory, UserLifeStats, UserGoals, ScoreUpdate, UserLog
from schemas import UserStats, ChatResponse
from liferank_mcp.client import mcp_client

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def generate_ai_response(message: str, user_stats: Dict, user: User) -> str:
        """Generate AI response using coach.txt file and ALL user logs/score updates"""
        try:
            # Get coach knowledge from txt file
            coach_knowledge = await ChatService._read_coach_file()
            
            # Get ALL user's logs and score updates (no limits)
            user_logs = await ChatService._get_user_logs_context(user.id)
            score_updates = await ChatService._get_score_updates_context(user.id)
            
            # Create enhanced context with ALL user history
            enhanced_context = ChatService._create_enhanced_context(
                user_stats, user, coach_knowledge, user_logs, score_updates
            )
            
            # Use MCP client to generate coaching response
            response = await mcp_client.generate_coaching_response(user.id, message)
            return response
            
        except Exception as e:
            logger.error(f"MCP AI Response Error: {e}")
            # Fall back to rule-based response with ALL user history
            return ChatService._generate_rule_based_response_with_knowledge(
                message, user_stats, user, coach_knowledge, user_logs, score_updates
            )
    
    @staticmethod
    async def _read_coach_file() -> str:
        """Read coach.txt file from backend directory"""
        try:
            coach_file_path = Path(__file__).parent.parent / "coach.txt"
            
            if coach_file_path.exists():
                with open(coach_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Coach file not found at {coach_file_path}")
                return "DEFAULT COACHING: Be supportive, encouraging, and provide specific actionable advice based on user's scores and recent activities."
                
        except Exception as e:
            logger.error(f"Error reading coach file: {e}")
            return "DEFAULT COACHING: Be supportive, encouraging, and provide specific actionable advice."
    
    @staticmethod
    async def _get_user_logs_context(user_id: int) -> List[Dict]:
        """Get ALL user logs for context (no limit)"""
        try:
            from database import SessionLocal
            db = SessionLocal()
            try:
                # Get ALL user logs (no limit)
                logs = db.query(UserLog).filter(
                    UserLog.user_id == user_id
                ).order_by(UserLog.timestamp.desc()).all()
                
                return [
                    {
                        "description": log.description,
                        "timestamp": log.timestamp.isoformat()
                    }
                    for log in logs
                ]
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting user logs: {e}")
            return []
    
    @staticmethod
    async def _get_score_updates_context(user_id: int) -> List[Dict]:
        """Get ALL user score updates for context (no limit)"""
        try:
            from database import SessionLocal
            db = SessionLocal()
            try:
                # Get ALL score updates (no limit)
                updates = db.query(ScoreUpdate).filter(
                    ScoreUpdate.user_id == user_id
                ).order_by(ScoreUpdate.timestamp.desc()).all()
                
                return [
                    {
                        "category": update.category,
                        "old_score": update.old_score,
                        "new_score": update.new_score,
                        "timestamp": update.timestamp.isoformat()
                    }
                    for update in updates
                ]
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting score updates: {e}")
            return []
    
    @staticmethod
    def _create_enhanced_context(
        user_stats: Dict, 
        user: User, 
        coach_knowledge: str, 
        user_logs: List[Dict], 
        score_updates: List[Dict]
    ) -> str:
        """Create enhanced context with knowledge, ALL logs, and ALL score updates"""
        context = f"""
COACH KNOWLEDGE BASE:
{coach_knowledge}

USER PROFILE:
- Name: {user.full_name or user.email}
- Current Overall Score: {user_stats.get('overall_score', 7.0)}/10

CURRENT LIFE SCORES:
"""
        
        categories = user_stats.get('categories', {})
        for category, score in categories.items():
            context += f"- {category.title()}: {score}/10\n"
        
        if score_updates:
            context += f"\nALL SCORE IMPROVEMENTS HISTORY:\n"
            for update in score_updates:  # ALL updates, no limit
                context += f"- {update['timestamp'][:10]}: {update['category']} improved from {update['old_score']} to {update['new_score']}\n"
        
        if user_logs:
            context += f"\nALL USER ACTIVITIES HISTORY:\n"
            for log in user_logs:  # ALL logs, no limit
                context += f"- {log['timestamp'][:10]}: {log['description']}\n"
        
        context += f"\nUse ALL this history to provide personalized, specific advice that references their past activities and improvements."
        
        return context
    
    @staticmethod
    def _generate_rule_based_response_with_knowledge(
        message: str, 
        user_stats: Dict, 
        user: User, 
        coach_knowledge: str,
        user_logs: List[Dict],
        score_updates: List[Dict]
    ) -> str:
        """Generate response using rule-based logic with coach knowledge and ALL user history"""
        message_lower = message.lower()
        overall_score = user_stats.get('overall_score', 7.0)
        categories = user_stats.get('categories', {})
        
        # Check recent improvements from ALL score updates
        recent_improvements = score_updates[:3] if score_updates else []
        recent_activities = user_logs[:5] if user_logs else []
        
        name = user.full_name or "there"
        
        # Greeting responses with recent progress
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            response = f"Hello {name}! Your current Life Rank score is {overall_score}/10."
            if recent_improvements:
                latest = recent_improvements[0]
                response += f" I see you recently improved your {latest['category']} from {latest['old_score']} to {latest['new_score']} - excellent progress!"
            elif recent_activities:
                response += f" I noticed you recently: {recent_activities[0]['description']} - great work!"
            return response + " What would you like to work on today?"
        
        # Progress and improvement responses
        elif any(word in message_lower for word in ['progress', 'improvement', 'better', 'doing']):
            if recent_improvements:
                response = f"You've been making fantastic progress! Recent improvements:\n"
                for imp in recent_improvements:
                    response += f"• {imp['category'].title()}: {imp['old_score']} → {imp['new_score']}\n"
                if recent_activities:
                    response += f"\nYour recent activities:\n"
                    for activity in recent_activities[:3]:
                        response += f"• {activity['description']}\n"
                response += f"\nYour overall score is now {overall_score}/10. Keep up the momentum!"
                return response
            else:
                return f"Your overall score is {overall_score}/10. Let's work on creating some positive momentum together! What area would you like to focus on?"
        
        # Use coach knowledge for specific advice
        elif any(word in message_lower for word in ['advice', 'help', 'how', 'what should']):
            # Find lowest scoring category for targeted advice
            lowest_category = min(categories.items(), key=lambda x: x[1]) if categories else None
            
            response = f"Based on my coaching knowledge and your current situation:\n\n"
            
            if lowest_category and lowest_category[1] < 7:
                cat_name, cat_score = lowest_category
                response += f"Your {cat_name} score of {cat_score}/10 has the most room for growth. "
                
                # Extract relevant advice from coach knowledge
                if 'HEALTH' in coach_knowledge and cat_name == 'health':
                    response += "For health improvements, start with 10-15 minute daily activities and focus on sleep hygiene."
                elif 'CAREER' in coach_knowledge and cat_name == 'career':
                    response += "For career growth, dedicate 1-2 hours weekly to skill development and focus on quality networking."
                elif 'RELATIONSHIPS' in coach_knowledge and cat_name == 'relationships':
                    response += "For relationships, focus on quality time with device-free conversations and practice active listening."
                elif 'FINANCES' in coach_knowledge and cat_name == 'finances':
                    response += "For finances, start by tracking your expenses and building a small emergency fund."
                else:
                    response += "Start with small, consistent actions in this area."
            
            if recent_activities:
                response += f"\n\nSince you've been working on: {recent_activities[0]['description']}, how has that been going?"
            
            return response
        
        # Motivation requests
        elif any(word in message_lower for word in ['motivated', 'motivation', 'encourage', 'stuck']):
            response = f"I understand it can be challenging sometimes. Let me remind you of your strengths:\n\n"
            
            # Highlight their best areas
            if categories:
                best_category = max(categories.items(), key=lambda x: x[1])
                response += f"Your {best_category[0]} score of {best_category[1]}/10 shows you have the capability for excellence!\n"
            
            if recent_improvements:
                response += f"You've already proven you can improve - look at your recent {recent_improvements[0]['category']} progress!\n"
            elif recent_activities:
                response += f"You've been taking action: {recent_activities[0]['description']} - that shows commitment!\n"
            
            response += f"\nRemember: small, consistent steps lead to big changes. What's one tiny thing you could do today?"
            return response
        
        # Default response with recent context
        lowest_category = min(categories.items(), key=lambda x: x[1]) if categories else ("general wellness", 7.0)
        response = f"I'm here to help you improve your Life Rank of {overall_score}/10!"
        
        if recent_improvements:
            response += f" You've been doing excellent work - I see your {recent_improvements[0]['category']} improved recently."
        elif recent_activities:
            response += f" I noticed you've been active: {recent_activities[0]['description']}."
        
        response += f" Your {lowest_category[0]} area has the most potential for growth. What specific aspect would you like to discuss?"
        return response
    
    @staticmethod
    async def log_user_description(db: Session, user_id: int, description: str) -> UserLog:
        """Log user activity description"""
        try:
            log = UserLog(
                user_id=user_id,
                description=description
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        except Exception as e:
            logger.error(f"Error logging user description: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def update_user_score(
        db: Session, 
        user_id: int, 
        category: str, 
        new_score: float
    ) -> Dict:
        """Update user score and create score update record"""
        try:
            # Get current stats
            stats = db.query(UserLifeStats).filter(
                UserLifeStats.user_id == user_id
            ).order_by(UserLifeStats.updated_at.desc()).first()
            
            if not stats:
                stats = UserLifeStats(user_id=user_id)
                db.add(stats)
            
            # Get old score
            old_score = getattr(stats, f"{category}_score", 7.0)
            
            # Update score
            setattr(stats, f"{category}_score", new_score)
            
            # Recalculate overall score
            stats.overall_score = (
                stats.health_score + stats.career_score + 
                stats.relationship_score + stats.finance_score + 
                stats.personal_score + stats.social_score
            ) / 6
            
            db.commit()
            db.refresh(stats)
            
            # Create score update record
            score_update = ScoreUpdate(
                user_id=user_id,
                category=category,
                old_score=old_score,
                new_score=new_score
            )
            db.add(score_update)
            db.commit()
            db.refresh(score_update)
            
            return {
                "category": category,
                "old_score": old_score,
                "new_score": new_score,
                "overall_score": stats.overall_score
            }
            
        except Exception as e:
            logger.error(f"Error updating user score: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def get_user_logs(db: Session, user_id: int, limit: int = 50) -> List[UserLog]:
        """Get user's activity logs"""
        try:
            logs = db.query(UserLog).filter(
                UserLog.user_id == user_id
            ).order_by(UserLog.timestamp.desc()).limit(limit).all()
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting user logs: {e}")
            return []
    
    @staticmethod
    async def get_score_updates(db: Session, user_id: int, limit: int = 50) -> List[ScoreUpdate]:
        """Get user's score update history"""
        try:
            updates = db.query(ScoreUpdate).filter(
                ScoreUpdate.user_id == user_id
            ).order_by(ScoreUpdate.timestamp.desc()).limit(limit).all()
            
            return updates
            
        except Exception as e:
            logger.error(f"Error getting score updates: {e}")
            return []
    
    # Keep existing methods unchanged
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
            
            # Calculate weekly progress (mock data for now)
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
            for msg in reversed(messages):
                chat_responses.append(ChatResponse(
                    message=msg.message,
                    sender=msg.sender,
                    timestamp=msg.timestamp.isoformat() if msg.timestamp else datetime.utcnow().isoformat()
                ))
            
            return chat_responses
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    # Keep other existing methods...
    @staticmethod
    async def update_user_stats(db: Session, user_id: int, stats: UserStats) -> Dict:
        """Update user's statistics"""
        try:
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
            
            old_progress = goal.progress
            goal.progress = max(0.0, min(100.0, progress))
            if goal.progress >= 100:
                goal.is_completed = True
            
            db.commit()
            db.refresh(goal)
            
            # Log the goal progress as user activity
            await ChatService.log_user_description(
                db=db,
                user_id=goal.user_id,
                description=f"Updated progress on '{goal.title}' from {old_progress:.0f}% to {goal.progress:.0f}%"
            )
            
            return goal
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            db.rollback()
            raise