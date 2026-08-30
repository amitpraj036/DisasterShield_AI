from flask import Blueprint, request, jsonify

from models import db, DisasterReport
from services.auth_service import login_required, get_current_user


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/api/reports"
)


ALLOWED_DISASTER_TYPES = {
    "flood",
    "landslide",
    "earthquake",
    "fire",
    "cyclone",
    "storm",
    "drought",
    "other"
}

ALLOWED_SEVERITIES = {
    "low",
    "moderate",
    "high",
    "critical"
}


@reports_bp.route("", methods=["POST"])
@login_required
def create_report():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400

    disaster_type = data.get(
        "disaster_type",
        ""
    ).strip().lower()

    description = data.get(
        "description",
        ""
    ).strip()

    severity = data.get(
        "severity",
        "moderate"
    ).strip().lower()

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not disaster_type:
        return jsonify({
            "success": False,
            "message": "Disaster type is required"
        }), 400

    if disaster_type not in ALLOWED_DISASTER_TYPES:
        return jsonify({
            "success": False,
            "message": "Invalid disaster type"
        }), 400

    if not description:
        return jsonify({
            "success": False,
            "message": "Description is required"
        }), 400

    if len(description) < 10:
        return jsonify({
            "success": False,
            "message": "Description must contain at least 10 characters"
        }), 400

    if severity not in ALLOWED_SEVERITIES:
        return jsonify({
            "success": False,
            "message": "Invalid severity"
        }), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Valid latitude and longitude are required"
        }), 400

    if not -90 <= latitude <= 90:
        return jsonify({
            "success": False,
            "message": "Latitude must be between -90 and 90"
        }), 400

    if not -180 <= longitude <= 180:
        return jsonify({
            "success": False,
            "message": "Longitude must be between -180 and 180"
        }), 400

    user = get_current_user()

    report = DisasterReport(
        user_id=user.id,
        disaster_type=disaster_type,
        description=description,
        latitude=latitude,
        longitude=longitude,
        severity=severity,
        status="pending"
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Disaster report submitted successfully",
        "report": {
            "id": report.id,
            "disaster_type": report.disaster_type,
            "severity": report.severity,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "status": report.status,
            "created_at": report.created_at.isoformat()
        }
    }), 201


@reports_bp.route("/my", methods=["GET"])
@login_required
def my_reports():

    user = get_current_user()

    reports = (
        DisasterReport.query
        .filter_by(user_id=user.id)
        .order_by(DisasterReport.created_at.desc())
        .all()
    )

    result = []

    for report in reports:
        result.append({
            "id": report.id,
            "disaster_type": report.disaster_type,
            "description": report.description,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "severity": report.severity,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat()
        })

    return jsonify({
        "success": True,
        "count": len(result),
        "reports": result
    })
