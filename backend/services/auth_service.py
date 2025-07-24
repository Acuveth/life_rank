# File: services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import httpx
import os
from google.oauth2 import id_token
from google.auth.transport import requests

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Verify JWT token and return email"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None
    
    @staticmethod
    async def verify_google_token(token: str) -> Optional[dict]:
        """Verify Google ID token and return user info"""
        try:
            # Method 1: Using google-auth library (recommended)
            if GOOGLE_CLIENT_ID:
                try:
                    # Verify the token
                    idinfo = id_token.verify_oauth2_token(
                        token, requests.Request(), GOOGLE_CLIENT_ID
                    )
                    
                    # Additional security check
                    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                        raise ValueError('Wrong issuer.')
                    
                    return {
                        "email": idinfo.get("email"),
                        "full_name": idinfo.get("name"),
                        "google_id": idinfo.get("sub"),
                        "avatar_url": idinfo.get("picture"),
                        "is_verified": idinfo.get("email_verified", False)
                    }
                except ValueError as e:
                    print(f"Google token verification error (Method 1): {str(e)}")
                    # Fall back to Method 2
                    pass
            
            # Method 2: Manual verification via Google's tokeninfo endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    
                    # Verify the audience (client ID) matches
                    if GOOGLE_CLIENT_ID and user_info.get("aud") != GOOGLE_CLIENT_ID:
                        print("Google token audience mismatch")
                        return None
                    
                    return {
                        "email": user_info.get("email"),
                        "full_name": user_info.get("name"),
                        "google_id": user_info.get("sub"),
                        "avatar_url": user_info.get("picture"),
                        "is_verified": user_info.get("email_verified") == "true"
                    }
                else:
                    print(f"Google tokeninfo request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Google token verification error: {str(e)}")
            return None