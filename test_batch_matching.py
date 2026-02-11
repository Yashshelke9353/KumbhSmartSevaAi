#!/usr/bin/env python3
"""Test face matching with actual database records"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from modules.face_recognition_matcher import FaceRecognitionMatcher
from modules.lost_person import LostPersonRegistry

print("=" * 70)
print("🔍 FACE MATCHING WITH DATABASE RECORDS")
print("=" * 70)

# Initialize
matcher = FaceRecognitionMatcher()
registry = LostPersonRegistry()

# Get records from database
lost_persons = registry.get_all_reports(status='lost')
found_persons = registry.get_found_persons(status='unclaimed')

print(f"\n📊 Database Data:")
print(f"   Lost persons (status='lost'): {len(lost_persons)}")
print(f"   Found persons (status='unclaimed'): {len(found_persons)}")

# Show records
print(f"\n📋 Lost Persons:")
for lp in lost_persons:
    print(f"   ID: {lp['id']}, Photo: {lp.get('photo_path', 'N/A')}")

print(f"\n📋 Found Persons:")
for fp in found_persons:
    print(f"   ID: {fp['id']}, Photo: {fp.get('photo_path', 'N/A')}")

# Test batch matching
print("\n" + "=" * 70)
print("🧬 RUNNING BATCH FACE MATCHING (threshold: 40%)")
print("=" * 70)

results = matcher.batch_match_all(lost_persons, found_persons, threshold=40)

print(f"\n📊 RESULTS:")
print(f"   Lost persons with matches: {len(results)}")
print(f"   Total matches found: {sum(len(matches) for matches in results.values())}")

if results:
    print(f"\n✅ MATCHES FOUND:")
    for lost_id, matches in results.items():
        print(f"\n   Lost ID {lost_id}:")
        for match in matches:
            print(f"      → Found ID {match['found_id']}: {match['similarity']}%")
else:
    print(f"\n⚠️ NO MATCHES FOUND AT 40% THRESHOLD")
    
    # Try with lower threshold
    print(f"\nTrying with 20% threshold...")
    results_20 = matcher.batch_match_all(lost_persons, found_persons, threshold=20)
    
    if results_20:
        print(f"✅ Found {sum(len(m) for m in results_20.values())} matches at 20%:")
        for lost_id, matches in results_20.items():
            print(f"\n   Lost ID {lost_id}:")
            for match in matches:
                print(f"      → Found ID {match['found_id']}: {match['similarity']}%")
    else:
        print(f"⚠️ NO MATCHES EVEN AT 20% THRESHOLD")
        print(f"\nDiagnosis:")
        print(f"- Check if photos exis on disk")
        print(f"- Verify face detection is working")
        print(f"- Check image quality/format")

print("\n" + "=" * 70)
