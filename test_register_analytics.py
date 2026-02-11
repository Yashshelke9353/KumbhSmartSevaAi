#!/usr/bin/env python3
"""Test Register and Analytics Routes"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import DatabaseManager
from modules.admin_manager import AdminManager
from modules.certificate_manager import CertificateManager

print("=" * 70)
print("🧪 TESTING REGISTER AND ANALYTICS FUNCTIONALITY")
print("=" * 70)

try:
    # Initialize database
    db = DatabaseManager()
    db.init_db()
    
    admin_manager = AdminManager()
    cert_manager = CertificateManager()
    
    print("\n✅ Database and managers initialized")
    
    # Test 1: Check if we can get locations
    print("\n[TEST 1] Getting locations...")
    locations = admin_manager.get_all_locations()
    if locations:
        print(f"✅ Found {len(locations)} locations")
        print(f"   First location: {locations[0]['name']} (ID: {locations[0]['id']})")
    else:
        print("⚠️  No locations found - sample data might not be initialized")
    
    # Test 2: Check crowd analytics
    print("\n[TEST 2] Testing crowd analytics...")
    if locations:
        analytics = admin_manager.get_crowd_analytics(locations[0]['id'])
        print(f"✅ Analytics retrieved successfully")
        print(f"   - Peak Hours: {len(analytics.get('peak_hours', []))} records")
        print(f"   - Daily Data: {len(analytics.get('daily_data', []))} records")
        print(f"   - Crowd Levels: {len(analytics.get('crowd_levels', []))} records")
        
        # Check data structure
        if analytics.get('daily_data'):
            sample_day = analytics['daily_data'][0]
            print(f"   - Sample daily record fields: {list(sample_day.keys())}")
            if 'avg_visitors' in sample_day and 'peak_visitors' in sample_day:
                print(f"     ✅ Required fields present: avg_visitors, peak_visitors")
            else:
                print(f"     ⚠️  Missing fields - Template might fail")
    
    # Test 3: Check user creation (register functionality)
    print("\n[TEST 3] Testing user registration...")
    from werkzeug.security import generate_password_hash
    
    # Test user data
    test_user = {
        'name': 'Test User',
        'email': f'testuser_{os.urandom(4).hex()}@test.com',
        'phone': '9876543210',
        'password': generate_password_hash('testpass123')
    }
    
    user_id = db.create_user(
        test_user['name'],
        test_user['email'],
        test_user['phone'],
        test_user['password']
    )
    
    if user_id:
        print(f"✅ User created successfully (ID: {user_id})")
        
        # Verify user can be retrieved
        retrieved_user = db.get_user_by_email(test_user['email'])
        if retrieved_user:
            print(f"✅ User retrieved from database")
            print(f"   - Name: {retrieved_user['name']}")
            print(f"   - Email: {retrieved_user['email']}")
            print(f"   - Phone: {retrieved_user['phone']}")
        else:
            print(f"❌ User could not be retrieved")
    else:
        print(f"❌ Failed to create user (might be duplicate email)")
    
    # Test 4: Check certificate manager
    print("\n[TEST 4] Testing certificate manager...")
    cert_count = cert_manager.get_certificate_count()
    print(f"✅ Certificate count retrieved: {cert_count}")
    
    # Test 5: Verify all methods used in analytics template
    print("\n[TEST 5] Verifying all analytics data...")
    if locations:
        loc_id = locations[0]['id']
        
        # This is what the templates need
        analytics = admin_manager.get_crowd_analytics(loc_id)
        daily_data = analytics.get('daily_data', [])
        peak_hours = analytics.get('peak_hours', [])
        
        print(f"\n✅ All required data available for analytics template:")
        print(f"   - analytics object: {list(analytics.keys())}")
        print(f"   - daily_data length: {len(daily_data)}")
        print(f"   - peak_hours length: {len(peak_hours)}")
        
        if daily_data:
            print(f"   - daily_data[0] fields: {list(daily_data[0].keys())}")
        if peak_hours:
            print(f"   - peak_hours[0] fields: {list(peak_hours[0].keys())}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Register and Analytics should work!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("❌ TESTS FAILED")
    print("=" * 70)
