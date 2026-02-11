#!/usr/bin/env python3
"""
Debug script to test face matcher
"""

import os
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.face_recognition_matcher import FaceRecognitionMatcher, OPENCV_AVAILABLE

def main():
    print("\n" + "="*60)
    print("🔍 FACE MATCHER DEBUG TEST")
    print("="*60)
    
    # Check OpenCV
    if not OPENCV_AVAILABLE:
        print("❌ OpenCV not available!")
        print("   Install: pip install opencv-python numpy")
        return False
    
    print("✅ OpenCV is available")
    
    # Initialize matcher
    try:
        matcher = FaceRecognitionMatcher()
        print("✅ Face matcher initialized")
    except Exception as e:
        print(f"❌ Error initializing matcher: {e}")
        return False
    
    # Find test images
    uploads_dir = "static/uploads"
    lost_images = []
    found_images = []
    
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, file)
            if file.lower().startswith('lost_'):
                lost_images.append(filepath)
            elif file.lower().startswith('found_'):
                found_images.append(filepath)
    
    print(f"\n📸 Found Images:")
    print(f"   Lost persons: {len(lost_images)}")
    for img in lost_images:
        print(f"      • {img}")
    print(f"   Found persons: {len(found_images)}")
    for img in found_images:
        print(f"      • {img}")
    
    if len(lost_images) == 0 or len(found_images) == 0:
        print("\n⚠️  Need at least one lost and one found image to test")
        return False
    
    # Test face detection
    print(f"\n🎯 Testing Face Detection:")
    for lost_img in lost_images[:1]:
        print(f"   Testing: {lost_img}")
        face, img = matcher.detect_face(lost_img)
        if face is not None:
            print(f"   ✅ Face detected! Size: {face.shape}")
        else:
            print(f"   ❌ No face detected")
    
    # Test feature extraction
    print(f"\n🔑 Testing Feature Extraction:")
    for lost_img in lost_images[:1]:
        face, _ = matcher.detect_face(lost_img)
        if face is not None:
            kp, desc = matcher.extract_features(face)
            if desc is not None:
                print(f"   ✅ Features extracted! Count: {len(desc)}")
            else:
                print(f"   ❌ No features extracted")
    
    # Test matching
    print(f"\n🔗 Testing Face Matching:")
    if len(lost_images) > 0 and len(found_images) > 0:
        lost_img = lost_images[0]
        found_img = found_images[0]
        
        print(f"   Lost: {lost_img}")
        print(f"   Found: {found_img}")
        
        matches = matcher.find_matches(lost_img, [(1, found_img)], threshold=0)
        
        if matches:
            print(f"   ✅ Match found! Similarity: {matches[0]['similarity']}%")
        else:
            print(f"   ❌ No matches found")
            print("   This is normal if faces are different")
    
    print("\n" + "="*60)
    print("Debug test complete!")
    print("="*60 + "\n")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
