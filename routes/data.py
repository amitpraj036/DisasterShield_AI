from datetime import datetime
from flask import Blueprint, jsonify, request
from models import db, RiskData, DataSource


data_bp = Blueprint(
    "data",
    __name__,
    url_prefix="/api/data"
)


ALLOWED_SOURCE_TYPES = {
    "rainfall",
    "soil_moisture",
    "terrain",
    "satellite",
    "historical"
}


@data_bp.route("/sources", methods=["GET"])
def get_sources():
    sources = (
        DataSource.query
        .filter_by(is_active=True)
        .order_by(DataSource.id)
        .all()
    )

    return jsonify({
        "success": True,
        "count": len(sources),
        "sources": [
            {
                "id": source.id,
                "name": source.name,
                "source_type": source.source_type,
                "description": source.description,
                "is_active": source.is_active,
                "created_at": source.created_at.isoformat(),
                "last_sync_at": (
                    source.last_sync_at.isoformat()
                    if source.last_sync_at
                    else None
                )
            }
            for source in sources
        ]
    })


@data_bp.route("/ingest", methods=["POST"])
def ingest_data():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "JSON data is required"
        }), 400

    required_fields = [
        "latitude",
        "longitude",
        "source_type"
    ]

    missing = [
        field for field in required_fields
        if field not in data
    ]

    if missing:
        return jsonify({
            "success": False,
            "message": "Missing required fields",
            "missing": missing
        }), 400

    source_type = str(data["source_type"]).strip().lower()

    if source_type not in ALLOWED_SOURCE_TYPES:
        return jsonify({
            "success": False,
            "message": "Invalid source_type",
            "allowed": sorted(ALLOWED_SOURCE_TYPES)
        }), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Latitude and longitude must be numbers"
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

    def optional_float(field):
        value = data.get(field)

        if value is None or value == "":
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(field)

    try:
        rainfall_mm = optional_float("rainfall_mm")
        soil_moisture = optional_float("soil_moisture")
        slope_degree = optional_float("slope_degree")
        elevation = optional_float("elevation")

        historical_landslides = data.get(
            "historical_landslides",
            0
        )

        if historical_landslides is None:
            historical_landslides = 0

        historical_landslides = int(historical_landslides)

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": f"Invalid numeric value for {error.args[0]}"
        }), 400

    if historical_landslides < 0:
        return jsonify({
            "success": False,
            "message": "historical_landslides cannot be negative"
        }), 400

    source = (
        DataSource.query
        .filter_by(source_type=source_type, is_active=True)
        .first()
    )

    if not source:
        return jsonify({
            "success": False,
            "message": "No active data source configured",
            "source_type": source_type
        }), 400

    # IMPORTANT:
    # Every observation creates a NEW database row.
    # Existing historical data is never overwritten.
    record = RiskData(
        latitude=latitude,
        longitude=longitude,
        rainfall_mm=rainfall_mm,
        soil_moisture=soil_moisture,
        slope_degree=slope_degree,
        elevation=elevation,
        historical_landslides=historical_landslides,
        source=source_type,
        recorded_at=datetime.utcnow()
    )

    db.session.add(record)

    source.last_sync_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to permanently store data"
        }), 500

    return jsonify({
        "success": True,
        "message": "Data ingested and permanently stored",
        "data": {
            "id": record.id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "source": record.source,
            "recorded_at": record.recorded_at.isoformat()
        }
    }), 201
