from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

from flask import Blueprint, jsonify, request

from models import db, Alert, CitizenLocation, SafetyAlertEvent
from services.auth_service import login_required, get_current_user
from services.notification_service import send_safety_alert_email


safety_bp = Blueprint("safety", __name__, url_prefix="/api/safety")

# Do not spam a citizen with the same alert repeatedly.
ALERT_COOLDOWN_HOURS = 6
AUTOMATIC_SEVERITIES = {"high", "critical"}


def haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))


def active_alerts_nearby(latitude, longitude):
    now = datetime.utcnow()
    alerts = (
        Alert.query
        .filter(Alert.status == "active")
        .filter(Alert.severity.in_(AUTOMATIC_SEVERITIES))
        .all()
    )

    matches = []
    for alert in alerts:
        if alert.expires_at and alert.expires_at <= now:
            continue
        if alert.latitude is None or alert.longitude is None or not alert.radius_km:
            continue

        distance = haversine_km(
            latitude, longitude, alert.latitude, alert.longitude
        )
        if distance <= alert.radius_km:
            matches.append((alert, distance))

    return matches


def serialize_match(alert, distance_km, email_sent=False):
    return {
        "id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "latitude": alert.latitude,
        "longitude": alert.longitude,
        "radius_km": alert.radius_km,
        "distance_km": round(distance_km, 2),
        "email_sent": email_sent,
    }


@safety_bp.route("/preferences", methods=["GET", "POST"])
@login_required
def safety_preferences():
    user = get_current_user()
    if user.role != "citizen":
        return jsonify({"success": False, "message": "Citizen access required"}), 403

    location = CitizenLocation.query.filter_by(user_id=user.id).first()

    if request.method == "GET":
        return jsonify({
            "success": True,
            "tracking_enabled": bool(location and location.tracking_enabled),
        })

    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("tracking_enabled"))

    if not location:
        # Location is required only when tracking is first enabled.
        if enabled:
            return jsonify({
                "success": False,
                "message": "Please share your location first to enable safety alerts."
            }), 400
        return jsonify({"success": True, "tracking_enabled": False})

    location.tracking_enabled = enabled
    db.session.commit()

    return jsonify({
        "success": True,
        "tracking_enabled": enabled,
        "message": "Location safety alerts enabled." if enabled else "Location safety alerts disabled."
    })


@safety_bp.route("/location", methods=["POST"])
@login_required
def update_location_and_check():
    user = get_current_user()
    if user.role != "citizen":
        return jsonify({"success": False, "message": "Citizen access required"}), 403

    data = request.get_json(silent=True) or {}

    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
        accuracy = data.get("accuracy")
        accuracy = float(accuracy) if accuracy not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Valid latitude and longitude are required."}), 400

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return jsonify({"success": False, "message": "Invalid location coordinates."}), 400

    location = CitizenLocation.query.filter_by(user_id=user.id).first()
    if not location:
        location = CitizenLocation(user_id=user.id, latitude=latitude, longitude=longitude)
        db.session.add(location)

    location.latitude = latitude
    location.longitude = longitude
    location.accuracy_m = accuracy
    location.tracking_enabled = True
    location.updated_at = datetime.utcnow()
    db.session.commit()

    matches = active_alerts_nearby(latitude, longitude)
    triggered = []
    now = datetime.utcnow()
    cooldown_cutoff = now - timedelta(hours=ALERT_COOLDOWN_HOURS)

    for alert, distance_km in matches:
        event = SafetyAlertEvent.query.filter_by(
            user_id=user.id, alert_id=alert.id
        ).first()

        email_sent = False
        should_notify = event is None or event.notified_at < cooldown_cutoff

        if should_notify:
            if event is None:
                event = SafetyAlertEvent(
                    user_id=user.id,
                    alert_id=alert.id,
                    distance_km=distance_km,
                    email_sent=False,
                    notified_at=now,
                )
                db.session.add(event)
            else:
                event.distance_km = distance_km
                event.notified_at = now
                event.email_sent = False

            try:
                send_safety_alert_email(user, alert, distance_km)
                event.email_sent = True
                email_sent = True
            except Exception as email_error:
                # Keep the location check usable even if SMTP is temporarily unavailable.
                print("SAFETY ALERT EMAIL ERROR:", email_error)

            db.session.commit()
        else:
            email_sent = bool(event.email_sent)

        triggered.append(serialize_match(alert, distance_km, email_sent))

    return jsonify({
        "success": True,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy_m": accuracy,
        },
        "inside_danger_zone": bool(matches),
        "alerts": triggered,
        "cooldown_hours": ALERT_COOLDOWN_HOURS,
    })
