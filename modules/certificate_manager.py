import qrcode
import uuid
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import sqlite3
import database

class CertificateManager:
    """Manages visitor certificate generation, storage, and verification"""
    
    def __init__(self, db_path=None, upload_folder='static/uploads'):
        if db_path is None:
            db_path = database.DB_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.upload_folder = upload_folder
        self.qr_folder = os.path.join(upload_folder, 'qr_codes')
        self.cert_folder = os.path.join(upload_folder, 'certificates')
        os.makedirs(self.qr_folder, exist_ok=True)
        os.makedirs(self.cert_folder, exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def generate_certificate(self, user_id, full_name, location_id, visit_date, 
                            photo_path=None, email=None, phone=None):
        """
        Generate a new visitor certificate
        Returns: certificate_id if successful, None otherwise
        """
        try:
            certificate_id = str(uuid.uuid4())[:8].upper()
            
            # Ensure location_id is an integer
            location_id = int(location_id)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check for duplicate (same person, same location, same date)
            cursor.execute('''
                SELECT id FROM visitor_certificates 
                WHERE full_name = ? AND location_id = ? AND visit_date = ?
            ''', (full_name, location_id, visit_date))
            
            if cursor.fetchone():
                conn.close()
                return None  # Duplicate entry
            
            # Insert certificate
            cursor.execute('''
                INSERT INTO visitor_certificates 
                (certificate_id, user_id, full_name, location_id, visit_date, photo_path, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (certificate_id, user_id, full_name, location_id, visit_date, photo_path, email, phone))
            
            cert_record_id = cursor.lastrowid
            conn.commit()
            
            # Generate QR code
            qr_path = self._generate_qr_code(certificate_id)
            
            # Update QR code path
            cursor.execute('UPDATE visitor_certificates SET qr_code_path = ? WHERE id = ?', 
                          (qr_path, cert_record_id))
            conn.commit()
            conn.close()
            
            return certificate_id
            
        except Exception as e:
            print(f"Error generating certificate: {str(e)}")
            return None
    
    def _generate_qr_code(self, certificate_id):
        """Generate QR code for certificate"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(certificate_id)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_filename = f"cert_{certificate_id}.png"
            qr_path = os.path.join(self.qr_folder, qr_filename)
            qr_image.save(qr_path)
            
            return qr_filename
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            return None
    
    def get_certificate(self, certificate_id):
        """Get certificate details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT vc.*, l.name as location_name 
            FROM visitor_certificates vc
            LEFT JOIN locations l ON vc.location_id = l.id
            WHERE vc.certificate_id = ?
        ''', (certificate_id,))
        
        cert = cursor.fetchone()
        conn.close()
        return dict(cert) if cert else None
    
    def verify_certificate(self, certificate_id):
        """Verify certificate authenticity"""
        cert = self.get_certificate(certificate_id)
        return {
            'valid': cert is not None,
            'certificate': cert
        }
    
    def get_user_certificates(self, user_id):
        """Get all certificates for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT vc.*, l.name as location_name 
            FROM visitor_certificates vc
            LEFT JOIN locations l ON vc.location_id = l.id
            WHERE vc.user_id = ?
            ORDER BY vc.created_at DESC
        ''', (user_id,))
        
        certs = cursor.fetchall()
        conn.close()
        return [dict(c) for c in certs]
    
    def get_all_certificates(self, location_id=None, start_date=None, end_date=None):
        """Get certificates with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT vc.*, l.name as location_name 
            FROM visitor_certificates vc
            LEFT JOIN locations l ON vc.location_id = l.id
            WHERE 1=1
        '''
        params = []
        
        if location_id:
            query += ' AND vc.location_id = ?'
            params.append(location_id)
        
        if start_date:
            query += ' AND DATE(vc.visit_date) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(vc.visit_date) <= ?'
            params.append(end_date)
        
        query += ' ORDER BY vc.created_at DESC'
        cursor.execute(query, params)
        
        certs = cursor.fetchall()
        conn.close()
        return [dict(c) for c in certs]
    
    def get_certificate_count_by_location(self, start_date=None, end_date=None):
        """Get certificate count grouped by location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT l.id, l.name as location_name, COUNT(vc.id) as count
            FROM locations l
            LEFT JOIN visitor_certificates vc ON l.id = vc.location_id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND DATE(vc.visit_date) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(vc.visit_date) <= ?'
            params.append(end_date)
        
        query += ' GROUP BY l.id, l.name'
        cursor.execute(query, params)
        
        results = cursor.fetchall()
        conn.close()
        return [dict(r) for r in results]
    
    def get_certificate_count(self):
        """Get total certificate count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM visitor_certificates')
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    
    def get_peak_hours(self, location_id=None, date=None):
        """Get peak visiting hours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT strftime('%H', vc.created_at) as hour, COUNT(vc.id) as count
            FROM visitor_certificates vc
            WHERE 1=1
        '''
        params = []
        
        if location_id:
            query += ' AND vc.location_id = ?'
            params.append(location_id)
        
        if date:
            query += ' AND DATE(vc.created_at) = ?'
            params.append(date)
        
        query += ' GROUP BY hour ORDER BY count DESC LIMIT 5'
        cursor.execute(query, params)
        
        results = cursor.fetchall()
        conn.close()
        return [dict(r) for r in results]
    
    def get_daily_statistics(self, location_id=None, days=30):
        """Get daily visitor statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT DATE(vc.visit_date) as date, COUNT(vc.id) as count
            FROM visitor_certificates vc
            WHERE 1=1
        '''
        params = []
        
        if location_id:
            query += ' AND vc.location_id = ?'
            params.append(location_id)
        
        query += f''' AND DATE(vc.visit_date) >= DATE('now', '-{days} days')
            GROUP BY DATE(vc.visit_date)
            ORDER BY date DESC
        '''
        cursor.execute(query, params)
        
        results = cursor.fetchall()
        conn.close()
        return [dict(r) for r in results]
