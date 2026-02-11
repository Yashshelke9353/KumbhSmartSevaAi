#!/usr/bin/env python3
"""Diagnose face matching similarity scores across different scenarios"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from modules.face_recognition_matcher import FaceRecognitionMatcher
from pathlib import Path

print("=" * 70)
print("🧬 FACE MATCHER SIMILARITY DIAGNOSIS")
print("=" * 70)

# Initialize matcher
matcher = FaceRecognitionMatcher()

# Find all images in uploads
upload_dir = "static/uploads"
lost_images = list(Path(upload_dir).glob("lost_*.jpg"))
found_images = list(Path(upload_dir).glob("found_*.jpg"))

print(f"\n📸 Available test images:")
print(f"   Lost: {len(lost_images)}")
print(f"   Found: {len(found_images)}")

if not lost_images or not found_images:
    print("\n❌ Not enough images for testing!")
    sys.exit(1)

# Test same image matching (should be high)
print("\n" + "=" * 70)
print("TEST 1: SAME IMAGE (should be 100%)")
print("=" * 70)

test_img = str(lost_images[0])
matches = matcher.find_matches(test_img, [(1, test_img)], threshold=0)
if matches:
    print(f"✅ Same image similarity: {matches[0]['similarity']}%")
else:
    print(f"⚠️ No match found for same image!")

# Test all lost vs all found
print("\n" + "=" * 70)
print("TEST 2: ALL LOST vs ALL FOUND (cross-matching)")
print("=" * 70)

all_matches = []
for lost_idx, lost_img in enumerate(lost_images, 1):
    found_pairs = [(idx, str(img)) for idx, img in enumerate(found_images, 1)]
    matches = matcher.find_matches(str(lost_img), found_pairs, threshold=0)
    
    if matches:
        for match in matches:
            all_matches.append({
                'lost': lost_idx,
                'found': match['found_id'],
                'similarity': match['similarity']
            })

# Display results
if all_matches:
    print(f"\n📊 Found {len(all_matches)} matches (threshold: 0%):")
    print("\n   Lost# → Found#: Similarity")
    print("   " + "-" * 35)
    
    max_sim = 0
    for match in all_matches:
        print(f"   {match['lost']:2d}   →   {match['found']:2d}   : {match['similarity']:6.1f}%")
        max_sim = max(max_sim, match['similarity'])
    
    print("\n📈 Statistics:")
    print(f"   Maximum similarity: {max_sim:.1f}%")
    print(f"   Average similarity: {sum(m['similarity'] for m in all_matches) / len(all_matches):.1f}%")
    print(f"   Min for match 40%: {len([m for m in all_matches if m['similarity'] >= 40])}")
    print(f"   Min for match 30%: {len([m for m in all_matches if m['similarity'] >= 30])}")
    print(f"   Min for match 20%: {len([m for m in all_matches if m['similarity'] >= 20])}")
    print(f"   Min for match 10%: {len([m for m in all_matches if m['similarity'] >= 10])}")
else:
    print("⚠️ No cross-matches found at 0% threshold!")

# Recommendations
print("\n" + "=" * 70)
print("📋 RECOMMENDATIONS")
print("=" * 70)

if all_matches:
    max_sim = max(m['similarity'] for m in all_matches)
    if max_sim < 50:
        print(f"""
⚠️ Maximum similarity is only {max_sim:.1f}%

Possible causes:
1. Photos are of DIFFERENT PEOPLE (expected behavior)
2. Algorithm is too strict for similar faces
3. Image quality/angle differences too large

Solutions:
1. Lower the threshold from 40% to 20-30%
2. Use photos of the SAME PERSON for testing
3. Ensure photos are clear face shots

Suggested settings:
- If photos are CLEARLY of same person: 20-30% threshold
- If photos might be same person: 10-20% threshold
- Current 40% threshold: Only for near-perfect matches
""")
    else:
        print(f"""
✅ Maximum similarity is {max_sim:.1f}%

Recommendations:
1. Try lowering threshold to 30-35%
2. Or default 40% is reasonable if strictly same person
3. Check if test images are actually same/similar people
""")
else:
    print("""
⚠️ No matches found at all!

Check:
1. Are images being loaded correctly?
2. Are faces being detected?
3. Are feature extraction working?
4. Check console output for errors
""")

print("\n" + "=" * 70)
