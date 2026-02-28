from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from modules.locker import DigitalLocker
from modules.lost_person import LostPersonRegistry
from modules.face_recognition_matcher import FaceRecognitionMatcher
from modules.certificate_manager import CertificateManager
from modules.admin_manager import AdminManager
from modules.auth import JWTAuth
from database.db_manager import DatabaseManager
from modules.rooms import rooms_bp
import json
from dotenv import load_dotenv

# Try to import Google Generative AI, but handle import errors gracefully
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: google-generativeai import failed: {e}")
    print("Translation feature will use fallback. Please ensure all dependencies are installed correctly.")
    GENAI_AVAILABLE = False
    genai = None

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Use environment variable for secret key, fallback to a secure random value for production
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex() if os.getenv('FLASK_ENV') == 'production' else 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Gemini API
model = None
if GENAI_AVAILABLE:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            print("✓ Gemini API initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini API: {e}")
            model = None
    else:
        print("Warning: GEMINI_API_KEY not found in .env file")
else:
    print("Warning: google-generativeai not available. Translation will use basic fallback.")

# Initialize modules
db = DatabaseManager()

# CRITICAL: Initialize database tables BEFORE any routes run
# This must happen here, not in if __name__ == '__main__', to work with Gunicorn on Render
try:
    db.init_db()
    print("✓ Database initialized successfully")
except Exception as e:
    print(f"✗ Database initialization error: {e}")
    import traceback
    traceback.print_exc()

try:
    locker = DigitalLocker()
    print("✓ DigitalLocker initialized")
except Exception as e:
    print(f"✗ DigitalLocker error: {e}")
    locker = None

try:
    lost_registry = LostPersonRegistry()
    print("✓ LostPersonRegistry initialized")
except Exception as e:
    print(f"✗ LostPersonRegistry error: {e}")
    lost_registry = None

try:
    face_matcher = FaceRecognitionMatcher()
    print("✓ FaceRecognitionMatcher initialized")
except Exception as e:
    print(f"✗ FaceRecognitionMatcher error: {e}")
    face_matcher = None

try:
    cert_manager = CertificateManager()
    print("✓ CertificateManager initialized")
except Exception as e:
    print(f"✗ CertificateManager error: {e}")
    cert_manager = None

try:
    admin_manager = AdminManager()
    print("✓ AdminManager initialized")
except Exception as e:
    print(f"✗ AdminManager error: {e}")
    admin_manager = None

# Register rooms blueprint
app.register_blueprint(rooms_bp)

# Ensure upload folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/certificates', exist_ok=True)
os.makedirs('static/uploads/qr_codes', exist_ok=True)

def login_required(f):
    """Decorator to require login for certain routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Enforce login for most modules except certificate generation/verification and public pages
@app.before_request
def require_login_for_modules():
    exempt_endpoints = {
        'index', 'login', 'register', 'logout',
        # Admin login routes must be publicly accessible so staff can authenticate
        'admin_login', 'admin_logout',
        'generate_certificate_page', 'create_certificate', 'view_certificate',
        'verify_certificate', 'verify_certificate_page', 'api_verify_certificate', 'download_certificate'
    }

    endpoint = request.endpoint or ''

    # Allow static files and flask internal endpoints
    if endpoint.startswith('static'):
        return

    # Allow explicit exemptions
    if endpoint in exempt_endpoints:
        return

    # Also allow any certificate-related endpoints (flexible)
    if 'certificate' in endpoint:
        return

    # If user is logged in (regular user or admin), allow
    if session.get('user_id') or session.get('admin_id'):
        return

    # Otherwise block access and redirect to login
    # Do not flash when already on login/register pages
    if endpoint not in {'login', 'register'}:
        flash('Please login to access this feature', 'warning')
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, phone, password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        # Check if user exists
        if db.get_user_by_email(email):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        hashed_password = generate_password_hash(password)
        user_id = db.create_user(name, email, phone, hashed_password)
        
        if user_id:
            flash('Registration successful! Please login', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.get_user_by_email(email)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session['user_id']
    
    # Get user's locker items
    locker_items = locker.get_user_items(user_id)
    
    # Get user's lost person reports
    lost_reports = lost_registry.get_user_reports(user_id)
    
    return render_template('dashboard.html', 
                         locker_items=locker_items,
                         lost_reports=lost_reports)

# ==================== DIGITAL LOCKER ROUTES ====================

@app.route('/locker')
@login_required
def locker_page():
    """Digital locker page with search"""
    user_id = session['user_id']
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Search by document number or type
        items = locker.search_items(user_id, search_query)
        flash(f'Found {len(items)} result(s) for "{search_query}"', 'info')
    else:
        items = locker.get_user_items(user_id)
    
    return render_template('locker.html', items=items, search_query=search_query)

@app.route('/locker/add', methods=['GET', 'POST'])
@login_required
def add_locker_item():
    """Add item to digital locker"""
    if request.method == 'POST':
        user_id = session['user_id']
        doc_type = request.form.get('doc_type')
        doc_number = request.form.get('doc_number')
        notes = request.form.get('notes', '')
        
        # Handle file upload
        file = request.files.get('document')
        file_path = None
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{user_id}_{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_path = filename  # Store relative path
        
        item_id = locker.add_item(user_id, doc_type, doc_number, file_path, notes)
        
        if item_id:
            flash('Document added to locker successfully!', 'success')
            return redirect(url_for('locker_page'))
        else:
            flash('Failed to add document', 'danger')
    
    return render_template('add_locker_item.html')

@app.route('/locker/view/<int:item_id>')
@login_required
def view_locker_item(item_id):
    """View locker item with QR code"""
    user_id = session['user_id']
    item = locker.get_item(item_id, user_id)
    
    if not item:
        flash('Item not found or access denied', 'danger')
        return redirect(url_for('locker_page'))
    
    # Generate QR code
    qr_code_path = locker.generate_qr_code(item_id, user_id)
    
    return render_template('view_locker_item.html', item=item, qr_code=qr_code_path)

@app.route('/locker/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_locker_item(item_id):
    """Delete locker item"""
    user_id = session['user_id']
    
    if locker.delete_item(item_id, user_id):
        flash('Document deleted successfully', 'success')
    else:
        flash('Failed to delete document', 'danger')
    
    return redirect(url_for('locker_page'))

# ==================== LOST PERSON ROUTES ====================

@app.route('/lost-person')
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def lost_person_page():
    """Lost person registry page"""
    reports = lost_registry.get_all_reports()
    return render_template('lost_person.html', reports=reports)

@app.route('/lost-person/report', methods=['GET', 'POST'])
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def report_lost_person():
    """Report a lost person"""
    if request.method == 'POST':
        user_id = session['user_id']
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        description = request.form.get('description')
        last_seen_location = request.form.get('last_seen_location')
        contact = request.form.get('contact')
        
        # Handle photo upload
        photo = request.files.get('photo')
        photo_path = None
        
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lost_{timestamp}_{filename}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            photo_path = filename  # Store relative path
        
        report_id = lost_registry.add_report(
            user_id, name, age, gender, description, 
            last_seen_location, contact, photo_path
        )
        
        if report_id:
            flash('Missing person report submitted successfully!', 'success')
            return redirect(url_for('lost_person_page'))
        else:
            flash('Failed to submit report', 'danger')
    
    return render_template('report_lost_person.html')

@app.route('/lost-person/found', methods=['GET', 'POST'])
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def report_found_person():
    """Report a found person"""
    if request.method == 'POST':
        user_id = session['user_id']
        description = request.form.get('description')
        location = request.form.get('location')
        contact = request.form.get('contact')
        
        # Handle photo upload
        photo = request.files.get('photo')
        photo_path = None
        
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"found_{timestamp}_{filename}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            photo_path = filename
        
        found_id = lost_registry.add_found_person(
            user_id, description, location, contact, photo_path
        )
        
        if found_id:
            flash('Found person report submitted successfully!', 'success')
            return redirect(url_for('found_persons_page'))
        else:
            flash('Failed to submit report', 'danger')
    
    return render_template('report_found_person.html')

@app.route('/lost-person/found-list')
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def found_persons_page():
    """List of found persons"""
    found_persons = lost_registry.get_found_persons()
    return render_template('found_persons.html', found_persons=found_persons)

@app.route('/lost-person/view/<int:report_id>')
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def view_lost_report(report_id):
    """View detailed lost person report"""
    report = lost_registry.get_report(report_id)
    
    if not report:
        flash('Report not found', 'danger')
        return redirect(url_for('lost_person_page'))
    
    return render_template('view_lost_report.html', report=report)

@app.route('/lost-person/mark-found/<int:report_id>', methods=['POST'])
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def mark_as_found(report_id):
    """Mark a lost person as found"""
    user_id = session['user_id']
    
    if lost_registry.mark_as_found(report_id, user_id):
        flash('Person marked as found!', 'success')
    else:
        flash('Failed to update status', 'danger')
    
    return redirect(url_for('lost_person_page'))

@app.route('/my-reports')
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def my_reports():
    """User's own reports"""
    user_id = session['user_id']
    reports = lost_registry.get_user_reports(user_id)
    return render_template('my_reports.html', reports=reports)

# ==================== FACE RECOGNITION ROUTES ====================

@app.route('/face-match')
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def face_match_page():
    """Face matching dashboard"""
    # Get all lost and found persons with photos
    lost_persons = lost_registry.get_all_reports(status='lost')
    found_persons = lost_registry.get_found_persons()
    
    # Filter only those with photos
    lost_with_photos = [p for p in lost_persons if p.get('photo_path')]
    found_with_photos = [p for p in found_persons if p.get('photo_path')]
    
    return render_template('face_match.html', 
                         lost_count=len(lost_with_photos),
                         found_count=len(found_with_photos))

@app.route('/face-match/run', methods=['POST'])
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def run_face_match():
    """Run face matching algorithm"""
    try:
        # Get threshold from request (default 40%)
        threshold = int(request.form.get('threshold', 40))
        
        # Get all persons with photos - try multiple status options
        # First try 'lost' status, if empty try all statuses
        lost_persons = lost_registry.get_all_reports(status='lost')
        if not lost_persons:
            # Fallback: get all lost reports regardless of status
            try:
                conn = lost_registry.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT lp.*, u.name as reporter_name, u.phone as reporter_phone
                    FROM lost_persons lp
                    JOIN users u ON lp.user_id = u.id
                    ORDER BY lp.created_at DESC
                ''')
                lost_persons = [dict(report) for report in cursor.fetchall()]
                conn.close()
            except:
                lost_persons = []
        
        found_persons = lost_registry.get_found_persons()
        if not found_persons:
            # Fallback: get all found reports regardless of status
            try:
                conn = lost_registry.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fp.*, u.name as reporter_name, u.phone as reporter_phone
                    FROM found_persons fp
                    JOIN users u ON fp.user_id = u.id
                    ORDER BY fp.created_at DESC
                ''')
                found_persons = [dict(fp) for fp in cursor.fetchall()]
                conn.close()
            except:
                found_persons = []
        
        # Filter only those with photos
        lost_with_photos = [p for p in lost_persons if p.get('photo_path')]
        found_with_photos = [p for p in found_persons if p.get('photo_path')]
        
        if not lost_with_photos:
            flash('No lost person reports with photos found. Please create a lost person report with a photo first.', 'warning')
            return redirect(url_for('face_match_page'))
        
        if not found_with_photos:
            flash('No found person reports with photos found. Please create a found person report with a photo first.', 'warning')
            return redirect(url_for('face_match_page'))
        
        print(f"[FACE MATCH] Lost with photos: {len(lost_with_photos)}, Found with photos: {len(found_with_photos)}, Threshold: {threshold}%")
        
        # Run batch matching
        matches = face_matcher.batch_match_all(
            lost_with_photos, 
            found_with_photos, 
            threshold
        )
        
        total_matches = sum(len(m) for m in matches.values()) if matches else 0
        
        if not matches or total_matches == 0:
            # No matches at current threshold - suggest lower threshold
            flash(f'No matches found with {threshold}% similarity threshold. Try lowering it to 20-30% for more results.', 'info')
            # Show empty results page
            return render_template('face_match_results.html', 
                                 matches={},
                                 lost_persons={p['id']: p for p in lost_persons},
                                 found_persons={p['id']: p for p in found_persons},
                                 threshold=threshold)
        else:
            flash(f'Found {total_matches} match(es) across {len(matches)} lost person(s)!', 'success')
        
        return render_template('face_match_results.html', 
                             matches=matches,
                             lost_persons={p['id']: p for p in lost_persons},
                             found_persons={p['id']: p for p in found_persons},
                             threshold=threshold)
        
    except Exception as e:
        print(f"[ERROR] Face matching: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error during face matching: {str(e)}', 'danger')
        return redirect(url_for('face_match_page'))

@app.route('/face-match/compare/<int:lost_id>/<int:found_id>')
@JWTAuth.role_or_login_required('admin', 'supervisor', 'volunteer')
def compare_faces(lost_id, found_id):
    """Compare two specific persons"""
    try:
        lost_report = lost_registry.get_report(lost_id)
        found_report = lost_registry.get_found_person(found_id)
        
        if not lost_report or not found_report:
            flash('Report not found', 'danger')
            return redirect(url_for('face_match_page'))
        
        # Calculate similarity
        similarity = 0
        if lost_report.get('photo_path') and found_report.get('photo_path'):
            lost_path = f"static/uploads/{lost_report['photo_path']}"
            found_path = f"static/uploads/{found_report['photo_path']}"
            
            print(f"Comparing faces: {lost_path} vs {found_path}")
            
            if os.path.exists(lost_path) and os.path.exists(found_path):
                # Use find_matches to compare single pair
                matches = face_matcher.find_matches(lost_path, [(found_id, found_path)], threshold=0)
                if matches and len(matches) > 0:
                    similarity = int(matches[0].get('similarity', 0))
                    print(f"Similarity score: {similarity}%")
                else:
                    print("No matches found or similarity is 0")
            else:
                flash('One or both photos not found', 'warning')
                if not os.path.exists(lost_path):
                    print(f"Lost person photo not found: {lost_path}")
                if not os.path.exists(found_path):
                    print(f"Found person photo not found: {found_path}")
        
        return render_template('compare_faces.html',
                             lost_report=lost_report,
                             found_report=found_report,
                             similarity=similarity)
    
    except Exception as e:
        print(f"Error in compare_faces: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error comparing faces: {str(e)}', 'danger')
        return redirect(url_for('face_match_page'))

# ==================== CERTIFICATE ROUTES ====================

@app.route('/generate-certificate')
def generate_certificate_page():
    """Certificate generation page"""
    locations = admin_manager.get_all_locations()
    return render_template('generate_certificate.html', locations=locations)

@app.route('/certificate/create', methods=['POST'])
def create_certificate():
    """Create a new visitor certificate"""
    try:
        full_name = request.form.get('full_name', '').strip()
        location_id = request.form.get('location_id', '').strip()
        visit_date = request.form.get('visit_date', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validate required fields
        if not all([full_name, location_id, visit_date]):
            return jsonify({
                'success': False,
                'error': 'Full name, location, and visit date are required'
            }), 400
        
        # Ensure location exists
        location = admin_manager.get_location(int(location_id))
        if not location:
            return jsonify({
                'success': False,
                'error': 'Invalid location. Please select a valid location.'
            }), 400
        
        # Handle photo upload
        photo = request.files.get('photo')
        photo_path = None
        
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cert_{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            photo.save(file_path)
            photo_path = filename
        
        # Generate certificate
        # Use anonymous user for non-logged-in visitors
        user_id = session.get('user_id', 0)
        
        cert_id = cert_manager.generate_certificate(
            user_id, full_name, int(location_id), visit_date, photo_path, email, phone
        )
        
        if cert_id:
            return jsonify({
                'success': True,
                'certificate_id': cert_id,
                'redirect': url_for('view_certificate', certificate_id=cert_id)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'This certificate already exists for the same person on the same date at this location.'
            }), 400
            
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        print(f"Certificate creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'Error creating certificate: {str(e)}'}), 500

@app.route('/certificate/<certificate_id>/save-image', methods=['POST'])
def save_certificate_image(certificate_id):
    """Save certificate image to server"""
    try:
        cert = cert_manager.get_certificate(certificate_id)
        
        if not cert:
            return jsonify({'success': False, 'error': 'Certificate not found'}), 404
        
        # Get the image data from the request
        data = request.get_json()
        image_data = data.get('image_data')  # Base64 encoded PNG
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Create certificates folder if it doesn't exist
        cert_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'certificates')
        os.makedirs(cert_folder, exist_ok=True)
        
        # Save the image
        import base64
        image_filename = f"Kumbh_Certificate_{certificate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        image_path = os.path.join(cert_folder, image_filename)
        
        # Decode base64 image data and save
        image_data = image_data.replace('data:image/png;base64,', '')
        with open(image_path, 'wb') as img_file:
            img_file.write(base64.b64decode(image_data))
        
        return jsonify({
            'success': True,
            'message': 'Certificate image saved successfully',
            'filename': image_filename,
            'path': f'/static/uploads/certificates/{image_filename}'
        }), 200
    
    except Exception as e:
        print(f"Error saving certificate image: {str(e)}")
        return jsonify({'success': False, 'error': f'Error saving image: {str(e)}'}), 500

@app.route('/certificate/<certificate_id>')
def view_certificate(certificate_id):
    """View certificate details"""
    cert = cert_manager.get_certificate(certificate_id)
    
    if not cert:
        flash('Certificate not found', 'danger')
        return redirect(url_for('index'))
    
    return render_template('view_certificate.html', certificate=cert)

@app.route('/certificate/verify/<certificate_id>')
def verify_certificate(certificate_id):
    """Verify certificate authenticity"""
    result = cert_manager.verify_certificate(certificate_id)
    return render_template('verify_certificate.html', result=result)

@app.route('/verify-certificate')
def verify_certificate_page():
    """Certificate verification page"""
    return render_template('verify_certificate.html', result=None)

@app.route('/api/certificate/verify', methods=['POST'])
def api_verify_certificate():
    """API endpoint to verify certificate"""
    data = request.get_json()
    cert_id = data.get('certificate_id')
    
    result = cert_manager.verify_certificate(cert_id)
    return jsonify(result)

@app.route('/certificate/<certificate_id>/download')
def download_certificate(certificate_id):
    """Download certificate as PDF (placeholder)"""
    cert = cert_manager.get_certificate(certificate_id)
    
    if not cert:
        flash('Certificate not found', 'danger')
        return redirect(url_for('index'))
    
    # Generate simple HTML to PDF (you can use reportlab or weasyprint)
    # For now, return certificate data as JSON for frontend to handle
    return jsonify({
        'certificate_id': cert['certificate_id'],
        'full_name': cert['full_name'],
        'location': cert['location_name'],
        'visit_date': cert['visit_date'],
        'created_at': cert['created_at']
    })

# ==================== ADMIN DASHBOARD ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin/Volunteer login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = admin_manager.get_admin_by_email(email)
        
        if admin and check_password_hash(admin['password'], password) and admin['status'] == 'active':
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            session['admin_role'] = admin['role']
            session['location_id'] = admin['location_id']
            flash(f'Welcome, {admin["name"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials or account inactive', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

def admin_login_required(f):
    """Decorator to require admin login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login as admin first', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_role_required(role):
    """Decorator to require specific admin role"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin_id' not in session:
                flash('Please login as admin first', 'warning')
                return redirect(url_for('admin_login'))
            
            if session.get('admin_role') not in [role, 'admin', 'supervisor']:
                flash('Insufficient permissions', 'danger')
                return redirect(url_for('admin_dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    """Admin dashboard home"""
    admin_id = session['admin_id']
    admin = admin_manager.get_admin_by_id(admin_id)
    
    # Get statistics
    all_locations = admin_manager.get_all_locations()
    locations_status = admin_manager.get_all_locations_status()
    active_alerts = admin_manager.get_active_alerts(admin.get('location_id'))
    
    # Get certificate statistics
    raw_certs = cert_manager.get_certificate_count_by_location()

    # Normalize keys to match templates (use 'location_name')
    certs_data = []
    for c in raw_certs:
        # certificate_manager returns 'name' — map to 'location_name'
        certs_data.append({
            'id': c.get('id'),
            'location_name': c.get('name') or c.get('location_name') or 'Unknown',
            'count': int(c.get('count', 0))
        })

    # Calculate total metrics
    total_visitors = sum(c['count'] for c in certs_data)

    return render_template('admin_dashboard.html',
                         admin=admin,
                         locations_status=locations_status,
                         active_alerts=active_alerts,
                         total_visitors=total_visitors,
                         certs_data=certs_data)


@app.route('/supervisor/dashboard')
@admin_role_required('supervisor')
def supervisor_dashboard():
    """Supervisor-specific dashboard"""
    admin_id = session.get('admin_id')
    admin = admin_manager.get_admin_by_id(admin_id)
    # Provide a simplified view for supervisors
    return render_template('supervisor_dashboard.html', admin=admin)


@app.route('/volunteer/dashboard')
@admin_role_required('volunteer')
def volunteer_dashboard():
    """Volunteer dashboard"""
    admin_id = session.get('admin_id')
    admin = admin_manager.get_admin_by_id(admin_id)
    # Volunteers have a simple dashboard focused on reports and assignments
    assignments = admin_manager.get_volunteer_assignments(location_id=session.get('location_id'))
    return render_template('volunteer_dashboard.html', admin=admin, assignments=assignments)

@app.route('/admin/analytics')
@admin_login_required
def admin_analytics():
    """Analytics page"""
    locations = admin_manager.get_all_locations()
    selected_location_id = request.args.get('location_id', locations[0]['id'] if locations else None)
    days = int(request.args.get('days', 7))

    if selected_location_id:
        # Use certificate data as the primary source for analytics
        try:
            loc_id = int(selected_location_id)
        except (TypeError, ValueError):
            loc_id = None

        if loc_id:
            # Daily visitor stats from certificates
            raw_daily = cert_manager.get_daily_statistics(location_id=loc_id, days=days)

            # Normalize daily data to match template expectations (avg_visitors, peak_visitors)
            daily_data = []
            for d in raw_daily:
                cnt = int(d.get('count', 0))
                daily_data.append({
                    'date': d.get('date'),
                    'avg_visitors': cnt,
                    'peak_visitors': cnt
                })

            # Peak hours from certificate creation timestamps
            raw_peak = cert_manager.get_peak_hours(location_id=loc_id)
            peak_hours = []
            for p in raw_peak:
                peak_hours.append({
                    'hour': p.get('hour'),
                    'avg_visitors': int(p.get('count', 0))
                })

            # Derive crowd level distribution from daily certificate counts vs location capacity
            location = admin_manager.get_location(loc_id)
            capacity = location.get('capacity', 5000) if location else 5000

            high, medium, normal = 0, 0, 0
            for d in daily_data:
                count = int(d.get('count', d.get('avg_visitors', 0)))
                if count > capacity * 0.8:
                    high += 1
                elif count > capacity * 0.5:
                    medium += 1
                else:
                    normal += 1

            crowd_levels = []
            if normal:
                crowd_levels.append({'crowd_level': 'normal', 'count': normal})
            if medium:
                crowd_levels.append({'crowd_level': 'medium', 'count': medium})
            if high:
                crowd_levels.append({'crowd_level': 'high', 'count': high})

            analytics = {
                'peak_hours': peak_hours,
                'daily_data': daily_data,
                'crowd_levels': crowd_levels
            }
        else:
            analytics = {'peak_hours': [], 'daily_data': [], 'crowd_levels': []}
            daily_data = []
            peak_hours = []
    else:
        analytics = {'peak_hours': [], 'daily_data': [], 'crowd_levels': []}
        daily_data = []
        peak_hours = []
    
    return render_template('admin_analytics.html',
                         locations=locations,
                         selected_location_id=selected_location_id,
                         analytics=analytics,
                         daily_data=daily_data,
                         peak_hours=peak_hours)

@app.route('/admin/volunteers')
@admin_role_required('supervisor')
def manage_volunteers():
    """Manage volunteers"""
    location_id = session.get('location_id')
    volunteers = admin_manager.get_all_admins(role='volunteer', location_id=location_id)
    locations = admin_manager.get_all_locations()
    assignments = admin_manager.get_volunteer_assignments(location_id=location_id)
    
    return render_template('manage_volunteers.html',
                         volunteers=volunteers,
                         locations=locations,
                         assignments=assignments)

@app.route('/admin/volunteers/assign', methods=['POST'])
@admin_role_required('supervisor')
def assign_volunteer():
    """Assign volunteer to location"""
    admin_user_id = request.form.get('admin_user_id')
    location_id = request.form.get('location_id')
    shift_start = request.form.get('shift_start')
    shift_end = request.form.get('shift_end')
    
    assignment_id = admin_manager.assign_volunteer(admin_user_id, location_id, shift_start, shift_end)
    
    if assignment_id:
        flash('Volunteer assigned successfully', 'success')
    else:
        flash('Failed to assign volunteer', 'danger')
    
    return redirect(url_for('manage_volunteers'))

@app.route('/admin/crowd-status/<int:location_id>')
@admin_login_required
def crowd_status(location_id):
    """Get crowd status for a location"""
    status = admin_manager.get_current_crowd_status(location_id)
    history = admin_manager.get_crowd_history(location_id, hours=24)
    
    return render_template('crowd_status.html',
                         location_id=location_id,
                         status=status,
                         history=history)

@app.route('/admin/alerts')
@admin_login_required
def manage_alerts():
    """Manage alerts"""
    location_id = session.get('location_id')
    alerts = admin_manager.get_active_alerts(location_id)
    
    return render_template('manage_alerts.html', alerts=alerts)

@app.route('/admin/alerts/<int:alert_id>/resolve', methods=['POST'])
@admin_login_required
def resolve_alert(alert_id):
    """Resolve an alert"""
    if admin_manager.resolve_alert(alert_id):
        flash('Alert resolved', 'success')
    else:
        flash('Failed to resolve alert', 'danger')
    
    return redirect(url_for('manage_alerts'))

@app.route('/admin/reports')
@admin_login_required
def admin_reports():
    """Generate reports"""
    location_id = session.get('location_id')
    report_type = request.args.get('type', 'daily')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get certificate data
    certs = cert_manager.get_all_certificates(location_id, start_date, end_date)
    
    # Group by location
    certs_by_location = cert_manager.get_certificate_count_by_location(start_date, end_date)
    
    # Calculate number of days
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days_count = (end_dt - start_dt).days + 1
        per_day_avg = len(certs) // days_count if days_count > 0 else 0
    except:
        days_count = 1
        per_day_avg = len(certs)
    
    return render_template('admin_reports.html',
                         report_type=report_type,
                         start_date=start_date,
                         end_date=end_date,
                         certificates=certs,
                         certs_by_location=certs_by_location,
                         days_count=days_count,
                         per_day_avg=per_day_avg)

# ==================== API ENDPOINTS ====================

@app.route('/api/crowd-data', methods=['POST'])
@admin_login_required
def api_record_crowd_data():
    """API endpoint to record crowd data"""
    data = request.get_json()
    location_id = data.get('location_id')
    visitor_count = data.get('visitor_count')
    
    # Determine crowd level
    location = admin_manager.get_location(location_id)
    if location:
        capacity = location['capacity']
        if visitor_count > capacity * 0.8:
            crowd_level = 'high'
        elif visitor_count > capacity * 0.5:
            crowd_level = 'medium'
        else:
            crowd_level = 'normal'
    else:
        crowd_level = 'normal'
    
    if admin_manager.record_crowd_data(location_id, visitor_count, crowd_level):
        # If high, create alert
        if crowd_level == 'high':
            admin_manager.create_alert(
                location_id,
                'crowd_alert',
                f'High crowd density detected: {visitor_count} visitors',
                'high'
            )
        
        return jsonify({'success': True})
    else:
        return jsonify({'success': False}), 500

@app.route('/api/locations/status')
def api_locations_status():
    """Get status of all locations"""
    locations = admin_manager.get_all_locations_status()
    return jsonify(locations)

@app.route('/api/dashboard/stats')
@admin_login_required
def api_dashboard_stats():
    """Get dashboard statistics"""
    certs_data = cert_manager.get_certificate_count_by_location()
    peak_hours = cert_manager.get_peak_hours()
    
    return jsonify({
        'locations': certs_data,
        'peak_hours': peak_hours
    })

@app.route('/api/translate', methods=['POST'])
def api_translate():
    """Translate text using Google Gemini API or fallback method"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_language = data.get('source_language', '').split('-')[0]  # Get language code
        target_language = data.get('target_language', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Map language codes to language names for better prompting
        language_map = {
            'en': 'English',
            'hi': 'Hindi',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'ml': 'Malayalam'
        }
        
        source_lang_name = language_map.get(source_language, 'English')
        target_lang_name = language_map.get(target_language, 'English')
        
        # Try Gemini API first
        if model:
            try:
                prompt = f"""You are a professional translator specializing in Indian languages.
Translate the following text from {source_lang_name} to {target_lang_name}.
Provide ONLY the translated text, nothing else. Do not include explanations or notes.

Text to translate: "{text}"

Translated text:"""
                
                response = model.generate_content(prompt)
                translated_text = response.text.strip()
                
                print(f"✓ Translation successful via Gemini: {source_lang_name} -> {target_lang_name}")
                
                return jsonify({
                    'success': True,
                    'translated_text': translated_text,
                    'source_language': source_lang_name,
                    'target_language': target_lang_name,
                    'method': 'gemini'
                })
            except Exception as e:
                print(f"Gemini API error: {e}")
                # Fall through to fallback method
        
        # Fallback: Use MyMemory API (free translation service)
        import urllib.parse
        import urllib.request
        import json as json_module
        
        # Convert language codes for MyMemory API
        mymemory_map = {
            'en': 'en-US',
            'hi': 'hi',
            'mr': 'mr',
            'gu': 'gu',
            'ta': 'ta',
            'te': 'te',
            'kn': 'kn',
            'ml': 'ml'
        }
        
        sourceLang = mymemory_map.get(source_language, 'en-US')
        targetLang = mymemory_map.get(target_language, 'en-US')
        
        try:
            encodedText = urllib.parse.quote(text)
            url = f"https://api.mymemory.translated.net/get?q={encodedText}&langpair={sourceLang}|{targetLang}"
            
            print(f"Attempting fallback translation: {url}")
            
            with urllib.request.urlopen(url, timeout=5) as response:
                result_data = json_module.loads(response.read().decode('utf-8'))
                
            if result_data.get('responseStatus') == 200:
                translated_text = result_data['responseData']['translatedText']
                print(f"✓ Translation successful via MyMemory: {source_lang_name} -> {target_lang_name}")
                
                return jsonify({
                    'success': True,
                    'translated_text': translated_text,
                    'source_language': source_lang_name,
                    'target_language': target_lang_name,
                    'method': 'mymemory'
                })
            else:
                error_msg = result_data.get('responseStatus', 'Unknown error')
                print(f"MyMemory API error: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Translation service temporarily unavailable. Please try again.'
                }), 503
        except urllib.error.URLError as url_error:
            print(f"Network error in translation: {url_error}")
            return jsonify({
                'success': False,
                'error': 'No internet connection. Please check your connection and try again.'
      Database is already initialized above, before app routes definexception as fallback_error:
            print(f"Fallback translation error: {fallback_error}")
            return jsonify({
                'success': False,
                'error': f'Translation failed: {str(fallback_error)}. Please try again.'
            }), 500
    
    except Exception as e:
        print(f"Translation endpoint error: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error and display useful information"""
    print(f"500 Error: {error}")
    import traceback
    traceback.print_exc()
    return render_template('500.html', error=str(error)), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found"""
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Database is already initialized above
    # Bind to localhost to avoid browser permission issues when testing on local machine
    # Access the site at http://localhost:5000
    app.run(debug=True, host='127.0.0.1', port=5000)
