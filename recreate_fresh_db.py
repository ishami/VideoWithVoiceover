#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from app import app, db
    from models import User, Project
    
    with app.app_context():
        print("Dropping all existing tables...")
        db.drop_all()
        
        print("Creating fresh tables from current models...")
        db.create_all()
        
        # Verify the tables were created correctly
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables created: {tables}")
        
        if 'users' in tables:
            columns = inspector.get_columns('users')
            print("Users table columns:")
            for col in columns:
                print(f"  {col['name']}: {col['type']}")
        
        # Test creating a user
        print("\nTesting user creation...")
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
