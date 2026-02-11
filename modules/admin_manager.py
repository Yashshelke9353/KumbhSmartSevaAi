import sqlite3
from datetime import datetime, timedelta
import os

class AdminManager:
    """Manages admin users, volunteers, and their assignments"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(base_dir, 'database', 'main.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== ADMIN USER MANAGEMENT ====================
    
    def create_admin_user(self, name, email, phone, password_hash, role='volunteer', location_id=None):
        """Create a new admin/staff user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_users (name, email, phone, password, role, location_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (name, email, phone, password_hash, role, location_id))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def get_admin_by_email(self, email):
        """Get admin user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_admin_by_id(self, user_id):
        """Get admin user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_all_admins(self, role=None, location_id=None):
        """Get all admin users with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM admin_users WHERE status = ?'
        params = ['active']
        
        if role:
            query += ' AND role = ?'
            params.append(role)
        
        if location_id:
            query += ' AND location_id = ?'
            params.append(location_id)
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        conn.close()
        return [dict(u) for u in users]
    
    def update_admin_status(self, user_id, status):
        """Update admin user status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE admin_users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (status, user_id)
        )
        conn.commit()
        conn.close()
        return True
    
    # ==================== VOLUNTEER ASSIGNMENT ====================
    
    def assign_volunteer(self, admin_user_id, location_id, shift_start, shift_end):
        """Assign volunteer to a location and shift"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO volunteer_assignments 
                (admin_user_id, location_id, shift_start, shift_end, status)
                VALUES (?, ?, ?, ?, 'assigned')
            ''', (admin_user_id, location_id, shift_start, shift_end))
            
            assignment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return assignment_id
        except Exception as e:
            print(f"Error assigning volunteer: {str(e)}")
            return None
    
    def get_volunteer_assignments(self, admin_user_id=None, location_id=None):
        """Get volunteer assignments"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT va.*, au.name as volunteer_name, l.name as location_name
            FROM volunteer_assignments va
            JOIN admin_users au ON va.admin_user_id = au.id
            JOIN locations l ON va.location_id = l.id
            WHERE 1=1
        '''
        params = []
        
        if admin_user_id:
            query += ' AND va.admin_user_id = ?'
            params.append(admin_user_id)
        
        if location_id:
            query += ' AND va.location_id = ?'
            params.append(location_id)
        
        cursor.execute(query, params)
        assignments = cursor.fetchall()
        conn.close()
        return [dict(a) for a in assignments]
    
    def get_active_volunteers(self, location_id):
        """Get currently active volunteers for a location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT au.id, au.name, au.email, au.phone
            FROM volunteer_assignments va
            JOIN admin_users au ON va.admin_user_id = au.id
            WHERE va.location_id = ? AND va.status = 'assigned'
            AND datetime(va.shift_start) <= datetime('now')
            AND datetime(va.shift_end) >= datetime('now')
        ''', (location_id,))
        
        volunteers = cursor.fetchall()
        conn.close()
        return [dict(v) for v in volunteers]
    
    # ==================== CROWD ANALYSIS ====================
    
    def record_crowd_data(self, location_id, visitor_count, crowd_level='normal'):
        """Record crowd data for a location"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crowd_data (location_id, visitor_count, crowd_level)
                VALUES (?, ?, ?)
            ''', (location_id, visitor_count, crowd_level))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error recording crowd data: {str(e)}")
            return False
    
    def get_current_crowd_status(self, location_id):
        """Get latest crowd status for a location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crowd_data 
            WHERE location_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (location_id,))
        
        data = cursor.fetchone()
        conn.close()
        return dict(data) if data else None
    
    def get_crowd_history(self, location_id, hours=24):
        """Get crowd history for the last N hours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM crowd_data 
            WHERE location_id = ? 
            AND timestamp > datetime('now', ? || ' hours')
            ORDER BY timestamp ASC
        ''', (location_id, -hours))
        
        data = cursor.fetchall()
        conn.close()
        return [dict(d) for d in data]
    
    def get_all_locations_status(self):
        """Get current status of all locations with fallback to certificate counts"""
        conn = self.get_connection()
        cursor = conn.cursor()
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
        return [dict(l) for l in locations]
    
    def get_crowd_analytics(self, location_id, days=7):
        """Get crowd analytics for a location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Peak hours
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, AVG(visitor_count) as avg_visitors
            FROM crowd_data 
            WHERE location_id = ? AND timestamp > datetime('now', ? || ' days')
            GROUP BY hour
            ORDER BY avg_visitors DESC
        ''', (location_id, -days))
        
        peak_hours = [dict(r) for r in cursor.fetchall()]
        
        # Daily totals
        cursor.execute('''
            SELECT DATE(timestamp) as date, AVG(visitor_count) as avg_visitors, MAX(visitor_count) as peak_visitors
            FROM crowd_data 
            WHERE location_id = ? AND timestamp > datetime('now', ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''', (location_id, -days))
        
        daily_data = [dict(r) for r in cursor.fetchall()]
        
        # Crowd level distribution
        cursor.execute('''
            SELECT crowd_level, COUNT(*) as count
            FROM crowd_data 
            WHERE location_id = ? AND timestamp > datetime('now', ? || ' days')
            GROUP BY crowd_level
        ''', (location_id, -days))
        
        crowd_levels = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            'peak_hours': peak_hours,
            'daily_data': daily_data,
            'crowd_levels': crowd_levels
        }
    
    # ==================== ALERTS ====================
    
    def create_alert(self, location_id, alert_type, message, severity='medium'):
        """Create an alert"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (location_id, alert_type, message, severity)
                VALUES (?, ?, ?, ?)
            ''', (location_id, alert_type, message, severity))
            
            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return alert_id
        except Exception as e:
            print(f"Error creating alert: {str(e)}")
            return None
    
    def get_active_alerts(self, location_id=None):
        """Get active (unresolved) alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM alerts WHERE resolved = 0'
        params = []
        
        if location_id:
            query += ' AND location_id = ?'
            params.append(location_id)
        
        query += ' ORDER BY created_at DESC'
        cursor.execute(query, params)
        
        alerts = cursor.fetchall()
        conn.close()
        return [dict(a) for a in alerts]
    
    def resolve_alert(self, alert_id):
        """Mark an alert as resolved"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE alerts SET resolved = 1 WHERE id = ?', (alert_id,))
        conn.commit()
        conn.close()
        return True
    
    # ==================== LOCATION MANAGEMENT ====================
    
    def get_all_locations(self):
        """Get all locations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM locations ORDER BY name')
        locations = cursor.fetchall()
        conn.close()
        return [dict(l) for l in locations]
    
    def get_location(self, location_id):
        """Get location details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
        location = cursor.fetchone()
        conn.close()
        return dict(location) if location else None
    
    def create_location(self, name, latitude=None, longitude=None, capacity=5000):
        """Create a new location"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO locations (name, latitude, longitude, capacity)
                VALUES (?, ?, ?, ?)
            ''', (name, latitude, longitude, capacity))
            
            location_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return location_id
        except sqlite3.IntegrityError:
            return None
