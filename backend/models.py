# File: models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Null for Google OAuth users
    google_id = Column(String(100), unique=True, nullable=True)  # For Google OAuth
    avatar_url = Column(String(500), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    life_stats = relationship("UserLifeStats", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("UserGoals", back_populates="user", cascade="all, delete-orphan")
    score_updates = relationship("ScoreUpdate", back_populates="user", cascade="all, delete-orphan")  # NEW
    logs = relationship("UserLog", back_populates="user", cascade="all, delete-orphan")  # NEW

class UserLifeStats(Base):
    __tablename__ = "user_life_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, default=7.0)
    health_score = Column(Float, default=7.0)
    career_score = Column(Float, default=7.0)
    relationship_score = Column(Float, default=7.0)
    finance_score = Column(Float, default=7.0)
    personal_score = Column(Float, default=7.0)
    social_score = Column(Float, default=7.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User", back_populates="life_stats")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(String(10), nullable=False)  # 'user' or 'ai'
    timestamp = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="chat_history")

class UserGoals(Base):
    __tablename__ = "user_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True)
    progress = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User", back_populates="goals")

class ScoreUpdate(Base):
    __tablename__ = "score_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # 'health', 'career', etc.
    old_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="score_updates")

class UserLog(Base):
    __tablename__ = "user_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)  # What they did
    timestamp = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="logs")