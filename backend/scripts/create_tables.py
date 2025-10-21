"""Create database tables"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, engine
# Import all models so they are registered with SQLAlchemy
from app.models import User, Invoice, InvoiceLineItem, AuditLog, InvoiceNumberSequence

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    print(f"Models registered: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
