#!/usr/bin/env python3
"""Check database for lost and found person records"""

import sqlite3
import os
from pathlib import Path
import database

print("=" * 70)
print("🔍 DATABASE RECORDS CHECK")
print("=" * 70)

db_path = database.DB_PATH

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check lost persons table
print("\n📋 LOST PERSONS TABLE:")
print("=" * 70)

cursor.execute('''
    SELECT * FROM lost_persons LIMIT 20
''')

lost_rows = cursor.fetchall()
print(f"Total lost person records: ", end="")
cursor.execute("SELECT COUNT(*) FROM lost_persons")
total = cursor.fetchone()[0]
print(total)

if lost_rows:
    print("\nShowing first 5 records:")
    for i, row in enumerate(lost_rows[:5], 1):
        row_dict = dict(row)
        print(f"\n{i}. ID: {row_dict['id']}")
        print(f"   Name: {row_dict.get('full_name', 'N/A')}")
        print(f"   Photo: {row_dict.get('photo_path', 'N/A')}")
        print(f"   Status: {row_dict.get('status', 'N/A')}")
        print(f"   Created: {row_dict.get('created_at', 'N/A')}")
        
        # Check if photo exists
        if row_dict.get('photo_path'):
            photo_path = f"static/uploads/{row_dict['photo_path']}"
            exists = os.path.exists(photo_path)
            print(f"   Photo exists: {'✅ YES' if exists else '❌ NO'}")
else:
    print("⚠️ No lost person records in database!")

# Check found persons table
print("\n\n📋 FOUND PERSONS TABLE:")
print("=" * 70)

cursor.execute('''
    SELECT * FROM found_persons LIMIT 20
''')

found_rows = cursor.fetchall()
print(f"Total found person records: ", end="")
cursor.execute("SELECT COUNT(*) FROM found_persons")
total = cursor.fetchone()[0]
print(total)

if found_rows:
    print("\nShowing first 5 records:")
    for i, row in enumerate(found_rows[:5], 1):
        row_dict = dict(row)
        print(f"\n{i}. ID: {row_dict['id']}")
        print(f"   Name: {row_dict.get('full_name', 'N/A')}")
        print(f"   Photo: {row_dict.get('photo_path', 'N/A')}")
        print(f"   Status: {row_dict.get('status', 'N/A')}")
        print(f"   Created: {row_dict.get('created_at', 'N/A')}")
        
        # Check if photo exists
        if row_dict.get('photo_path'):
            photo_path = f"static/uploads/{row_dict['photo_path']}"
            exists = os.path.exists(photo_path)
            print(f"   Photo exists: {'✅ YES' if exists else '❌ NO'}")
else:
    print("⚠️ No found person records in database!")

# Summary
print("\n\n📊 SUMMARY:")
print("=" * 70)

cursor.execute("SELECT COUNT(*) FROM lost_persons WHERE photo_path IS NOT NULL AND photo_path != ''")
lost_with_photos = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM found_persons WHERE photo_path IS NOT NULL AND photo_path != ''")
found_with_photos = cursor.fetchone()[0]

print(f"Lost persons with photos: {lost_with_photos}")
print(f"Found persons with photos: {found_with_photos}")

if lost_with_photos == 0 and found_with_photos == 0:
    print("""
❌ PROBLEM IDENTIFIED:
   No lost or found person records in database!
   
SOLUTION:
   1. Go to: http://localhost:5000/report-lost-person
   2. Fill in form and upload a lost person photo
   3. Go to: http://localhost:5000/report-found-person
   4. Fill in form and upload a found person photo
   5. Go to: http://localhost:5000/face-match
   6. Click "Run Face Matching"
""")
elif lost_with_photos == 0:
    print("""
⚠️ No lost persons with photos!
   You need to create lost person reports with photos.
""")
elif found_with_photos == 0:
    print("""
⚠️ No found persons with photos!
   You need to create found person reports with photos.
""")
else:
    print(f"""
✅ Data looks good! 
   {lost_with_photos} lost persons and {found_with_photos} found persons with photos
   
Face matching should work. Try running:
   http://localhost:5000/face-match

If still no matches:
   1. Check if threshold is set correctly (default 40%)
   2. People must have similar faces to match
   3. Try lowering threshold to 20-30%
""")

conn.close()

print("\n" + "=" * 70)
