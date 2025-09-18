#!/usr/bin/env python3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Remove the existing database to force a fresh start
if os.path.exists('video_app.db'):
    os.remove('video_app.db')
    print("Removed existing database")

try:
    from app import app, db
    
    with app.app_context():
        # Create all tables from scratch based on current models
        db.create_all()
        print("✓ Database recreated successfully from models")
        
        # Verify the User model works
        from models import User
        print("✓ User model imported successfully")
        
        # Test creating a user to make sure everything works
        test_user = User(email='test@example.com', password_hash='test')
        db.session.add(test_user)
        db.session.commit()
        print("✓ Test user created successfully")
        
        # Verify the user can be queried
        user = User.query.first()
        print(f"✓ User query successful: {user.email}, projects_limit: {user.projects_limit}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
