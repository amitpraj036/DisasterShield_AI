from flask import Blueprint, jsonify, render_template
from datetime import datetime
from models import db

from models import RiskData, DisasterReport, Alert


gis_bp = Blueprint(
    "gis",
    __name__,
    url_prefix="/api/gis"
)


@gis_bp.route("/map", methods=["GET"])
def map_dashboard():
    return render_template("map.html")


@gis_bp.route("/map-data", methods=["GET"])
def get_map_data():

    risk_records = (
        RiskData.query
        .order_by(RiskData.recorded_at.desc())
        .all()
    )

    reports = (
        DisasterReport.query
        .filter_by(status="verified")
        .order_by(DisasterReport.created_at.desc())
        .all()
    )

    now = datetime.utcnow()
    expired_alerts = (
        Alert.query
        .filter(
            Alert.status == "active",
            Alert.expires_at.isnot(None),
            Alert.expires_at <= now
        )
        .all()
    )
    for expired in expired_alerts:
        expired.status = "inactive"
    if expired_alerts:
        db.session.commit()

    alerts = (
        Alert.query
        .filter_by(status="active")
        .order_by(Alert.created_at.desc())
        .all()
    )

    risk_data = []

    for record in risk_records:
        risk_data.append({
            "id": record.id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "rainfall_mm": record.rainfall_mm,
            "soil_moisture": record.soil_moisture,
            "slope_degree": record.slope_degree,
            "elevation": record.elevation,
            "historical_landslides": record.historical_landslides,
            "risk_score": record.risk_score,
            "risk_level": record.risk_level,
            "source": record.source,
            "recorded_at": record.recorded_at.isoformat()
        })

    report_data = []

    for report in reports:
        report_data.append({
            "id": report.id,
            "disaster_type": report.disaster_type,
            "description": report.description,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "severity": report.severity,
            "status": report.status,
            "created_at": report.created_at.isoformat()
        })

    alert_data = []

    for alert in alerts:
        alert_data.append({
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
            "created_at": alert.created_at.isoformat(),
            "expires_at": (
                alert.expires_at.isoformat()
                if alert.expires_at
                else None
            )
        })

    return jsonify({
        "success": True,
        "risk_data": risk_data,
        "verified_reports": report_data,
        "active_alerts": alert_data
    })
