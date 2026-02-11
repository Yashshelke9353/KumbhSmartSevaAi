from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database.db_manager import DatabaseManager
import math

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

def haversine(lat1, lon1, lat2, lon2):
    # Returns distance in kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Use the same DatabaseManager instance as app (or create new)
_db = DatabaseManager()

@rooms_bp.route('/add', methods=['GET', 'POST'])
def add_room():
    if request.method == 'POST':
        name = request.form.get('name')
        owner_name = request.form.get('owner_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        price = request.form.get('price')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # Basic validation
        if not all([name, owner_name, phone, price, latitude, longitude]):
            flash('Please fill required fields', 'danger')
            return redirect(url_for('rooms.add_room'))

        # Handle photo
        photo = request.files.get('photo')
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"room_{ts}_{filename}"
            upload_dir = os.path.join(current_app.root_path, current_app.config.get('UPLOAD_FOLDER', 'static/uploads'))
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            photo.save(save_path)
            # store relative path
            photo_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), filename)

        # Additional facility fields
        num_rooms = int(request.form.get('num_rooms') or 1)
        water_facility = 1 if request.form.get('water_facility')=='on' else 0
        toilet_available = 1 if request.form.get('toilet_available')=='on' else 0
        bathroom_type = request.form.get('bathroom_type')
        security = request.form.get('security')
        amenities = request.form.get('amenities')

        room_id = _db.add_room(
            name, owner_name, phone, address, float(price), float(latitude), float(longitude), photo_path,
            num_rooms=num_rooms, water_facility=water_facility, toilet_available=toilet_available,
            bathroom_type=bathroom_type, security=security, amenities=amenities
        )
        if room_id:
            flash('Room added successfully', 'success')
            return redirect(url_for('rooms.view_room', room_id=room_id))
        else:
            flash('Failed to add room', 'danger')
    return render_template('rooms_add.html')

@rooms_bp.route('/search', methods=['GET', 'POST'])
def search_rooms():
    results = []
    user_lat = request.values.get('latitude')
    user_lng = request.values.get('longitude')
    budget = request.values.get('budget')
    min_price = request.values.get('min_price')
    max_price = request.values.get('max_price')
    show_all = request.values.get('show_all')
    check_in = request.values.get('check_in')
    check_out = request.values.get('check_out')

    # Perform search when user provided any search parameter (budget, dates or location)
    if request.method == 'POST' or (user_lat and user_lng) or budget or (check_in and check_out):
        # Price filters
        min_p = float(min_price) if min_price else None
        max_p = float(max_price) if max_price else (float(budget) if budget else None)
        include_booked = True if show_all else False
        rooms = _db.search_rooms(min_price=min_p, max_price=max_p, include_booked=include_booked)
        user_lat_f = float(user_lat) if user_lat else None
        user_lng_f = float(user_lng) if user_lng else None

        for r in rooms:
            dist = None
            if user_lat_f is not None and user_lng_f is not None:
                dist = haversine(user_lat_f, user_lng_f, r['latitude'], r['longitude'])
            # check availability if dates provided
            available = True
            if check_in and check_out:
                available = _db.is_room_available(r['id'], check_in, check_out)
            r['distance_km'] = round(dist, 2) if dist is not None else None
            r['available'] = available
        # Rank: available first, then by distance then price
        results = sorted(rooms, key=lambda x: (0 if x['available'] else 1, x.get('distance_km') if x.get('distance_km') is not None else 9999, x['price_per_night']))
    return render_template('rooms_search.html', results=results, latitude=user_lat, longitude=user_lng, budget=budget, check_in=check_in, check_out=check_out)

@rooms_bp.route('/view/<int:room_id>')
def view_room(room_id):
    room = _db.get_room(room_id)
    bookings = _db.bookings_for_room(room_id)
    return render_template('rooms_view.html', room=room, bookings=bookings)

@rooms_bp.route('/book/<int:room_id>', methods=['POST'])
def book_room(room_id):
    visitor_name = request.form.get('visitor_name')
    visitor_phone = request.form.get('visitor_phone')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    aadhaar_path = None

    # Handle Aadhaar upload for booking (optional but recommended)
    aadhaar_file = request.files.get('aadhaar')
    if aadhaar_file and aadhaar_file.filename:
        filename = secure_filename(aadhaar_file.filename)
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"aadhaar_{room_id}_{ts}_{filename}"
        upload_dir = os.path.join(current_app.root_path, current_app.config.get('UPLOAD_FOLDER', 'static/uploads'))
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        aadhaar_file.save(save_path)
        aadhaar_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), filename)

    if not all([visitor_name, visitor_phone, check_in, check_out]):
        flash('Please provide booking details', 'danger')
        return redirect(url_for('rooms.view_room', room_id=room_id))

    # Check availability
    if not _db.is_room_available(room_id, check_in, check_out):
        flash('Room is not available for selected dates', 'danger')
        return redirect(url_for('rooms.view_room', room_id=room_id))

    booking_id = _db.create_booking(room_id, visitor_name, visitor_phone, check_in, check_out, aadhaar_photo_path=aadhaar_path)
    if booking_id:
        flash('Booking confirmed', 'success')
    else:
        flash('Failed to create booking', 'danger')
    return redirect(url_for('rooms.view_room', room_id=room_id))

# Owner routes
@rooms_bp.route('/owner/bookings')
def owner_bookings():
    # Simple listing of all bookings for owners (no auth in this minimal example)
    conn = _db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT b.*, r.name as room_name, r.owner_name FROM bookings b JOIN rooms r ON b.room_id = r.id ORDER BY b.created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    bookings = [dict(r) for r in rows]
    return render_template('owner_bookings.html', bookings=bookings)
