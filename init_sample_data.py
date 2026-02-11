#!/usr/bin/env python3
"""
Sample Data Initializer for Kumbh Smart Seva
Populates database with test data for demonstration
"""

import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

DB_PATH = 'database/main.db'

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clear_data():
    """Clear all test data (careful!)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = [
        'visitor_certificates', 'crowd_data', 'volunteer_assignments',
        'alerts', 'lost_persons', 'found_persons', 'locker_items',
        'admin_users', 'users', 'locations'
    ]
    
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')
    
    conn.commit()
    conn.close()
    print("✓ Cleared all data")

def insert_sample_locations():
    """Insert sample Nashik/Kumbh locations"""
    conn = get_connection()
    cursor = conn.cursor()
    
    locations = [
        ('Ramkund Ghat', 19.8974, 73.7898, 8000),
        ('Godavari Ghat', 19.8970, 73.7890, 7000),
        ('Kalaram Ghat', 19.8968, 73.7885, 6000),
        ('Panchavati', 19.9089, 73.7960, 5000),
        ('Trimbakeshwar Temple', 19.8893, 73.7845, 4000),
        ('Kalaram Mandir', 19.8975, 73.7900, 5500),
        ('Sita Gufa', 19.8980, 73.7910, 3000),
        ('Kapaleshwar Temple', 19.8970, 73.7895, 4500),
        ('Someshwar Temple', 19.8965, 73.7880, 3500),
        ('Pandavleni Caves', 19.9145, 73.8120, 2500),
        ('Coin Museum', 19.8950, 73.7950, 1500),
        ('Gargoti Museum', 19.8940, 73.7940, 1500),
        ('Anjaneri Hills', 19.9200, 73.8150, 2000),
        ('Saptashrungi Temple', 19.9250, 73.8200, 3000),
        ('Dudhsagar Falls', 19.8800, 73.8300, 2000),
        ('Gangapur Dam', 19.8750, 73.7850, 1000),
        ('Harihar Fort', 19.8700, 73.7800, 1500),
        ('Brahmagiri Hills', 19.8600, 73.7750, 2500),
        ('Nandur Madhmeshwar Bird Sanctuary', 19.8550, 73.7700, 800),
        ('Main Road Nashik', 19.8950, 73.7850, 5000),
        ('Saraf Bazar', 19.8960, 73.7860, 4000),
        ('College Road', 19.8940, 73.7920, 3500),
        ('Panchavati Market', 19.9090, 73.7960, 4500),
        ('Other', 19.8950, 73.7900, 5000),
    ]
    
    for name, lat, lng, capacity in locations:
        try:
            cursor.execute(
                'INSERT INTO locations (name, latitude, longitude, capacity) VALUES (?, ?, ?, ?)',
                (name, lat, lng, capacity)
            )
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("✓ Inserted 24 Nashik/Kumbh locations")

def insert_sample_users():
    """Insert sample visitor users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    users = [
        ('Rajesh Kumar', 'rajesh@example.com', '9876543210', 'password123'),
        ('Priya Singh', 'priya@example.com', '9876543211', 'password123'),
        ('Amit Patel', 'amit@example.com', '9876543212', 'password123'),
        ('Seema Sharma', 'seema@example.com', '9876543213', 'password123'),
        ('Vikram Yadav', 'vikram@example.com', '9876543214', 'password123'),
    ]
    
    for name, email, phone, password in users:
        hashed = generate_password_hash(password)
        try:
            cursor.execute(
                'INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)',
                (name, email, phone, hashed)
            )
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("✓ Inserted 5 sample visitor users")

def insert_sample_admins():
    """Insert sample admin/volunteer users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    admins = [
        ('Admin User', 'admin@kumbh.com', '9999999999', 'admin123', 'admin', None),
        ('Sharma Supervisor', 'supervisor@kumbh.com', '9999999998', 'admin123', 'supervisor', 1),
        ('Volunteer Raj', 'volunteer1@kumbh.com', '9999999997', 'admin123', 'volunteer', 1),
        ('Volunteer Priya', 'volunteer2@kumbh.com', '9999999996', 'admin123', 'volunteer', 2),
        ('Volunteer Arjun', 'volunteer3@kumbh.com', '9999999995', 'admin123', 'volunteer', 3),
    ]
    
    for name, email, phone, password, role, location_id in admins:
        hashed = generate_password_hash(password)
        try:
            cursor.execute('''
                INSERT INTO admin_users (name, email, phone, password, role, location_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (name, email, phone, hashed, role, location_id))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("✓ Inserted 5 sample admin/volunteer users")

def insert_sample_certificates():
    """Insert sample certificates"""
    conn = get_connection()
    cursor = conn.cursor()
    
    names = [
        'Rajesh Kumar', 'Priya Singh', 'Amit Patel', 'Seema Sharma',
        'Vikram Yadav', 'Neha Verma', 'Suresh Gupta', 'Anjali Sharma'
    ]
    
    location_ids = list(range(1, 25))  # IDs 1-24 for all locations
    
    # Generate certificates for past 30 days
    for i, name in enumerate(names):
        cert_id = f"CERT{1000 + i}"
        location_id = location_ids[i % len(location_ids)]
        visit_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                INSERT INTO visitor_certificates 
                (certificate_id, user_id, full_name, location_id, visit_date, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (cert_id, 1, name, location_id, visit_date, f'{name.lower().replace(" ", ".")}@email.com', f'981234567{i}'))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print("✓ Inserted 8 sample certificates")

def insert_sample_crowd_data():
    """Insert sample crowd monitoring data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use first 5 locations for crowd data
    location_ids = [1, 2, 3, 4, 5]
    crowd_levels = ['normal', 'medium', 'high']
    
    # Insert data for past 24 hours
    for location_id in location_ids:
        for hour in range(24):
            timestamp = (datetime.now() - timedelta(hours=24-hour)).isoformat()
            visitor_count = random.randint(100, 5000)
            crowd_level = 'high' if visitor_count > 3000 else 'medium' if visitor_count > 1500 else 'normal'
            
            cursor.execute('''
                INSERT INTO crowd_data (location_id, timestamp, visitor_count, crowd_level)
                VALUES (?, ?, ?, ?)
            ''', (location_id, timestamp, visitor_count, crowd_level))
    
    conn.commit()
    conn.close()
    print("✓ Inserted crowd monitoring data for 24 hours")

def insert_sample_alerts():
    """Insert sample alerts"""
    conn = get_connection()
    cursor = conn.cursor()
    
    alerts = [
        (1, 'crowd_alert', 'High crowd density detected at Ramkund Ghat', 'high', 0),
        (2, 'weather_alert', 'Heavy rainfall expected at Godavari Ghat', 'medium', 0),
        (3, 'facility_alert', 'Medical facility extended hours at Kalaram Ghat', 'low', 0),
        (4, 'security_alert', 'Heightened security during peak hours', 'medium', 0),
        (5, 'maintenance_alert', 'Path closure for maintenance', 'high', 0),
    ]
    
    for location_id, alert_type, message, severity, resolved in alerts:
        cursor.execute('''
            INSERT INTO alerts (location_id, alert_type, message, severity, resolved)
            VALUES (?, ?, ?, ?, ?)
        ''', (location_id, alert_type, message, severity, resolved))
    
    conn.commit()
    conn.close()
    print("✓ Inserted 5 sample alerts")

def insert_sample_assignments():
    """Insert sample volunteer assignments"""
    conn = get_connection()
    cursor = conn.cursor()
    
    assignments = [
        (3, 1, '2026-02-09 06:00', '2026-02-09 14:00'),  # Volunteer Raj at Ganges Ghat
        (4, 2, '2026-02-09 08:00', '2026-02-09 16:00'),  # Volunteer Priya at Yamuna Bank
        (5, 3, '2026-02-09 10:00', '2026-02-09 18:00'),  # Volunteer Arjun at Temple Area
        (3, 1, '2026-02-09 14:00', '2026-02-09 22:00'),  # Volunteer Raj evening shift
    ]
    
    for admin_id, location_id, shift_start, shift_end in assignments:
        cursor.execute('''
            INSERT INTO volunteer_assignments 
            (admin_user_id, location_id, shift_start, shift_end, status)
            VALUES (?, ?, ?, ?, 'assigned')
        ''', (admin_id, location_id, shift_start, shift_end))
    
    conn.commit()
    conn.close()
    print("✓ Inserted volunteer assignments")

def print_statistics():
    """Print summary statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count records
    tables = {
        'Visitor Users': 'users',
        'Admin Users': 'admin_users',
        'Certificates': 'visitor_certificates',
        'Crowd Records': 'crowd_data',
        'Alerts': 'alerts',
        'Assignments': 'volunteer_assignments'
    }
    
    print("\n" + "="*50)
    print("DATABASE STATISTICS")
    print("="*50)
    
    for label, table in tables.items():
        cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
        count = cursor.fetchone()['count']
        print(f"{label:<25} : {count:>5}")
    
    print("="*50 + "\n")
    
    conn.close()

def main():
    """Main initialization function"""
    print("\n🏛️  Kumbh Smart Seva - Sample Data Initializer")
    print("="*50)
    
    try:
        # Initialize
        print("\n📊 Inserting sample data...")
        insert_sample_locations()
        insert_sample_users()
        insert_sample_admins()
        insert_sample_certificates()
        insert_sample_crowd_data()
        insert_sample_alerts()
        insert_sample_assignments()
        
        # Show statistics
        print_statistics()
        
        print("✅ Sample data initialized successfully!")
        print("\n📝 Test Credentials:")
        print("-" * 50)
        print("Visitor Login:")
        print("  Email: rajesh@example.com")
        print("  Password: password123")
        print("\nAdmin Login:")
        print("  Email: admin@kumbh.com")
        print("  Password: admin123")
        print("\nSupervisor Login:")
        print("  Email: supervisor@kumbh.com")
        print("  Password: admin123")
        print("-" * 50 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    main()
