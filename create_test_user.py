#!/usr/bin/env python3
"""
Create test user for performance testing
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from werkzeug.security import generate_password_hash


def create_test_user():
    """Create a test user for performance testing"""
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(email="test@example.com").first()

        if existing_user:
            print("Test user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Username: {existing_user.username}")
            return

        # Create new test user
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash=generate_password_hash("test_password"),
        )

        try:
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created successfully!")
            print("Email: test@example.com")
            print("Password: test_password")
            print("Username: test_user")
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            db.session.rollback()


if __name__ == "__main__":
    create_test_user()
