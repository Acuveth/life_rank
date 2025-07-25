# backend/services/chat_service.py
import openai
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from models import User, ChatHistory, UserLifeStats
from schemas import UserStats, ChatResponse

# Configure OpenAI (you'll need to add your API key to environment)
openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatService:
    @staticmethod
    async def generate_ai_response(message: str, user_stats: Dict, user: User) -> str:
        """Generate AI response using OpenAI or fallback to rule-based responses"""
        
        # If OpenAI is configured, use it
        if openai.api_key and openai.api_key != "your_openai_api_key_here":
            try:
                # Create context from user stats
                context = ChatService._create_user_context(user_stats, user)
                
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a life coach AI assistant for the Life Rank app. "
                                     f"Help users improve their life scores based on their data. "
                                     f"User context: {context}"
                        },
                        {"role": "user", "content": message}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"OpenAI API Error: {e}")
                # Fall back to rule-based response
                pass
        
        # Rule-based fallback responses
        return ChatService._generate_rule_based_response(message, user_stats, user)
    
    @staticmethod
    def _create_user_context(user_stats: Dict, user: User) -> str:
        """Create context string for AI from user data"""
        context = f"User: {user.full_name or user.email}, "
        context += f"Overall Score: {user_stats.get('overall_score', 'Unknown')}/10, "
        
        categories = user_stats.get('categories', {})
        if categories:
            context += "Category scores: "
            for category, score in categories.items():
                context += f"{category}: {score}/10, "
                
        goals = user_stats.get('goals', [])
        if goals:
            context += f"Active goals: {len(goals)} goals in progress"
            
        return context
    
    @staticmethod
    def _generate_rule_based_response(message: str, user_stats: Dict, user: User) -> str:
        """Generate response using rule-based logic when OpenAI is not available"""
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
        """Get user's life rank statistics"""
        # For now, return sample data. You'll replace this with actual database queries
        return {
            "overall_score": 7.2,
            "categories": {
                "health": 8.1,
                "career": 6.8,
                "relationships": 7.5,
                "finances": 6.2,
                "personal": 8.0,
                "social": 7.3
            },
            "goals": [
                {"id": 1, "title": "Exercise 4x per week", "progress": 75, "category": "health"},
                {"id": 2, "title": "Save $500 monthly", "progress": 60, "category": "finances"},
                {"id": 3, "title": "Read 2 books per month", "progress": 90, "category": "personal"},
                {"id": 4, "title": "Network with 5 professionals", "progress": 40, "category": "career"}
            ],
            "weekly_progress": [6.8, 7.0, 6.9, 7.1, 7.2, 7.1, 7.2]
        }
    
    @staticmethod
    async def save_chat_message(db: Session, user_id: int, message: str, sender: str):
        """Save chat message to database"""
        # You'll implement this when you add the ChatHistory model
        pass
    
    @staticmethod
    async def get_chat_history(db: Session, user_id: int, limit: int) -> List[ChatResponse]:
        """Get user's chat history"""
        # For now, return empty list. You'll implement this with actual database queries
        return []
    
    @staticmethod
    async def update_user_stats(db: Session, user_id: int, stats: UserStats) -> Dict:
        """Update user's statistics"""
        # You'll implement this when you add the UserLifeStats model
        return stats.dict()