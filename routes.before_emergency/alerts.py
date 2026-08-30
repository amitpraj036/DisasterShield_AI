from datetime import datetime

from flask import Blueprint, jsonify, request

from models import db, Alert
from services.auth_service import admin_required, get_current_user


alerts_bp = Blueprint(
    "alerts",
    __name__,
    url_prefix="/api/alerts"
)


@alerts_bp.route("", methods=["GET"])
def get_alerts():
    alerts = (
        Alert.query
        .order_by(Alert.created_at.desc())
        .all()
    )

    result = []

    for alert in alerts:
        result.append({
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "radius_km": alert.radius_km,
            "source": alert.source,
            "status": alert.status,
            "created_by": alert.created_by,
            "created_at": alert.created_at.isoformat(),
            "expires_at": (
                alert.expires_at.isoformat()
                if alert.expires_at
                else None
            )
        })

    return jsonify({
        "success": True,
        "count": len(result),
        "alerts": result
    })


@alerts_bp.route("", methods=["POST"])
@admin_required
def create_alert():

    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    message = str(data.get("message", "")).strip()
    alert_type = str(data.get("alert_type", "")).strip().lower()
    severity = str(
        data.get("severity", "moderate")
    ).strip().lower()

    if not title:
        return jsonify({
            "success": False,
            "message": "Title is required"
        }), 400

    if not message:
        return jsonify({
            "success": False,
            "message": "Message is required"
        }), 400

    if not alert_type:
        return jsonify({
            "success": False,
            "message": "Alert type is required"
        }), 400

    allowed_severity = {
        "low",
        "moderate",
        "high",
        "critical"
    }

    if severity not in allowed_severity:
        return jsonify({
            "success": False,
            "message": "Invalid severity"
        }), 400

    admin = get_current_user()

    alert = Alert(
        title=title,
        message=message,
        alert_type=alert_type,
        severity=severity,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        radius_km=data.get("radius_km"),
        source=data.get("source", "admin"),
        status="active",
        created_by=admin.id,
        expires_at=None
    )

    db.session.add(alert)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Alert created successfully",
        "alert": {
            "id": alert.id,
            "title": alert.title,
            "severity": alert.severity,
            "status": alert.status,
            "source": alert.source,
            "created_by": alert.created_by,
            "created_at": alert.created_at.isoformat()
        }
    }), 201


@alerts_bp.route("/<int:alert_id>/deactivate", methods=["POST"])
@admin_required
def deactivate_alert(alert_id):

    alert = db.session.get(
        Alert,
        alert_id
    )

    if not alert:
        return jsonify({
            "success": False,
            "message": "Alert not found"
        }), 404

    if alert.status == "inactive":
        return jsonify({
            "success": False,
            "message": "Alert is already inactive"
        }), 409

    alert.status = "inactive"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Alert deactivated successfully",
        "alert": {
            "id": alert.id,
            "status": alert.status
        }
    })
