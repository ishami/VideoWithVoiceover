#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from app import app, db
    from models import User, Project
    
    print(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    with app.app_context():
        # Check what models SQLAlchemy knows about
        print("Models registered with db.metadata:")
        for table_name, table in db.metadata.tables.items():
            print(f"  {table_name}: {table}")
            
        # Try to create tables with more verbose output
        print("\nAttempting to create tables...")
        db.create_all()
        
        # Check if tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        if 'users' in tables:
            columns = inspector.get_columns('users')
            print("Users table columns:")
            for col in columns:
                print(f"  {col['name']}: {col['type']}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
