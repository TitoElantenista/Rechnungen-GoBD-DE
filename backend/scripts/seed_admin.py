"""Seed initial admin user"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User

def seed_admin():
    """Create initial admin user"""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@rechnungen-gobd.de",
            hashed_password=get_password_hash("admin"),
            full_name="Administrator",
            is_active=True,
            is_superuser=True,
            created_at=datetime.utcnow(),
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Created admin user:")
        print("   Username: admin")
        print("   Password: admin")
        print("   ⚠️  CHANGE PASSWORD IN PRODUCTION!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
