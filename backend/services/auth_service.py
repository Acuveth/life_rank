# backend/services/auth_service.py - Simplified with minimal env dependency
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import httpx
import os
from google.oauth2 import id_token
from google.auth.transport import requests
import json

# Hardcoded configuration with sensible defaults
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Hardcoded - 30 minutes is good default

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
        """Verify Google JWT ID token and return user info"""
        try:
            # Method 1: Using Google's official library (if client ID is configured)
            google_client_id = os.getenv("GOOGLE_CLIENT_ID")
            if google_client_id and google_client_id != "your_google_client_id_here":
                try:
                    # Verify the token using Google's library
                    idinfo = id_token.verify_oauth2_token(
                        token, 
                        requests.Request(), 
                        google_client_id
                    )
                    
                    # Token is valid, extract user info
                    return {
                        "email": idinfo.get("email"),
                        "full_name": idinfo.get("name"),
                        "google_id": idinfo.get("sub"),
                        "avatar_url": idinfo.get("picture"),
                        "is_verified": idinfo.get("email_verified", False)
                    }
                except ValueError as e:
                    print(f"Google token verification failed: {e}")
                    return None
            
            # Method 2: Manual JWT decoding (fallback - less secure)
            try:
                # Decode the JWT token without verification
                unverified_payload = jwt.get_unverified_claims(token)
                
                # Basic validation
                if unverified_payload.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                    print("Invalid Google token issuer")
                    return None
                
                # Check expiration
                exp = unverified_payload.get("exp")
                if exp and datetime.utcnow().timestamp() > exp:
                    print("Google token expired")
                    return None
                
                # Return user info (WARNING: Less secure without proper verification)
                return {
                    "email": unverified_payload.get("email"),
                    "full_name": unverified_payload.get("name"),
                    "google_id": unverified_payload.get("sub"),
                    "avatar_url": unverified_payload.get("picture"),
                    "is_verified": unverified_payload.get("email_verified", False)
                }
                
            except Exception as e:
                print(f"Manual JWT decoding failed: {e}")
                return None
                
        except Exception as e:
            print(f"Google token verification error: {str(e)}")
            return None