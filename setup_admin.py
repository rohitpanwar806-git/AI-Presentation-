#!/usr/bin/env python3
"""
Setup script to create default admin account for AI Presentation Avatar SaaS
Run this after deploying the backend to set up the initial admin user.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Load environment
load_dotenv()

from backend.db.database import Base
from backend.db.models import User
from backend.core.security import hash_password
from backend import config


def create_admin_user(email: str, password: str, first_name: str = "Admin", last_name: str = "User"):
    """Create or update default admin account."""
    
    print(f"\n{'='*70}")
    print("🔑 AI Presentation Avatar - Admin Setup Script")
    print(f"{'='*70}\n")
    
    # Validate inputs
    if not email or '@' not in email:
        print("❌ Invalid email address")
        return False
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return False
    
    # Create database engine
    try:
        engine = create_engine(config.DATABASE_URL)
        print(f"✓ Connecting to database...")
        print(f"  URL: {config.DATABASE_URL.replace(config.DATABASE_URL.split('@')[0].split('://')[-1], '***')}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Create tables
    try:
        print(f"✓ Creating tables...")
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False
    
    # Create or update admin user
    email = email.strip().lower()
    
    try:
        with Session(engine) as db:
            # Check if user exists
            existing = db.query(User).filter(User.email == email).first()
            
            if existing:
                print(f"\n ℹ  User already exists: {email}")
                print(f"    Updating as admin...\n")
                existing.first_name = first_name
                existing.last_name = last_name
                existing.password_hash = hash_password(password)
                existing.is_admin = True
                existing.is_verified = True
                existing.is_active = True
                existing.login_provider = "email"
                existing.last_login_at = datetime.now(timezone.utc)
                db.commit()
                user = existing
            else:
                print(f"\n✓ Creating new admin account...")
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password_hash=hash_password(password),
                    is_admin=True,
                    is_verified=True,
                    is_active=True,
                    login_provider="email",
                    last_login_at=datetime.now(timezone.utc),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            print(f"\n{'='*70}")
            print("✅ Admin Account Setup Complete!")
            print(f"{'='*70}\n")
            print(f"📧 Email:    {user.email}")
            print(f"👤 Name:     {user.first_name} {user.last_name}")
            print(f"🔐 Role:     Administrator")
            print(f"✓ Status:    Active & Verified")
            print(f"🔗 Provider: Email/Password\n")
            
            print(f"{'='*70}")
            print("Next Steps:")
            print(f"{'='*70}")
            print(f"1. Deploy backend to Cloud Run")
            print(f"2. Deploy frontend to Vercel")
            print(f"3. Sign in with:")
            print(f"   Email: {email}")
            print(f"   Password: (your password)")
            print(f"4. Admin panel will be visible after sign-in")
            print(f"5. Manage other users from admin panel\n")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        return False


def main():
    print("\n")
    
    # Get admin email
    admin_email = input("🔑 Admin email address: ").strip()
    if not admin_email:
        print("❌ Email is required")
        sys.exit(1)
    
    # Get password
    import getpass
    admin_password = getpass.getpass("🔐 Admin password (min 8 chars, hidden): ")
    if not admin_password:
        print("❌ Password is required")
        sys.exit(1)
    
    # Confirm
    confirm = input(f"\nCreate admin account for {admin_email}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        sys.exit(0)
    
    # Create admin
    success = create_admin_user(admin_email, admin_password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
