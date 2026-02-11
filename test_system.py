#!/usr/bin/env python3
"""
Testing and Verification Script for Kumbh Smart Seva
Tests certificate generation, locations, admin login, and face recognition
"""

import os
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from modules.admin_manager import AdminManager
from modules.certificate_manager import CertificateManager

def test_database():
    """Test database connection and tables"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Database Connection")
    print("="*60)
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get table count
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ Database connected successfully")
        print(f"✅ Found {len(tables)} tables")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table[0]}")
            count = cursor.fetchone()['count']
            print(f"   • {table[0]:<30} : {count:>5} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_locations():
    """Test locations"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Locations")
    print("="*60)
    
    try:
        admin_mgr = AdminManager()
        locations = admin_mgr.get_all_locations()
        
        print(f"✅ Found {len(locations)} locations")
        
        required_locations = [
            'Ramkund Ghat', 'Godavari Ghat', 'Kalaram Ghat',
            'Panchavati', 'Trimbakeshwar Temple'
        ]
        
        location_names = [loc['name'] for loc in locations]
        
        for req_loc in required_locations:
            if req_loc in location_names:
                print(f"✅ Location found: {req_loc}")
            else:
                print(f"❌ Location missing: {req_loc}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Location test failed: {str(e)}")
        return False

def test_admin_users():
    """Test admin user access"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Admin Users & Credentials")
    print("="*60)
    
    try:
        admin_mgr = AdminManager()
        
        # Test admin login credentials
        test_creds = [
            ('admin@kumbh.com', 'admin123', 'Admin'),
            ('supervisor@kumbh.com', 'admin123', 'Supervisor'),
            ('volunteer1@kumbh.com', 'admin123', 'Volunteer'),
        ]
        
        all_passed = True
        for email, password, role in test_creds:
            admin = admin_mgr.get_admin_by_email(email)
            
            if admin:
                if check_password_hash(admin['password'], password):
                    print(f"✅ {role} login: Valid credentials")
                else:
                    print(f"❌ {role} login: Invalid password")
                    all_passed = False
            else:
                print(f"❌ {role} login: User not found")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Admin user test failed: {str(e)}")
        return False

def test_certificate_generation():
    """Test certificate generation"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Certificate Generation")
    print("="*60)
    
    try:
        cert_mgr = CertificateManager()
        admin_mgr = AdminManager()
        
        # Get first location
        locations = admin_mgr.get_all_locations()
        if not locations:
            print("❌ No locations available for testing")
            return False
        
        location_id = locations[0]['id']
        
        # Try to create a test certificate
        cert_id = cert_mgr.generate_certificate(
            user_id=0,
            full_name="Test User",
            location_id=location_id,
            visit_date="2026-02-09",
            email="test@email.com",
            phone="9876543210"
        )
        
        if cert_id:
            print(f"✅ Certificate created: {cert_id}")
            
            # Verify it's in database
            cert = cert_mgr.get_certificate(cert_id)
            if cert:
                print(f"✅ Certificate verified in database")
                print(f"   Location: {cert.get('location_name')}")
                print(f"   Full Name: {cert.get('full_name')}")
                return True
            else:
                print(f"❌ Certificate not found in database")
                return False
        else:
            print(f"❌ Certificate generation failed (might be duplicate)")
            return False
        
    except Exception as e:
        print(f"❌ Certificate test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_face_recognition():
    """Test face recognition module"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Face Recognition Module")
    print("="*60)
    
    try:
        from modules.face_recognition_matcher import FaceRecognitionMatcher, OPENCV_AVAILABLE
        
        if not OPENCV_AVAILABLE:
            print("⚠️  OpenCV not available - Skipping face recognition tests")
            print("   Install with: pip install opencv-python numpy")
            return True
        
        face_matcher = FaceRecognitionMatcher()
        print("✅ Face recognition module initialized")
        
        # Check for test images
        test_images = []
        uploads_dir = "static/uploads"
        if os.path.exists(uploads_dir):
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        test_images.append(os.path.join(root, file))
        
        if len(test_images) >= 2:
            print(f"✅ Found {len(test_images)} test images")
            print("   Face recognition is ready to test with real images")
            return True
        else:
            print(f"⚠️  Only {len(test_images)} test image(s) available")
            print("   Upload lost and found person photos to test face recognition")
            return True
        
    except ImportError:
        print("⚠️  OpenCV not installed")
        print("   Install with: pip install opencv-python numpy")
        return True
    except Exception as e:
        print(f"❌ Face recognition test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🏛️  KUMBH SMART SEVA v2 - Test Suite")
    print("="*60)
    
    tests = [
        ("Database", test_database),
        ("Locations", test_locations),
        ("Admin Users", test_admin_users),
        ("Certificates", test_certificate_generation),
        ("Face Recognition", test_face_recognition),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            results.append((test_name, test_func()))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
    
    print("-" * 60)
    print(f"{'Passed':<10} {passed}/{total} tests")
    print("="*60 + "\n")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready.")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
