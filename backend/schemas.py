# File: schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None  # Optional for Google OAuth
    
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuth(BaseModel):
    token: str  # Google OAuth token

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    sender: str  # 'user' or 'ai'
    timestamp: str

class UserStats(BaseModel):
    overall_score: float = 7.0
    categories: Dict[str, float] = {
        "health": 7.0,
        "career": 7.0,
        "relationships": 7.0,
        "finances": 7.0,
        "personal": 7.0,
        "social": 7.0
    }
    goals: List[Dict[str, Any]] = []
    weekly_progress: List[float] = []

class Goal(BaseModel):
    id: Optional[int] = None
    title: str
    category: str
    progress: float = 0.0
    target_date: Optional[datetime] = None
    is_completed: bool = False

class GoalCreate(BaseModel):
    title: str
    category: str
    target_date: Optional[datetime] = None

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    progress: Optional[float] = None
    target_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

class ScoreUpdateCreate(BaseModel):
    category: str  # 'health', 'career', etc.
    new_score: float

class ScoreUpdateResponse(BaseModel):
    id: int
    category: str
    old_score: float
    new_score: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

# NEW: User Log schemas (just description)
class UserLogCreate(BaseModel):
    description: str  # What they did

class UserLogResponse(BaseModel):
    id: int
    description: str
    timestamp: datetime
    
    class Config:
        from_attributes = True