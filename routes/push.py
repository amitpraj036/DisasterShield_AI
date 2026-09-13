from flask import Blueprint, jsonify, request
from models import db, PushSubscription
from services.auth_service import login_required, get_current_user

push_bp = Blueprint("push", __name__, url_prefix="/api/push")


@push_bp.route("/public-key", methods=["GET"])
@login_required
def public_key():
    from pathlib import Path
    import base64
    import os
    from cryptography.hazmat.primitives import serialization

    base_dir = Path(__file__).resolve().parent.parent

    public_key_file = os.getenv(
        "VAPID_PUBLIC_KEY_FILE",
        ".vapid_public.pem"
    )

    public_key_path = Path(public_key_file)

    if not public_key_path.is_absolute():
        public_key_path = base_dir / public_key_path

    if not public_key_path.exists():
        return jsonify({
            "success": False,
            "message": "VAPID public key not found."
        }), 500

    try:
        public_key = serialization.load_pem_public_key(
            public_key_path.read_bytes()
        )

        raw_key = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

        encoded_key = base64.urlsafe_b64encode(
            raw_key
        ).rstrip(b"=").decode("ascii")

        return jsonify({
            "success": True,
            "public_key": encoded_key
        })

    except Exception as exc:
        print(f"VAPID public key error: {exc}")

        return jsonify({
            "success": False,
            "message": "Unable to load VAPID public key."
        }), 500


@push_bp.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    user = get_current_user()

    data = request.get_json(silent=True) or {}

    endpoint = data.get("endpoint")
    keys = data.get("keys") or {}

    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        return jsonify({
            "success": False,
            "message": "Invalid push subscription."
        }), 400

    subscription = PushSubscription.query.filter_by(
        endpoint=endpoint
    ).first()

    if subscription:
        subscription.user_id = user.id
        subscription.p256dh = p256dh
        subscription.auth = auth
        subscription.enabled = True
    else:
        subscription = PushSubscription(
            user_id=user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            enabled=True
        )
        db.session.add(subscription)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Push notifications enabled."
    })


@push_bp.route("/unsubscribe", methods=["POST"])
@login_required
def unsubscribe():
    user = get_current_user()

    data = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint")

    if endpoint:
        subscription = PushSubscription.query.filter_by(
            user_id=user.id,
            endpoint=endpoint
        ).first()

        if subscription:
            subscription.enabled = False
            db.session.commit()

    return jsonify({
        "success": True,
        "message": "Push notifications disabled."
    })
