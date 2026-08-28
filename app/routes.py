import math
from flask import request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Appointment

# Jackie Cutz Salon Coordinates (Update lat/lng to exact salon address if needed)
SALON_LAT = 29.7604
SALON_LNG = -95.3698
GEOFENCE_RADIUS_METERS = 3.05  # Exactly 10 feet (3.05 meters)

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@main_bp.route('/api/geofence-checkin', methods=['POST'])
@login_required
def geofence_checkin():
    data = request.get_json() or {}
    user_lat = data.get('lat')
    user_lng = data.get('lng')

    if user_lat is None or user_lng is None:
        return jsonify({'status': 'error', 'message': 'Missing coordinates'}), 400

    distance = calculate_haversine_distance(float(user_lat), float(user_lng), SALON_LAT, SALON_LNG)

    if distance <= GEOFENCE_RADIUS_METERS:
        # Find today's active booked appointment for this logged-in client
        appt = Appointment.query.filter_by(
            user_id=current_user.id,
            status='booked'
        ).first()

        if appt:
            appt.status = 'checked_in'
            db.session.commit()
            return jsonify({
                'status': 'checked_in',
                'message': 'Auto-detected within 10 feet! You are checked in.',
                'distance_feet': round(distance * 3.28084, 1)
            }), 200

        return jsonify({
            'status': 'already_checked_in_or_no_appt',
            'distance_feet': round(distance * 3.28084, 1)
        }), 200

    return jsonify({
        'status': 'outside_geofence',
        'distance_feet': round(distance * 3.28084, 1)
    }), 200