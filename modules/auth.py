import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from functools import wraps
from flask import redirect, url_for, flash

class JWTAuth:
    """JWT Authentication handler"""
    
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'kumbh-smart-seva-secret-key-change-in-production')
    ALGORITHM = 'HS256'
    TOKEN_EXPIRY_HOURS = 24
    
    @classmethod
    def generate_token(cls, user_id, user_type='visitor'):
        """Generate JWT token for a user"""
        try:
            payload = {
                'user_id': user_id,
                'user_type': user_type,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS)
            }
            token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
            return token
        except Exception as e:
            print(f"Error generating token: {str(e)}")
            return None
    
    @classmethod
    def verify_token(cls, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    @classmethod
    def token_required(cls, f):
        """Decorator to require valid JWT token"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(" ")[1]
                except IndexError:
                    return jsonify({'error': 'Invalid token format'}), 401
            
            if not token:
                return jsonify({'error': 'Token required'}), 401
            
            payload = cls.verify_token(token)
            if 'error' in payload:
                return jsonify(payload), 401
            
            request.user_id = payload['user_id']
            request.user_type = payload['user_type']
            
            return f(*args, **kwargs)
        
        return decorated
    
    @classmethod
    def session_required(cls, f):
        """Decorator to require valid session"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return {'error': 'Session required'}, 401
            return f(*args, **kwargs)
        return decorated

    @classmethod
    def role_or_login_required(cls, *allowed_admin_roles):
        """Decorator that allows either a logged-in user or an admin with one of the allowed roles.

        Usage: @JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
        This lets normal users (session['user_id']) access the route, and also
        lets admins logged-in via admin session access when their role matches.
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Allow regular logged-in users
                if 'user_id' in session:
                    return f(*args, **kwargs)

                # Allow admins with matching role
                admin_role = session.get('admin_role')
                if 'admin_id' in session and admin_role and admin_role in allowed_admin_roles:
                    return f(*args, **kwargs)

                # Not authorized: redirect to appropriate login
                flash('Please login with appropriate account to access this page', 'warning')
                # Prefer admin login if allowed roles include admin-like roles
                return redirect(url_for('login'))

            return wrapped
        return decorator
