from flask import Blueprint, request, jsonify, session
from models import db, User, EmailVerification
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

# Explicit .env path for Termux/Python compatibility
load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".env"
    )
)

auth_bp = Blueprint("auth", __name__)


def is_strong_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    if not re.search(r"[^A-Za-z0-9]", password):
        return False

    return True


def send_otp_email(email, otp):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username)

    if not smtp_username or not smtp_password:
        raise RuntimeError("Email service is not configured")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your DisasterShield AI Verification Code"
    message["From"] = f"DisasterShield AI <{smtp_from}>"
    message["To"] = email

    text_body = f"""
DisasterShield AI

Your verification code is: {otp}

This code will expire in 10 minutes.

If you did not request this code, you can safely ignore this email.

This is an automated email. Please do not reply.
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DisasterShield AI Verification</title>
</head>

<body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">

<div style="max-width:620px;margin:30px auto;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 8px 30px rgba(20,40,80,0.10);">

    <div style="background:linear-gradient(135deg,#0b1f3a,#1769aa);padding:28px 30px;color:white;">
        <div style="font-size:25px;font-weight:700;">
            🛡️ DisasterShield <span style="color:#67d5ff;">AI</span>
        </div>
        <div style="font-size:13px;margin-top:6px;color:#d7ecf8;">
            Smarter Alerts. Safer Communities.
        </div>
    </div>

    <div style="padding:35px 30px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#14233b;">
            Verify Your Email
        </div>

        <p style="font-size:15px;line-height:1.6;color:#667085;margin-top:12px;">
            Use the verification code below to complete your
            DisasterShield AI registration and secure your account.
        </p>

        <div style="margin:28px auto;padding:22px;background:#eef8ff;border:1px solid #ccecff;border-radius:14px;max-width:330px;">
            <div style="font-size:12px;font-weight:700;letter-spacing:2px;color:#3788b8;">
                YOUR VERIFICATION CODE
            </div>

            <div style="font-size:38px;font-weight:800;letter-spacing:8px;color:#102a43;margin-top:12px;">
                {otp}
            </div>
        </div>

        <p style="font-size:14px;color:#667085;">
            ⏱️ This code will expire in
            <strong style="color:#1677b8;">10 minutes</strong>.
        </p>

        <div style="margin-top:25px;padding:16px;background:#f8fafc;border-radius:12px;text-align:left;font-size:13px;line-height:1.6;color:#667085;">
            🔒 <strong style="color:#344054;">Security reminder:</strong>
            Never share this verification code with anyone.
            If you did not request this code, you can safely ignore this email.
        </div>
    </div>

    <div style="background:#101f35;padding:24px 30px;color:#d8e3ef;text-align:center;">
        <div style="font-size:17px;font-weight:700;color:white;">
            🛡️ DisasterShield AI
        </div>

        <div style="font-size:12px;margin-top:7px;">
            Together for a safer and more resilient tomorrow.
        </div>

        <div style="font-size:11px;margin-top:18px;color:#91a4b8;">
            This is an automated email. Please do not reply.
        </div>
    </div>

</div>

</body>
</html>
"""

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, email, message.as_string())


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    if not is_strong_password(password):
        return jsonify({
            "success": False,
            "message": "Please enter a strong password. Use at least 8 characters with uppercase, lowercase, number and special character."
        }), 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    try:
        otp = str(random.randint(100000, 999999))

        # Remove any previous pending verification
        EmailVerification.query.filter_by(email=email).delete(
            synchronize_session=False
        )

        verification = EmailVerification(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            otp_hash=generate_password_hash(otp),
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )

        db.session.add(verification)
        db.session.commit()

        try:
            send_otp_email(email, otp)
        except Exception as email_error:
            db.session.rollback()
            print("EMAIL ERROR:", email_error)

            return jsonify({
                "success": False,
                "message": "Unable to send verification email. Please try again later."
            }), 500

        return jsonify({
            "success": True,
            "message": "Verification code sent to your email."
        }), 200

    except Exception as e:
        db.session.rollback()
        print("REGISTER ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Registration failed. Please try again."
        }), 500


@auth_bp.route("/api/auth/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip()

    if not email or not otp:
        return jsonify({
            "success": False,
            "message": "Email and OTP are required."
        }), 400

    verification = EmailVerification.query.filter_by(email=email).first()

    if not verification:
        return jsonify({
            "success": False,
            "message": "No pending verification found. Please register again."
        }), 404

    if datetime.utcnow() > verification.expires_at:
        db.session.delete(verification)
        db.session.commit()

        return jsonify({
            "success": False,
            "message": "OTP has expired. Please request a new OTP."
        }), 400

    if not check_password_hash(verification.otp_hash, otp):
        return jsonify({
            "success": False,
            "message": "Invalid OTP. Please check the code and try again."
        }), 400

    try:
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            db.session.delete(verification)
            db.session.commit()

            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 409

        user = User(
            name=verification.name,
            email=verification.email,
            password_hash=verification.password_hash,
            role="citizen"
        )

        db.session.add(user)
        db.session.delete(verification)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Email verified successfully. Your account has been created."
        }), 201

    except Exception as e:
        db.session.rollback()
        print("VERIFY ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Account creation failed. Please try again."
        }), 500


@auth_bp.route("/api/auth/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    verification = EmailVerification.query.filter_by(email=email).first()

    if not verification:
        return jsonify({
            "success": False,
            "message": "No pending registration found for this email."
        }), 404

    try:
        otp = str(random.randint(100000, 999999))

        verification.otp_hash = generate_password_hash(otp)
        verification.expires_at = datetime.utcnow() + timedelta(minutes=10)

        db.session.commit()

        try:
            send_otp_email(email, otp)
        except Exception as email_error:
            db.session.rollback()
            print("EMAIL ERROR:", email_error)

            return jsonify({
                "success": False,
                "message": "Unable to send verification email. Please try again later."
            }), 500

        return jsonify({
            "success": True,
            "message": "A new verification code has been sent."
        }), 200

    except Exception as e:
        db.session.rollback()
        print("RESEND ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to resend OTP. Please try again."
        }), 500


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    session["user_id"] = user.id
    session["role"] = user.role

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
def me():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    user = User.query.get(user_id)

    if not user:
        session.clear()

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 200
