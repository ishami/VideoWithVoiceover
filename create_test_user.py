#!/usr/bin/env python3
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if test user exists
    test_user = User.query.filter_by(email='test@example.com').first()
    
    if not test_user:
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpass123')
        )
        db.session.add(test_user)
        db.session.commit()
        print("Test user created: test@example.com / testpass123")
    else:
        print("Test user already exists: test@example.com")
        
    print(f"User ID: {test_user.id}")
