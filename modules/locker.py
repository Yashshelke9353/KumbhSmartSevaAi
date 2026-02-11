import sqlite3
import qrcode
import os
from datetime import datetime
import database

class DigitalLocker:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = database.DB_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_item(self, user_id, doc_type, doc_number, file_path=None, notes=''):
        """Add item to digital locker"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO locker_items 
                   (user_id, doc_type, doc_number, file_path, notes) 
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, doc_type, doc_number, file_path, notes)
            )
            item_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return item_id
        except Exception as e:
            print(f"Error adding item: {e}")
            return None
    
    def get_user_items(self, user_id):
        """Get all items for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM locker_items WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        items = cursor.fetchall()
        conn.close()
        return [dict(item) for item in items]
    
    def search_items(self, user_id, search_query):
        """Search items by document number or type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_pattern = f'%{search_query}%'
        cursor.execute(
            '''SELECT * FROM locker_items 
               WHERE user_id = ? 
               AND (doc_number LIKE ? OR doc_type LIKE ? OR notes LIKE ?)
               ORDER BY created_at DESC''',
            (user_id, search_pattern, search_pattern, search_pattern)
        )
        items = cursor.fetchall()
        conn.close()
        return [dict(item) for item in items]
    
    def get_item(self, item_id, user_id):
        """Get a specific item (with user verification)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM locker_items WHERE id = ? AND user_id = ?',
            (item_id, user_id)
        )
        item = cursor.fetchone()
        conn.close()
        return dict(item) if item else None
    
    def delete_item(self, item_id, user_id):
        """Delete an item (with user verification)"""
        try:
            # First get the item to delete associated file
            item = self.get_item(item_id, user_id)
            if not item:
                return False
            
            # Delete file if exists
            if item.get('file_path'):
                file_path = os.path.join('static/uploads', item['file_path'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete from database
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM locker_items WHERE id = ? AND user_id = ?',
                (item_id, user_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting item: {e}")
            return False
    
    def generate_qr_code(self, item_id, user_id):
        """Generate QR code for an item"""
        try:
            # Create QR code data
            qr_data = f"KUMBH_LOCKER|ITEM:{item_id}|USER:{user_id}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_dir = 'static/uploads/qr_codes'
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = f'{qr_dir}/qr_{item_id}_{user_id}.png'
            img.save(qr_path)
            
            return qr_path
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None
    
    def get_stats(self, user_id):
        """Get locker statistics for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) as total FROM locker_items WHERE user_id = ?',
            (user_id,)
        )
        total = cursor.fetchone()['total']
        
        cursor.execute(
            '''SELECT doc_type, COUNT(*) as count 
               FROM locker_items 
               WHERE user_id = ? 
               GROUP BY doc_type''',
            (user_id,)
        )
        by_type = cursor.fetchall()
        
        conn.close()
        
        return {
            'total': total,
            'by_type': [dict(row) for row in by_type]
        }
