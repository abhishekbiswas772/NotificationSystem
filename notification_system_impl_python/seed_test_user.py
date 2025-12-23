#!/usr/bin/env python3
"""
Seed test user for notification system testing
"""

from app import create_app
from configs.db import db
from models.users import Users
from werkzeug.security import generate_password_hash

app = create_app()

# The user ID that test_all_scenarios.py expects
TEST_USER_ID = "64cf1551-81b5-4199-913c-61a99e170540"
TEST_EMAIL = "test@example.com"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"

def seed_test_user():
    """Create or update test user in database"""
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = Users.query.filter_by(id=TEST_USER_ID).first()

            if existing_user:
                print(f"✓ Test user already exists: {TEST_USER_ID}")
                print(f"  Email: {existing_user.email}")
                print(f"  Username: {existing_user.username}")
                return

            # Check if email/username is taken by another user
            email_exists = Users.query.filter_by(email=TEST_EMAIL).first()
            username_exists = Users.query.filter_by(username=TEST_USERNAME).first()

            if email_exists:
                print(f"✗ Email {TEST_EMAIL} already exists with different user ID")
                print(f"  Deleting old user and creating new one...")
                db.session.delete(email_exists)
                db.session.commit()

            if username_exists and username_exists.id != (email_exists.id if email_exists else None):
                print(f"✗ Username {TEST_USERNAME} already exists with different user ID")
                print(f"  Deleting old user and creating new one...")
                db.session.delete(username_exists)
                db.session.commit()

            # Create new test user
            hashed_password = generate_password_hash(TEST_PASSWORD)

            new_user = Users(
                id=TEST_USER_ID,
                email=TEST_EMAIL,
                username=TEST_USERNAME,
                password=hashed_password
            )

            db.session.add(new_user)
            db.session.commit()

            print(f"✓ Test user created successfully!")
            print(f"  User ID: {TEST_USER_ID}")
            print(f"  Email: {TEST_EMAIL}")
            print(f"  Username: {TEST_USERNAME}")
            print(f"  Password: {TEST_PASSWORD}")
            print(f"\nYou can now run test_all_scenarios.py")

        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating test user: {str(e)}")
            raise

if __name__ == "__main__":
    print("=" * 70)
    print("Seeding Test User for Notification System")
    print("=" * 70)
    print()

    seed_test_user()

    print()
    print("=" * 70)
