from datetime import datetime

from flask import Blueprint, jsonify, request

from models import db, DisasterReport, Alert
from services.auth_service import admin_required, get_current_user


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


@admin_bp.route("/reports", methods=["GET"])
@admin_required
def get_reports():

    reports = (
        DisasterReport.query
        .order_by(DisasterReport.created_at.desc())
        .all()
    )

    result = []

    for report in reports:
        result.append({
            "id": report.id,
            "user_id": report.user_id,
            "disaster_type": report.disaster_type,
            "description": report.description,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "severity": report.severity,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "verified_by": report.verified_by,
            "verified_at": (
                report.verified_at.isoformat()
                if report.verified_at
                else None
            ),
            "rejection_reason": report.rejection_reason
        })

    return jsonify({
        "success": True,
        "count": len(result),
        "reports": result
    })


@admin_bp.route("/reports/<int:report_id>/verify", methods=["POST"])
@admin_required
def verify_report(report_id):

    report = db.session.get(
        DisasterReport,
        report_id
    )

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    if report.status == "verified":
        return jsonify({
            "success": False,
            "message": "Report is already verified"
        }), 409

    if report.status == "rejected":
        return jsonify({
            "success": False,
            "message": "Rejected report cannot be verified"
        }), 409

    admin = get_current_user()

    report.status = "verified"
    report.verified_by = admin.id
    report.verified_at = datetime.utcnow()
    report.rejection_reason = None

    automatic_alert = None

    # ---------------------------------------------------------
    # AUTOMATIC ALERT
    # Create an alert automatically for high/critical reports.
    # ---------------------------------------------------------

    if report.severity in {"high", "critical"}:

        existing_alert = (
            Alert.query
            .filter_by(
                status="active",
                alert_type=report.disaster_type,
                latitude=report.latitude,
                longitude=report.longitude
            )
            .first()
        )

        if not existing_alert:

            title = (
                f"{report.severity.title()} "
                f"{report.disaster_type.title()} Alert"
            )

            message = (
                f"A verified {report.severity}-severity "
                f"{report.disaster_type} report has been received. "
                f"Avoid the affected area and follow local "
                f"emergency instructions."
            )

            automatic_alert = Alert(
                title=title,
                message=message,
                alert_type=report.disaster_type,
                severity=report.severity,
                latitude=report.latitude,
                longitude=report.longitude,
                radius_km=5.0,
                source="automatic",
                status="active",
                created_by=admin.id,
                expires_at=None
            )

            db.session.add(automatic_alert)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Report verified successfully",
        "report": {
            "id": report.id,
            "status": report.status,
            "verified_by": report.verified_by,
            "verified_at": report.verified_at.isoformat()
        },
        "automatic_alert": (
            {
                "id": automatic_alert.id,
                "title": automatic_alert.title,
                "severity": automatic_alert.severity,
                "status": automatic_alert.status,
                "source": automatic_alert.source
            }
            if automatic_alert
            else None
        )
    })


@admin_bp.route("/reports/<int:report_id>/reject", methods=["POST"])
@admin_required
def reject_report(report_id):

    report = db.session.get(
        DisasterReport,
        report_id
    )

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    if report.status == "verified":
        return jsonify({
            "success": False,
            "message": "Verified report cannot be rejected"
        }), 409

    if report.status == "rejected":
        return jsonify({
            "success": False,
            "message": "Report is already rejected"
        }), 409

    data = request.get_json(silent=True) or {}

    reason = str(
        data.get("reason", "")
    ).strip()

    if len(reason) < 5:
        return jsonify({
            "success": False,
            "message": "A rejection reason is required"
        }), 400

    admin = get_current_user()

    report.status = "rejected"
    report.verified_by = admin.id
    report.verified_at = datetime.utcnow()
    report.rejection_reason = reason

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Report rejected successfully",
        "report": {
            "id": report.id,
            "status": report.status,
            "verified_by": report.verified_by,
            "verified_at": report.verified_at.isoformat(),
            "rejection_reason": report.rejection_reason
        }
    })
