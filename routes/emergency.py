from flask import Blueprint, render_template, jsonify, request
from datetime import datetime


emergency_bp = Blueprint(
    "emergency",
    __name__,
    url_prefix="/citizen/emergency"
)


# ============================================================
# EMERGENCY SERVICES
# ============================================================

EMERGENCY_SERVICES = [
    {
        "id": "universal",
        "name": "National Emergency",
        "short_name": "Emergency",
        "number": "112",
        "icon": "🚨",
        "description": "For police, fire, ambulance and other emergency assistance.",
        "priority": "critical"
    },
    {
        "id": "ambulance",
        "name": "Ambulance",
        "short_name": "Ambulance",
        "number": "108",
        "icon": "🚑",
        "description": "Emergency ambulance service.",
        "priority": "critical"
    },
    {
        "id": "fire",
        "name": "Fire & Rescue",
        "short_name": "Fire",
        "number": "101",
        "icon": "🚒",
        "description": "Fire and rescue emergency assistance.",
        "priority": "high"
    },
    {
        "id": "police",
        "name": "Police",
        "short_name": "Police",
        "number": "100",
        "icon": "👮",
        "description": "Police emergency assistance.",
        "priority": "high"
    }
]


# ============================================================
# DISASTER INSTRUCTIONS
# ============================================================

DISASTER_GUIDES = {

    "earthquake": {
        "title": "Earthquake",
        "icon": "🌍",
        "color": "danger",
        "before": [
            "Keep an emergency kit ready.",
            "Know the safest areas in your building.",
            "Secure heavy furniture and objects."
        ],
        "during": [
            "DROP to the ground.",
            "COVER your head and neck.",
            "HOLD ON until shaking stops.",
            "Stay away from windows and glass.",
            "Do not use elevators."
        ],
        "after": [
            "Move carefully to a safe open area.",
            "Check yourself and others for injuries.",
            "Stay away from damaged buildings.",
            "Expect possible aftershocks.",
            "Follow official instructions."
        ]
    },

    "flood": {
        "title": "Flood",
        "icon": "🌊",
        "color": "warning",
        "before": [
            "Move important documents and medicines to a higher place.",
            "Keep drinking water stored safely.",
            "Charge your phone and power bank."
        ],
        "during": [
            "Move to higher ground.",
            "Do not walk or drive through moving flood water.",
            "Stay away from electrical equipment.",
            "Follow evacuation instructions.",
            "Keep emergency documents with you."
        ],
        "after": [
            "Avoid contaminated flood water.",
            "Do not enter damaged buildings.",
            "Use safe drinking water only.",
            "Watch for electrical hazards.",
            "Follow local authority instructions."
        ]
    },

    "landslide": {
        "title": "Landslide",
        "icon": "⛰️",
        "color": "danger",
        "before": [
            "Monitor local warnings during heavy rainfall.",
            "Know evacuation routes.",
            "Keep emergency supplies ready."
        ],
        "during": [
            "Move away from slopes and unstable ground.",
            "Leave the danger zone immediately if instructed.",
            "Avoid river channels and low-lying areas.",
            "Do not approach an active landslide."
        ],
        "after": [
            "Stay away from the slide area.",
            "Watch for additional landslides.",
            "Report blocked roads or injuries.",
            "Wait for authorities before returning."
        ]
    },

    "fire": {
        "title": "Fire",
        "icon": "🔥",
        "color": "danger",
        "before": [
            "Keep fire exits clear.",
            "Know the location of extinguishers.",
            "Avoid overloaded electrical sockets."
        ],
        "during": [
            "Raise the alarm.",
            "Call emergency services.",
            "Leave through the safest exit.",
            "Stay low if there is smoke.",
            "Never use an elevator during a fire."
        ],
        "after": [
            "Do not re-enter until authorities declare the building safe.",
            "Stay away from damaged electrical systems.",
            "Get medical attention for burns or smoke exposure."
        ]
    },

    "cyclone": {
        "title": "Cyclone",
        "icon": "🌀",
        "color": "warning",
        "before": [
            "Secure loose outdoor objects.",
            "Charge phones and emergency power banks.",
            "Store drinking water and essential medicines.",
            "Know your nearest shelter."
        ],
        "during": [
            "Stay indoors and away from windows.",
            "Do not go outside during the eye of the storm.",
            "Follow official evacuation orders.",
            "Keep emergency communication devices ready."
        ],
        "after": [
            "Avoid fallen power lines.",
            "Avoid flooded roads.",
            "Do not touch damaged electrical equipment.",
            "Return only after official clearance."
        ]
    },

    "heatwave": {
        "title": "Heatwave",
        "icon": "☀️",
        "color": "warning",
        "before": [
            "Keep drinking water available.",
            "Avoid unnecessary outdoor activity during peak heat.",
            "Wear light and loose clothing."
        ],
        "during": [
            "Move to a cool or shaded location.",
            "Drink water regularly.",
            "Avoid strenuous activity during peak heat.",
            "Check on elderly people and vulnerable persons."
        ],
        "after": [
            "Continue hydration.",
            "Rest in a cool environment.",
            "Seek urgent medical help for confusion, fainting or severe deterioration."
        ]
    }
}


# ============================================================
# EMERGENCY CHECKLIST
# ============================================================

EMERGENCY_CHECKLIST = [
    {
        "id": "phone",
        "icon": "📱",
        "title": "Phone charged",
        "description": "Keep your phone and power bank available."
    },
    {
        "id": "water",
        "icon": "💧",
        "title": "Drinking water",
        "description": "Keep safe drinking water ready."
    },
    {
        "id": "medicine",
        "icon": "💊",
        "title": "Essential medicines",
        "description": "Keep necessary medicines and prescriptions."
    },
    {
        "id": "documents",
        "icon": "📄",
        "title": "Important documents",
        "description": "Keep identity and emergency documents protected."
    },
    {
        "id": "torch",
        "icon": "🔦",
        "title": "Torch",
        "description": "Keep a working torch and spare batteries."
    },
    {
        "id": "food",
        "icon": "🥫",
        "title": "Emergency food",
        "description": "Keep basic non-perishable food available."
    },
    {
        "id": "firstaid",
        "icon": "🩹",
        "title": "First-aid kit",
        "description": "Keep basic first-aid supplies accessible."
    },
    {
        "id": "contact",
        "icon": "👨‍👩‍👧",
        "title": "Emergency contacts",
        "description": "Keep important family and emergency contacts saved."
    }
]


# ============================================================
# ROUTES
# ============================================================

@emergency_bp.route("/")
def emergency_center():
    return render_template(
        "emergency.html",
        services=EMERGENCY_SERVICES,
        guides=DISASTER_GUIDES,
        checklist=EMERGENCY_CHECKLIST
    )


# ============================================================
# API — EMERGENCY SERVICES
# ============================================================

@emergency_bp.route("/api/services")
def emergency_services():

    return jsonify({
        "success": True,
        "services": EMERGENCY_SERVICES,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    })


# ============================================================
# API — DISASTER GUIDE
# ============================================================

@emergency_bp.route("/api/guides")
def disaster_guides():

    disaster_type = request.args.get(
        "type",
        "",
        type=str
    ).strip().lower()

    if disaster_type:

        guide = DISASTER_GUIDES.get(
            disaster_type
        )

        if not guide:

            return jsonify({
                "success": False,
                "error": "guide_not_found"
            }), 404

        return jsonify({
            "success": True,
            "type": disaster_type,
            "guide": guide
        })

    return jsonify({
        "success": True,
        "guides": DISASTER_GUIDES
    })


# ============================================================
# API — CHECKLIST
# ============================================================

@emergency_bp.route("/api/checklist")
def emergency_checklist():

    return jsonify({
        "success": True,
        "items": EMERGENCY_CHECKLIST
    })


# ============================================================
# API — LOCATION SEARCH URLS
# ============================================================

@emergency_bp.route("/api/location-links")
def location_links():

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:

        return jsonify({
            "success": False,
            "error": "coordinates_required"
        }), 400

    if not (-90 <= lat <= 90):

        return jsonify({
            "success": False,
            "error": "invalid_latitude"
        }), 400

    if not (-180 <= lon <= 180):

        return jsonify({
            "success": False,
            "error": "invalid_longitude"
        }), 400

    coordinate = f"{lat},{lon}"

    return jsonify({
        "success": True,

        "coordinates": {
            "latitude": lat,
            "longitude": lon
        },

        "links": {
            "hospital":
                f"https://www.google.com/maps/search/hospital/@{coordinate},14z",

            "pharmacy":
                f"https://www.google.com/maps/search/pharmacy/@{coordinate},14z",

            "police":
                f"https://www.google.com/maps/search/police/@{coordinate},14z",

            "fire_station":
                f"https://www.google.com/maps/search/fire+station/@{coordinate},14z",

            "shelter":
                f"https://www.google.com/maps/search/emergency+shelter/@{coordinate},14z",

            "navigation":
                f"https://www.google.com/maps/@{coordinate},15z"
        }
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@emergency_bp.route("/api/health")
def emergency_health():

    return jsonify({
        "success": True,
        "module": "Emergency Response Center",
        "status": "operational"
    })
