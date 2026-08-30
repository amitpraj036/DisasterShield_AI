from flask import Blueprint, jsonify, request

from models import db, RiskData
from services.auth_service import admin_required


risk_bp = Blueprint(
    "risk",
    __name__,
    url_prefix="/api/risk"
)


def calculate_risk_score(
    rainfall_mm=None,
    soil_moisture=None,
    slope_degree=None,
    historical_landslides=0
):
    """
    Explainable baseline risk engine.

    This is NOT the final ML model.
    It provides a transparent baseline until
    enough historical labelled data is available.
    """

    score = 0.0

    # Rainfall contribution: maximum 35 points
    if rainfall_mm is not None:
        rainfall_score = min(
            max(rainfall_mm / 150.0 * 35.0, 0.0),
            35.0
        )
        score += rainfall_score

    # Soil moisture contribution: maximum 25 points
    if soil_moisture is not None:
        moisture_score = min(
            max(soil_moisture / 100.0 * 25.0, 0.0),
            25.0
        )
        score += moisture_score

    # Slope contribution: maximum 25 points
    if slope_degree is not None:
        slope_score = min(
            max(slope_degree / 45.0 * 25.0, 0.0),
            25.0
        )
        score += slope_score

    # Historical landslide contribution: maximum 15 points
    historical_score = min(
        max(historical_landslides / 5.0 * 15.0, 0.0),
        15.0
    )
    score += historical_score

    score = round(min(max(score, 0.0), 100.0), 2)

    if score >= 75:
        level = "critical"
    elif score >= 50:
        level = "high"
    elif score >= 25:
        level = "moderate"
    else:
        level = "low"

    return score, level


@risk_bp.route("", methods=["GET"])
def get_risk_data():

    records = (
        RiskData.query
        .order_by(RiskData.recorded_at.desc())
        .all()
    )

    result = []

    for record in records:
        result.append({
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

    return jsonify({
        "success": True,
        "count": len(result),
        "data": result
    })


@risk_bp.route("", methods=["POST"])
@admin_required
def create_risk_data():

    data = request.get_json(silent=True) or {}

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])

    except (KeyError, TypeError, ValueError):
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

    def optional_float(key):

        value = data.get(key)

        if value is None or value == "":
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            raise ValueError(key)

    try:
        rainfall_mm = optional_float("rainfall_mm")
        soil_moisture = optional_float("soil_moisture")
        slope_degree = optional_float("slope_degree")
        elevation = optional_float("elevation")

    except ValueError as error:

        return jsonify({
            "success": False,
            "message": f"Invalid value for {error.args[0]}"
        }), 400

    try:
        historical_landslides = int(
            data.get("historical_landslides", 0)
        )

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "historical_landslides must be an integer"
        }), 400

    if historical_landslides < 0:

        return jsonify({
            "success": False,
            "message": "historical_landslides cannot be negative"
        }), 400

    source = str(
        data.get("source", "manual")
    ).strip().lower()

    if not source:
        source = "manual"

    # Calculate baseline risk
    risk_score, risk_level = calculate_risk_score(
        rainfall_mm=rainfall_mm,
        soil_moisture=soil_moisture,
        slope_degree=slope_degree,
        historical_landslides=historical_landslides
    )

    # IMPORTANT:
    # Always create a NEW record.
    # Existing historical observations are never overwritten.
    record = RiskData(
        latitude=latitude,
        longitude=longitude,
        rainfall_mm=rainfall_mm,
        soil_moisture=soil_moisture,
        slope_degree=slope_degree,
        elevation=elevation,
        historical_landslides=historical_landslides,
        risk_score=risk_score,
        risk_level=risk_level,
        source=source
    )

    db.session.add(record)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Risk data recorded successfully",
        "data": {
            "id": record.id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "risk_score": record.risk_score,
            "risk_level": record.risk_level,
            "source": record.source,
            "recorded_at": record.recorded_at.isoformat()
        }
    }), 201
