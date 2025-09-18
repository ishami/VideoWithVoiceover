#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    # Just try to import and inspect the User model
    from models import User
    
    print("User model attributes:")
    for attr in dir(User):
        if not attr.startswith('_'):
            print(f"  {attr}")
    
    # Check if projects_limit exists as a column
    if hasattr(User, 'projects_limit'):
        print(f"✓ projects_limit attribute exists: {User.projects_limit}")
    else:
        print("✗ projects_limit attribute missing!")
        
    # Check the table columns that SQLAlchemy thinks exist
    print(f"\nTable columns according to SQLAlchemy:")
    for column in User.__table__.columns:
        print(f"  {column.name}: {column.type}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
