#!/usr/bin/env python3
"""Quick test to verify location status data display"""
import sqlite3
import database

db_path = database.DB_PATH

def test_location_status():
    """Test the location status query"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Run the updated query
    cursor.execute('''
        SELECT DISTINCT l.id, l.name, l.capacity,
        COALESCE((SELECT visitor_count FROM crowd_data 
         WHERE location_id = l.id 
         ORDER BY timestamp DESC LIMIT 1), 
         (SELECT COUNT(*) FROM visitor_certificates WHERE location_id = l.id)) as current_visitors,
        COALESCE((SELECT crowd_level FROM crowd_data 
         WHERE location_id = l.id 
         ORDER BY timestamp DESC LIMIT 1), 'normal') as crowd_level
        FROM locations l
        ORDER BY l.name
    ''')
    
    locations = cursor.fetchall()
    conn.close()
    
    print("\n✓ Location Status Report:")
    print("=" * 80)
    
    if not locations:
        print("No locations found in database.")
        return
    
    for loc in locations:
        loc_dict = dict(loc)
        print(f"\nLocation: {loc_dict['name']}")
        print(f"  ID: {loc_dict['id']}")
        print(f"  Capacity: {loc_dict['capacity']}")
        print(f"  Current Visitors: {loc_dict['current_visitors'] or 0}")
        print(f"  Crowd Level: {loc_dict['crowd_level']}")
    
    print("\n" + "=" * 80)
    print(f"✓ Total locations: {len(locations)}")

if __name__ == '__main__':
    test_location_status()
