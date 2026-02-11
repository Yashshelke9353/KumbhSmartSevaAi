#!/usr/bin/env python3
"""
Complete setup script for Kumbh Smart Seva v2
Initializes database with all locations and sample data
"""

import sqlite3
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from modules.admin_manager import AdminManager

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🏛️  KUMBH SMART SEVA v2 - Complete Setup Script")
    print("="*60)
    
    try:
        # Step 1: Initialize database
        print("\n📊 Step 1: Initializing database...")
        db = DatabaseManager()
        db.init_db()
        print("✅ Database initialized successfully!")
        
        # Step 2: Verify locations were created
        print("\n📍 Step 2: Verifying locations...")
        admin_mgr = AdminManager()
        locations = admin_mgr.get_all_locations()
        print(f"✅ Found {len(locations)} locations in database")
        
        if len(locations) < 20:
            print("⚠️  Warning: Expected at least 24 locations")
            print("    Make sure to run: python init_sample_data.py")
        
        # Print location list
        print("\n📍 Current Locations:")
        print("-" * 60)
        for loc in sorted(locations, key=lambda x: x['name']):
            print(f"  • {loc['name']:<40} (Cap: {loc['capacity']})")
        print("-" * 60)
        
        # Step 3: Verify admin users
        print("\n👥 Step 3: Verifying admin users...")
        admins = admin_mgr.get_all_admins()
        print(f"✅ Found {len(admins)} admin users")
        
        if len(admins) > 0:
            print("\n👤 Admin Users:")
            print("-" * 60)
            for admin in admins:
                print(f"  Name: {admin['name']}")
                print(f"  Email: {admin['email']}")
                print(f"  Role: {admin['role']}")
                print(f"  Status: {admin['status']}")
                print()
        
        # Step 4: Test credentials
        print("\n🔐 Step 4: Test Credentials")
        print("-" * 60)
        print("\n✅ Regular User Login:")
        print("  Email: rajesh@example.com")
        print("  Password: password123")
        print("\n✅ Admin Login:")
        print("  Email: admin@kumbh.com")
        print("  Password: admin123")
        print("\n✅ Supervisor Login:")
        print("  Email: supervisor@kumbh.com")
        print("  Password: admin123")
        print("-" * 60)
        
        # Step 5: Location-specific admins
        print("\n🏘️  Step 5: Location-assigned Admins")
        print("-" * 60)
        for admin in admins:
            if admin.get('location_id'):
                location = admin_mgr.get_location(admin['location_id'])
                if location:
                    print(f"  {admin['name']:<25} -> {location['name']}")
        print("-" * 60)
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("\n📝 Next Steps:")
        print("1. Run: python init_sample_data.py")
        print("   (to insert sample certificate and crowd data)")
        print("\n2. Start the application: python app.py")
        print("\n3. Open browser: http://localhost:5000")
        print("\n" + "="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
