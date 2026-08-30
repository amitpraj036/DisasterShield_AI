from functools import wraps

from flask import jsonify, session
from models import db, User


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(User, user_id)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if user is None:
            session.clear()

            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if user is None:
            session.clear()

            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401

        if user.role != "admin":
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        return f(*args, **kwargs)

    return decorated_function
