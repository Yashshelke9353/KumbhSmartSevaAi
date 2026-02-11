import sqlite3
from datetime import datetime
import os
from . import DB_PATH


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DB_PATH
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Admin/Staff users table with roles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'volunteer',
                location_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                latitude REAL,
                longitude REAL,
                capacity INTEGER DEFAULT 5000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Visitor certificates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visitor_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                location_id INTEGER NOT NULL,
                visit_date TEXT NOT NULL,
                photo_path TEXT,
                qr_code_path TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (location_id) REFERENCES locations(id)
            )
        ''')
        
        # Crowd data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crowd_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visitor_count INTEGER NOT NULL,
                crowd_level TEXT DEFAULT 'normal',
                peak_hour BOOLEAN DEFAULT 0,
                FOREIGN KEY (location_id) REFERENCES locations(id)
            )
        ''')
        
        # Volunteer assignments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS volunteer_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                shift_start TEXT NOT NULL,
                shift_end TEXT NOT NULL,
                status TEXT DEFAULT 'assigned',
                FOREIGN KEY (admin_user_id) REFERENCES admin_users(id),
                FOREIGN KEY (location_id) REFERENCES locations(id)
            )
        ''')
        
        # Digital locker table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locker_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                doc_type TEXT NOT NULL,
                doc_number TEXT NOT NULL,
                file_path TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Lost persons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lost_persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                description TEXT,
                last_seen_location TEXT,
                contact TEXT NOT NULL,
                photo_path TEXT,
                status TEXT DEFAULT 'lost',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Found persons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS found_persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                photo_path TEXT,
                status TEXT DEFAULT 'unclaimed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Alerts/Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations(id)
            )
        ''')

        # Rooms table for accommodation listings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                price_per_night REAL NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                photo_path TEXT,
                status TEXT DEFAULT 'available',
                num_rooms INTEGER DEFAULT 1,
                water_facility BOOLEAN DEFAULT 0,
                toilet_available BOOLEAN DEFAULT 0,
                bathroom_type TEXT,
                security TEXT,
                amenities TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                visitor_name TEXT NOT NULL,
                visitor_phone TEXT NOT NULL,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                aadhaar_photo_path TEXT,
                status TEXT DEFAULT 'booked',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        ''')

        # Attempt to add columns to existing tables if DB was created earlier
        try:
            cursor.execute("ALTER TABLE rooms ADD COLUMN num_rooms INTEGER DEFAULT 1")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE rooms ADD COLUMN water_facility BOOLEAN DEFAULT 0")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE rooms ADD COLUMN toilet_available BOOLEAN DEFAULT 0")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE rooms ADD COLUMN bathroom_type TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE rooms ADD COLUMN security TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE rooms ADD COLUMN amenities TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE bookings ADD COLUMN aadhaar_photo_path TEXT")
        except Exception:
            pass
        
        # Insert default locations
        self._insert_default_locations(cursor)
        
        conn.commit()
        conn.close()
        print("[OK] Database initialized successfully!")
    
    def _insert_default_locations(self, cursor):
        """Insert default Nashik/Kumbh locations"""
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
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, name, email, phone, password):
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)',
                (name, email, phone, password)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    # ==================== ROOMS & BOOKINGS ====================
    def add_room(self, name, owner_name, phone, address, price_per_night, latitude, longitude, photo_path=None,
                 num_rooms=1, water_facility=0, toilet_available=0, bathroom_type=None, security=None, amenities=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO rooms (name, owner_name, phone, address, price_per_night, latitude, longitude, photo_path, num_rooms, water_facility, toilet_available, bathroom_type, security, amenities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, owner_name, phone, address, price_per_night, latitude, longitude, photo_path, num_rooms, water_facility, toilet_available, bathroom_type, security, amenities))
        room_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return room_id

    def get_room(self, room_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def search_rooms(self, min_price=None, max_price=None, include_booked=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        params = []
        where_clauses = []

        if not include_booked:
            where_clauses.append('status = "available"')

        if min_price is not None:
            where_clauses.append('price_per_night >= ?')
            params.append(min_price)

        if max_price is not None:
            where_clauses.append('price_per_night <= ?')
            params.append(max_price)

        where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
        sql = f'SELECT * FROM rooms {where_sql}'
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_booking(self, room_id, visitor_name, visitor_phone, check_in, check_out, aadhaar_photo_path=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (room_id, visitor_name, visitor_phone, check_in, check_out, aadhaar_photo_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (room_id, visitor_name, visitor_phone, check_in, check_out, aadhaar_photo_path))
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return booking_id

    def bookings_for_room(self, room_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE room_id = ? AND status = "booked"', (room_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def is_room_available(self, room_id, desired_check_in, desired_check_out):
        """Check for date overlap. Dates are strings YYYY-MM-DD."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM bookings
            WHERE room_id = ? AND status = 'booked' AND NOT (check_out <= ? OR check_in >= ?)
        ''', (room_id, desired_check_in, desired_check_out))
        conflict = cursor.fetchone()
        conn.close()
        return conflict is None

    def cancel_booking(self, booking_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE bookings SET status = "cancelled" WHERE id = ?', (booking_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
