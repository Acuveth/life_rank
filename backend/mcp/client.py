# backend/mcp/client.py
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import openai
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LifeRankMCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.available_tools = []
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        ) if os.getenv("OPENAI_API_KEY") else None
        
    async def connect(self):
        """Connect to the MCP server"""
        try:
            # In production, you might connect to a running MCP server
            # For now, we'll use subprocess to start the server
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "mcp.server", "life-rank-coach"],
                env=None
            )
            
            self.session = await stdio_client(server_params)
            
            # Initialize the session
            await self.session.initialize()
            
            # List available tools
            tools_result = await self.session.list_tools()
            self.available_tools = tools_result.tools
            
            logger.info(f"Connected to MCP server with {len(self.available_tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool"""
        if not self.session:
            raise Exception("MCP client not connected")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else None
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
    
    async def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user context for AI coaching"""
        context = {}
        
        try:
            # Get user profile
            profile_result = await self.call_tool("get_user_profile", {"user_id": user_id})
            if profile_result:
                context["profile"] = json.loads(profile_result.split("User Profile: ")[1])
            
            # Get user stats
            stats_result = await self.call_tool("get_user_stats", {"user_id": user_id})
            if stats_result:
                context["stats"] = json.loads(stats_result.split("User Life Stats: ")[1])
            
            # Get user goals
            goals_result = await self.call_tool("get_user_goals", {"user_id": user_id})
            if goals_result:
                context["goals"] = json.loads(goals_result.split("User Goals: ")[1])
            
            # Get recent chat history
            chat_result = await self.call_tool("get_chat_history", {"user_id": user_id, "limit": 5})
            if chat_result:
                context["recent_chats"] = json.loads(chat_result.split("Recent Chat History: ")[1])
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
        
        return context
    
    async def generate_coaching_response(self, user_id: int, user_message: str) -> str:
        """Generate an AI coaching response using MCP tools"""
        try:
            # Get user context
            context = await self.get_user_context(user_id)
            
            # Create system prompt with context
            system_prompt = self._create_system_prompt(context)
            
            # Generate response using OpenAI
            if self.openai_client:
                response = await self._generate_with_openai(system_prompt, user_message)
            else:
                response = self._generate_fallback_response(user_message, context)
            
            # Check if we need to update any data based on the conversation
            await self._process_response_actions(user_id, user_message, response, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating coaching response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create a comprehensive system prompt with user context"""
        prompt = """You are a Life Rank AI Coach, a supportive and knowledgeable personal development assistant. Your role is to help users improve their overall life satisfaction and scores across different life categories.

COACHING PRINCIPLES:
- Be encouraging, supportive, and empathetic
- Provide specific, actionable advice
- Focus on small, achievable improvements
- Celebrate progress and milestones
- Help users set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
- Use motivational interviewing techniques

LIFE RANK CATEGORIES (scored 1-10):
- Health: Physical fitness, nutrition, sleep, mental health
- Career: Job satisfaction, skills development, advancement, work-life balance
- Relationships: Family, romantic partnerships, friendships, social connections
- Finances: Budgeting, saving, investing, debt management, financial security
- Personal Growth: Hobbies, learning, self-improvement, creativity
- Social Life: Community involvement, social activities, networking

"""
        
        # Add user context
        if context.get("profile"):
            profile = context["profile"]
            prompt += f"\nUSER PROFILE:\n"
            prompt += f"- Name: {profile.get('full_name', 'Not provided')}\n"
            prompt += f"- Age: {profile.get('age', 'Not provided')}\n"
            prompt += f"- Location: {profile.get('location', 'Not provided')}\n"
        
        if context.get("stats"):
            stats = context["stats"]
            prompt += f"\nCURRENT LIFE SCORES:\n"
            prompt += f"- Overall Score: {stats.get('overall_score', 'N/A')}/10\n"
            for category, score in stats.get("categories", {}).items():
                prompt += f"- {category.title()}: {score}/10\n"
        
        if context.get("goals"):
            goals = context["goals"]
            if goals:
                prompt += f"\nACTIVE GOALS:\n"
                for goal in goals[:5]:  # Show up to 5 goals
                    status = "✅ Completed" if goal.get("is_completed") else f"{goal.get('progress', 0):.0f}% Complete"
                    prompt += f"- {goal.get('title')} ({goal.get('category', 'General')}): {status}\n"
        
        if context.get("recent_chats"):
            chats = context["recent_chats"]
            if chats:
                prompt += f"\nRECENT CONVERSATION CONTEXT:\n"
                for chat in chats[-3:]:  # Show last 3 messages
                    sender = "User" if chat.get("sender") == "user" else "Coach"
                    prompt += f"- {sender}: {chat.get('message', '')[:100]}...\n"
        
        prompt += """\nRESPONSE GUIDELINES:
- Keep responses conversational and personal
- Reference the user's specific scores and goals when relevant
- Provide 1-3 concrete action steps
- Ask follow-up questions to engage the user
- Limit responses to 150-200 words for better engagement
- Use encouraging language and positive reinforcement
"""
        
        return prompt
    
    async def _generate_with_openai(self, system_prompt: str, user_message: str) -> str:
        """Generate response using OpenAI API"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # or "gpt-3.5-turbo" for lower cost
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _generate_fallback_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate fallback response when OpenAI is not available"""
        message_lower = user_message.lower()
        stats = context.get("stats", {})
        categories = stats.get("categories", {})
        goals = context.get("goals", [])
        
        # Health-related responses
        if any(word in message_lower for word in ['health', 'fitness', 'exercise', 'workout', 'diet', 'sleep']):
            health_score = categories.get('health', 7.0)
            if health_score >= 8:
                return f"Fantastic! Your health score of {health_score}/10 shows you're really taking care of yourself. To maintain this excellence, try adding variety to your routine or setting a new fitness challenge. What's your current favorite way to stay active?"
            elif health_score >= 6:
                return f"You're doing well with a health score of {health_score}/10! To boost it further, consider increasing your exercise frequency, focusing on nutrition, or improving your sleep quality. Which area feels most important to you right now?"
            else:
                return f"Your health score of {health_score}/10 shows great potential for improvement! Start small - even 20 minutes of daily walking can make a difference. What's one healthy habit you'd like to build this week?"
        
        # Career responses
        elif any(word in message_lower for word in ['career', 'work', 'job', 'professional', 'skills']):
            career_score = categories.get('career', 7.0)
            return f"Your career score is {career_score}/10 - {'great momentum!' if career_score >= 7 else 'room to grow!'} Consider focusing on skill development, networking, or having a conversation with your manager about your goals. What aspect of your career would you like to develop?"
        
        # Goals and progress
        elif any(word in message_lower for word in ['goal', 'goals', 'progress', 'achievement']):
            if goals:
                completed = sum(1 for g in goals if g.get('progress', 0) >= 90)
                return f"You have {len(goals)} active goals with {completed} nearly complete - impressive! Consistency is key to achieving your objectives. Which goal would you like to focus on this week?"
            else:
                return "Setting clear goals is a powerful way to improve your Life Rank! I'd love to help you create some meaningful objectives. What area of your life would you most like to improve?"
        
        # General encouragement
        else:
            overall_score = stats.get('overall_score', 7.0)
            if overall_score >= 8:
                return f"You're doing amazingly with a {overall_score}/10 overall score! What's been working well for you lately? I'm here to help you maintain this positive momentum."
            elif overall_score >= 6:
                return f"Your {overall_score}/10 overall score shows you're on a good path! Small, consistent improvements in your lowest-scoring areas can have a big impact. What would you like to work on together?"
            else:
                return f"Every journey toward a better life starts with awareness - you're already ahead of the game! With your {overall_score}/10 score, there's exciting potential for growth. What area feels most important to focus on first?"
    
    async def _process_response_actions(self, user_id: int, user_message: str, response: str, context: Dict[str, Any]):
        """Process any actions that should be taken based on the conversation"""
        # This is where you might implement logic to automatically update goals,
        # suggest score updates, or track progress based on user messages
        
        # Example: If user mentions completing a goal
        if any(phrase in user_message.lower() for phrase in ['completed', 'finished', 'done with', 'achieved']):
            # Could automatically update goal progress or suggest celebration
            logger.info(f"User {user_id} mentioned completing something - could update goals")
        
        # Example: If user mentions struggling with something
        if any(phrase in user_message.lower() for phrase in ['struggling', 'difficult', 'hard time', 'failing']):
            # Could lower relevant scores or create supportive goals
            logger.info(f"User {user_id} mentioned struggling - could offer additional support")

# Global MCP client instance
mcp_client = LifeRankMCPClient()

async def initialize_mcp():
    """Initialize the MCP client"""
    success = await mcp_client.connect()
    if success:
        logger.info("MCP client initialized successfully")
    else:
        logger.warning("Failed to initialize MCP client - falling back to basic functionality")
    return success

async def shutdown_mcp():
    """Shutdown the MCP client"""
    await mcp_client.disconnect()
    logger.info("MCP client disconnected")