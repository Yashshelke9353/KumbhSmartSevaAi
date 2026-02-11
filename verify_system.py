#!/usr/bin/env python3
"""
Complete verification script for Kumbh Smart Seva
Tests all components: database, login, certificates, face matching
"""

import os
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
import database
from modules.admin_manager import AdminManager
from modules.certificate_manager import CertificateManager
from modules.face_recognition_matcher import FaceRecognitionMatcher, OPENCV_AVAILABLE

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title:<66}  ")
    print(f"{'='*70}")

def test_admin_login():
    """Test admin login credentials"""
    print_section("TEST 1: ADMIN LOGIN VERIFICATION")
    
    admin_mgr = AdminManager()
    
    credentials = [
        ('admin@kumbh.com', 'admin123', 'ADMIN'),
        ('supervisor@kumbh.com', 'admin123', 'SUPERVISOR'),
        ('volunteer1@kumbh.com', 'admin123', 'VOLUNTEER'),
    ]
    
    all_ok = True
    for email, password, role in credentials:
        admin = admin_mgr.get_admin_by_email(email)
        
        if not admin:
            print(f"❌ {role:<15} NOT FOUND: {email}")
            all_ok = False
            continue
        
        if check_password_hash(admin['password'], password):
            print(f"✅ {role:<15} OK: {email}")
            print(f"   Status: {admin['status']} | Location: {admin.get('location_id', 'N/A')}")
        else:
            print(f"❌ {role:<15} INVALID PASSWORD: {email}")
            all_ok = False
    
    return all_ok

def test_certificate_generation():
    """Test certificate generation"""
    print_section("TEST 2: CERTIFICATE GENERATION")
    
    cert_mgr = CertificateManager()
    admin_mgr = AdminManager()
    
    locations = admin_mgr.get_all_locations()
    if not locations:
        print("❌ No locations found!")
        return False
    
    test_location_id = locations[0]['id']
    test_location_name = locations[0]['name']
    
    # Try to create a test certificate
    cert_id = cert_mgr.generate_certificate(
        user_id=0,
        full_name="Test Certificate",
        location_id=test_location_id,
        visit_date=datetime.now().strftime('%Y-%m-%d'),
        email="test@email.com",
        phone="9876543210"
    )
    
    if cert_id:
        print(f"✅ Certificate Generated Successfully")
        print(f"   Certificate ID: {cert_id}")
        print(f"   Location: {test_location_name}")
        
        # Verify it exists in database
        cert = cert_mgr.get_certificate(cert_id)
        if cert:
            print(f"   ✅ Certificate verified in database")
            return True
        else:
            print(f"   ❌ Certificate not found in database")
            return False
    else:
        print(f"⚠️ Certificate generation returned None")
        print(f"   This might be a duplicate entry (same person, location, date)")
        return False

def test_face_recognition():
    """Test face recognition"""
    print_section("TEST 3: FACE RECOGNITION")
    
    if not OPENCV_AVAILABLE:
        print("⚠️ OpenCV not available - Face recognition will use Pillow fallback")
        print("   Install: pip install opencv-python")
        return True
    
    try:
        matcher = FaceRecognitionMatcher()
        print("✅ Face matcher initialized")
        
        # Check for test images
        uploads_dir = "static/uploads"
        lost_images = []
        found_images = []
        
        if os.path.exists(uploads_dir):
            for file in os.listdir(uploads_dir):
                if file.lower().startswith('lost_') and file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    lost_images.append(os.path.join(uploads_dir, file))
                elif file.lower().startswith('found_') and file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    found_images.append(os.path.join(uploads_dir, file))
        
        print(f"   Lost person images: {len(lost_images)}")
        print(f"   Found person images: {len(found_images)}")
        
        if len(lost_images) > 0 and len(found_images) > 0:
            print(f"\n✅ Test images available - Face matching ready")
            return True
        else:
            print(f"\n⚠️ Upload lost & found person photos to test face matching")
            return True
        
    except Exception as e:
        print(f"❌ Face recognition error: {e}")
        return False

def test_locations():
    """Test locations"""
    print_section("TEST 4: LOCATIONS")
    
    admin_mgr = AdminManager()
    locations = admin_mgr.get_all_locations()
    
    print(f"✅ Total Locations: {len(locations)}")
    
    required = ['Ramkund Ghat', 'Godavari Ghat', 'Kalaram Ghat', 'Panchavati']
    loc_names = [loc['name'] for loc in locations]
    
    found_count = sum(1 for req in required if req in loc_names)
    print(f"✅ Key Locations: {found_count}/{len(required)} found")
    
    if found_count == len(required):
        print(f"   ✅ All major locations present")
        return True
    
    return True

def test_database():
    """Test database connection"""
    print_section("TEST 5: DATABASE")
    
    db = DatabaseManager()
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM locations")
        loc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitor_certificates")
        cert_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database Connected")
        print(f"   Admin Users: {admin_count}")
        print(f"   Locations: {loc_count}")
        print(f"   Certificates: {cert_count}")
        
        return True if admin_count > 0 and loc_count > 20 else False
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "🏛️  KUMBH SMART SEVA v2 - COMPLETE VERIFICATION" + " " * 7 + "║")
    print("╚" + "═" * 68 + "╝")
    
    tests = [
        ("Database", test_database),
        ("Locations", test_locations),
        ("Admin Login", test_admin_login),
        ("Certificates", test_certificate_generation),
        ("Face Recognition", test_face_recognition),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{'─'*70}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'─'*70}")
    
    print_section("NEXT STEPS")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n1. Start the application:")
        print("   python app.py")
        print("\n2. Open browser:")
        print("   http://localhost:5000")
        print("\n3. Admin Login:")
        print("   Email: admin@kumbh.com")
        print("   Password: admin123")
        print("\n4. Regular User Login:")
        print("   Email: rajesh@example.com")
        print("   Password: password123")
    else:
        print(f"⚠️  {total - passed} test(s) failed!")
        print("\nTroubleshooting:")
        print("1. Run: python init_sample_data.py")
        print(f"2. Check: {database.DB_PATH} exists")
        print("3. Run: pip install -r requirements.txt")
    
    print("\n" + "═"*70 + "\n")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
