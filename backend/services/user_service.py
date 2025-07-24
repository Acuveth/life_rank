# File: services/user_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models import User
from schemas import UserCreate, UserUpdate
from services.auth_service import AuthService
from typing import Optional

class UserService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create new user with password"""
        # Check if user already exists
        if UserService.get_user_by_email(db, user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password if provided
        hashed_password = None
        if user.password:
            hashed_password = AuthService.get_password_hash(user.password)
        
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            age=user.age,
            gender=user.gender,
            location=user.location,
            is_verified=False
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def create_google_user(db: Session, google_user_info: dict) -> User:
        """Create user from Google OAuth"""
        # Check if user already exists
        existing_user = UserService.get_user_by_email(db, google_user_info["email"])
        if existing_user:
            # Update Google ID if not set
            if not existing_user.google_id:
                existing_user.google_id = google_user_info["google_id"]
                existing_user.avatar_url = google_user_info.get("avatar_url")
                existing_user.is_verified = google_user_info.get("is_verified", False)
                db.commit()
                db.refresh(existing_user)
            return existing_user
        
        # Create new user
        db_user = User(
            email=google_user_info["email"],
            full_name=google_user_info.get("full_name"),
            google_id=google_user_info["google_id"],
            avatar_url=google_user_info.get("avatar_url"),
            is_verified=google_user_info.get("is_verified", False)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user profile"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not user.hashed_password:
            return None  # Google OAuth user
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user