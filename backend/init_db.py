#!/usr/bin/env python3
"""
Database initialization script for Life Rank application
"""

from database import engine, Base
from models import User, UserLifeStats, ChatHistory, UserGoals
import os
from dotenv import load_dotenv

def init_database():
    """Initialize the database with all tables"""
    
    # Load environment variables
    load_dotenv()
    
    print("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Print table information
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
    
    return True

def check_connection():
    """Check if database connection is working"""
    try:
        from database import SessionLocal
        db = SessionLocal()
        # Try to execute a simple query
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Life Rank Database Initialization")
    print("=" * 40)
    
    # Check connection first
    if not check_connection():
        print("Please check your database configuration and try again.")
        exit(1)
    
    # Initialize database
    if init_database():
        print("\n🎉 Database initialization completed!")
    else:
        print("\n❌ Database initialization failed!")
        exit(1)