import sqlite3
from datetime import datetime

class LostPersonRegistry:
    def __init__(self, db_path='C:\\Users\\yshel\\Downloads\\kumbh_smart_seva_v2\\kumbh_smart_seva_v2\\database\\main.db'):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== LOST PERSON OPERATIONS ====================
    
    def add_report(self, user_id, name, age, gender, description, 
                   last_seen_location, contact, photo_path=None):
        """Add a lost person report"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO lost_persons 
                   (user_id, name, age, gender, description, 
                    last_seen_location, contact, photo_path) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, name, age, gender, description, 
                 last_seen_location, contact, photo_path)
            )
            report_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return report_id
        except Exception as e:
            print(f"Error adding report: {e}")
            return None
    
    def get_all_reports(self, status='lost'):
        """Get all lost person reports"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT lp.*, u.name as reporter_name, u.phone as reporter_phone
               FROM lost_persons lp
               JOIN users u ON lp.user_id = u.id
               WHERE lp.status = ?
               ORDER BY lp.created_at DESC''',
            (status,)
        )
        reports = cursor.fetchall()
        conn.close()
        return [dict(report) for report in reports]
    
    def get_report(self, report_id):
        """Get a specific report"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT lp.*, u.name as reporter_name, u.email as reporter_email, 
                      u.phone as reporter_phone
               FROM lost_persons lp
               JOIN users u ON lp.user_id = u.id
               WHERE lp.id = ?''',
            (report_id,)
        )
        report = cursor.fetchone()
        conn.close()
        return dict(report) if report else None
    
    def get_user_reports(self, user_id):
        """Get all reports by a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM lost_persons WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        reports = cursor.fetchall()
        conn.close()
        return [dict(report) for report in reports]
    
    def mark_as_found(self, report_id, user_id=None):
        """Mark a lost person as found"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # If user_id provided, verify ownership
            if user_id:
                cursor.execute(
                    '''UPDATE lost_persons 
                       SET status = 'found', updated_at = CURRENT_TIMESTAMP 
                       WHERE id = ? AND user_id = ?''',
                    (report_id, user_id)
                )
            else:
                cursor.execute(
                    '''UPDATE lost_persons 
                       SET status = 'found', updated_at = CURRENT_TIMESTAMP 
                       WHERE id = ?''',
                    (report_id,)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking as found: {e}")
            return False
    
    def search_reports(self, search_term):
        """Search lost person reports"""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_pattern = f'%{search_term}%'
        cursor.execute(
            '''SELECT lp.*, u.name as reporter_name
               FROM lost_persons lp
               JOIN users u ON lp.user_id = u.id
               WHERE (lp.name LIKE ? OR lp.description LIKE ? 
                      OR lp.last_seen_location LIKE ?)
               AND lp.status = 'lost'
               ORDER BY lp.created_at DESC''',
            (search_pattern, search_pattern, search_pattern)
        )
        reports = cursor.fetchall()
        conn.close()
        return [dict(report) for report in reports]
    
    # ==================== FOUND PERSON OPERATIONS ====================
    
    def add_found_person(self, user_id, description, location, contact, photo_path=None):
        """Add a found person report"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO found_persons 
                   (user_id, description, location, contact, photo_path) 
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, description, location, contact, photo_path)
            )
            found_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return found_id
        except Exception as e:
            print(f"Error adding found person: {e}")
            return None
    
    def get_found_persons(self, status='unclaimed'):
        """Get all found persons"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT fp.*, u.name as reporter_name, u.phone as reporter_phone
               FROM found_persons fp
               JOIN users u ON fp.user_id = u.id
               WHERE fp.status = ?
               ORDER BY fp.created_at DESC''',
            (status,)
        )
        found_persons = cursor.fetchall()
        conn.close()
        return [dict(fp) for fp in found_persons]
    
    def get_found_person(self, found_id):
        """Get a specific found person report"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT fp.*, u.name as reporter_name, u.email as reporter_email, 
                      u.phone as reporter_phone
               FROM found_persons fp
               JOIN users u ON fp.user_id = u.id
               WHERE fp.id = ?''',
            (found_id,)
        )
        found_person = cursor.fetchone()
        conn.close()
        return dict(found_person) if found_person else None
    
    # ==================== STATISTICS ====================
    
    def get_stats(self):
        """Get overall statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total lost reports
        cursor.execute("SELECT COUNT(*) as count FROM lost_persons WHERE status = 'lost'")
        total_lost = cursor.fetchone()['count']
        
        # Total found
        cursor.execute("SELECT COUNT(*) as count FROM lost_persons WHERE status = 'found'")
        total_reunited = cursor.fetchone()['count']
        
        # Found persons waiting
        cursor.execute("SELECT COUNT(*) as count FROM found_persons WHERE status = 'unclaimed'")
        found_waiting = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'total_lost': total_lost,
            'total_reunited': total_reunited,
            'found_waiting': found_waiting,
            'success_rate': round((total_reunited / (total_lost + total_reunited) * 100), 2) if (total_lost + total_reunited) > 0 else 0
        }
