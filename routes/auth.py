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


# =========================================================
# PASSWORD RESET
# =========================================================

from models import PasswordReset


def send_password_reset_email(email, otp):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username)

    if not smtp_username or not smtp_password:
        raise RuntimeError("Email service is not configured")

    message = MIMEMultipart("alternative")

    message["Subject"] = "DisasterShield AI - Password Reset Code"
    message["From"] = f"DisasterShield AI <{smtp_from}>"
    message["To"] = email

    text_body = f"""
DisasterShield AI

Your password reset code is: {otp}

This code will expire in 10 minutes.

If you did not request a password reset, you can safely ignore this email.

This is an automated email. Please do not reply.
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Password Reset - DisasterShield AI</title>
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
            Reset Your Password
        </div>

        <p style="font-size:15px;line-height:1.6;color:#667085;">
            Use the verification code below to securely reset your DisasterShield AI password.
        </p>

        <div style="margin:28px auto;padding:22px;background:#eef8ff;border:1px solid #ccecff;border-radius:14px;max-width:330px;">

            <div style="font-size:12px;font-weight:700;letter-spacing:2px;color:#3788b8;">
                PASSWORD RESET CODE
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

            🔒 <strong style="color:#344054;">
                Security reminder:
            </strong>

            Never share this code with anyone.

            If you did not request a password reset,
            you can safely ignore this email.

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
        server.sendmail(
            smtp_from,
            email,
            message.as_string()
        )


@auth_bp.route("/forgot-password")
def forgot_password_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Forgot Password - DisasterShield AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #0f172a, #1e3a5f);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.card {
    width: 100%;
    max-width: 430px;
    background: white;
    padding: 30px;
    border-radius: 18px;
    box-shadow: 0 20px 50px rgba(0,0,0,.25);
}

.logo {
    text-align: center;
    font-size: 42px;
}

h1 {
    text-align: center;
    color: #0f172a;
    margin: 8px 0;
}

.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 25px;
}

label {
    display: block;
    margin: 14px 0 7px;
    font-weight: bold;
    color: #334155;
}

input {
    width: 100%;
    padding: 13px;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    font-size: 15px;
}

button {
    width: 100%;
    margin-top: 20px;
    padding: 13px;
    border: 0;
    border-radius: 9px;
    background: #2563eb;
    color: white;
    font-size: 15px;
    font-weight: bold;
    cursor: pointer;
}

button:disabled {
    opacity: .6;
}

#message {
    display: none;
    margin-top: 15px;
    padding: 11px;
    border-radius: 8px;
    font-size: 14px;
}

.success {
    display: block !important;
    background: #dcfae6;
    color: #067647;
}

.error {
    display: block !important;
    background: #fee2e2;
    color: #991b1b;
}

.back {
    text-align: center;
    margin-top: 18px;
    font-size: 14px;
}

a {
    color: #2563eb;
    font-weight: bold;
    text-decoration: none;
}

@media(max-width:600px) {

    body {
        padding: 12px;
    }

    .card {
        padding: 22px;
        border-radius: 14px;
    }

    h1 {
        font-size: 23px;
    }

}

</style>
</head>

<body>

<div class="card">

    <div class="logo">🔐</div>

    <h1>Forgot Password?</h1>

    <div class="subtitle">
        Enter your registered email address.
        We will send you a secure OTP to reset your password.
    </div>

    <form id="forgotForm">

        <label>Email</label>

        <input
            id="email"
            type="email"
            placeholder="Enter your registered email"
            autocomplete="email"
            required
        >

        <button id="sendButton" type="submit">
            Send Reset OTP
        </button>

    </form>

    <div id="message"></div>

    <div class="back">
        <a href="/citizen/login">← Back to Citizen Login</a>
        &nbsp; | &nbsp;
        <a href="/admin/login">Admin Login</a>
    </div>

</div>

<script>

document.getElementById("forgotForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const email =
            document.getElementById("email").value.trim();

        const button =
            document.getElementById("sendButton");

        const message =
            document.getElementById("message");

        button.disabled = true;
        button.textContent = "Sending...";

        message.className = "";
        message.style.display = "none";

        try {

            const response = await fetch(
                "/api/auth/forgot-password",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email
                    })
                }
            );

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(
                    result.message || "Unable to process request."
                );
            }

            message.className = "success";
            message.textContent = result.message;

            setTimeout(function() {
                window.location.href =
                    "/reset-password?email=" +
                    encodeURIComponent(email);
            }, 1200);

        } catch(error) {

            message.className = "error";
            message.textContent = error.message;

            button.disabled = false;
            button.textContent = "Send Reset OTP";
        }

    }
);

</script>

</body>
</html>
"""


@auth_bp.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    user = User.query.filter_by(email=email).first()

    # Always return a generic response.
    # This avoids revealing whether an email is registered.
    if not user:

        return jsonify({
            "success": True,
            "message": "If an account exists with this email, a reset code has been sent."
        }), 200

    try:

        otp = str(random.randint(100000, 999999))

        PasswordReset.query.filter_by(
            user_id=user.id,
            used=False
        ).delete(
            synchronize_session=False
        )

        reset = PasswordReset(
            user_id=user.id,
            email=user.email,
            otp_hash=generate_password_hash(otp),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            attempts=0,
            verified=False,
            used=False
        )

        db.session.add(reset)
        db.session.commit()

        try:

            send_password_reset_email(
                user.email,
                otp
            )

        except Exception as email_error:

            db.session.delete(reset)
            db.session.commit()

            print("PASSWORD RESET EMAIL ERROR:", email_error)

            return jsonify({
                "success": False,
                "message": "Unable to send reset email. Please try again later."
            }), 500

        return jsonify({
            "success": True,
            "message": "If an account exists with this email, a reset code has been sent."
        }), 200

    except Exception as e:

        db.session.rollback()

        print("FORGOT PASSWORD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to process password reset request."
        }), 500


@auth_bp.route("/reset-password")
def reset_password_page():

    return """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Reset Password - DisasterShield AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #0f172a, #1e3a5f);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 15px;
}

.card {
    width: 100%;
    max-width: 430px;
    background: white;
    padding: 30px;
    border-radius: 18px;
    box-shadow: 0 20px 50px rgba(0,0,0,.25);
}

.logo {
    text-align: center;
    font-size: 42px;
}

h1 {
    text-align: center;
    margin: 8px 0;
    color: #0f172a;
}

.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 14px;
    margin-bottom: 22px;
}

label {
    display: block;
    margin: 13px 0 6px;
    font-weight: bold;
    color: #334155;
}

input {
    width: 100%;
    padding: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    font-size: 15px;
}

button {
    width: 100%;
    margin-top: 20px;
    padding: 13px;
    border: 0;
    border-radius: 9px;
    background: #2563eb;
    color: white;
    font-size: 15px;
    font-weight: bold;
}

button:disabled {
    opacity: .6;
}

#message {
    display: none;
    margin-top: 15px;
    padding: 11px;
    border-radius: 8px;
    font-size: 14px;
}

.success {
    display: block !important;
    background: #dcfae6;
    color: #067647;
}

.error {
    display: block !important;
    background: #fee2e2;
    color: #991b1b;
}

.password-help {
    margin-top: 7px;
    font-size: 12px;
    color: #64748b;
    line-height: 1.5;
}

.back {
    text-align: center;
    margin-top: 18px;
    font-size: 14px;
}

a {
    color: #2563eb;
    font-weight: bold;
    text-decoration: none;
}

</style>

</head>

<body>

<div class="card">

    <div class="logo">🔐</div>

    <h1>Reset Password</h1>

    <div class="subtitle">
        Enter the OTP sent to your email and choose a new password.
    </div>

    <form id="resetForm">

        <label>OTP</label>

        <input
            id="otp"
            type="text"
            inputmode="numeric"
            maxlength="6"
            placeholder="Enter 6-digit OTP"
            required
        >

        <label>New Password</label>

        <input
            id="password"
            type="password"
            placeholder="Enter new password"
            autocomplete="new-password"
            required
        >

        <div class="password-help">
            Use at least 8 characters with uppercase, lowercase,
            number and special character.
        </div>

        <label>Confirm New Password</label>

        <input
            id="confirmPassword"
            type="password"
            placeholder="Confirm new password"
            autocomplete="new-password"
            required
        >

        <button id="resetButton" type="submit">
            Reset Password
        </button>

    </form>

    <div id="message"></div>

    <div class="back">
        <a href="/citizen/login">← Back to Login</a>
    </div>

</div>

<script>

const params = new URLSearchParams(
    window.location.search
);

const email = params.get("email") || "";

document.getElementById("resetForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const otp =
            document.getElementById("otp").value.trim();

        const password =
            document.getElementById("password").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;

        const button =
            document.getElementById("resetButton");

        const message =
            document.getElementById("message");

        message.className = "";
        message.style.display = "none";

        if (!email) {

            message.className = "error";
            message.textContent =
                "Reset session is invalid. Please request a new OTP.";

            return;
        }

        if (!/^[0-9]{6}$/.test(otp)) {

            message.className = "error";
            message.textContent =
                "Please enter the 6-digit OTP.";

            return;
        }

        if (password !== confirmPassword) {

            message.className = "error";
            message.textContent =
                "Passwords do not match.";

            return;
        }

        if (
            password.length < 8 ||
            !/[A-Z]/.test(password) ||
            !/[a-z]/.test(password) ||
            !/[0-9]/.test(password) ||
            !/[^A-Za-z0-9]/.test(password)
        ) {

            message.className = "error";
            message.textContent =
                "Password must contain 8+ characters, uppercase, lowercase, number and special character.";

            return;
        }

        button.disabled = true;
        button.textContent = "Resetting...";

        try {

            const response = await fetch(
                "/api/auth/reset-password",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email,
                        otp: otp,
                        password: password
                    })
                }
            );

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(
                    result.message ||
                    "Password reset failed."
                );
            }

            message.className = "success";
            message.textContent =
                "Password changed successfully. Redirecting to login...";

            setTimeout(function() {
                window.location.href =
                    result.role === "admin"
                    ? "/admin/login"
                    : "/citizen/login";
            }, 1500);

        } catch(error) {

            message.className = "error";
            message.textContent =
                error.message;

            button.disabled = false;
            button.textContent =
                "Reset Password";
        }

    }
);

</script>

</body>
</html>
"""


@auth_bp.route("/api/auth/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip()
    new_password = data.get("password", "")

    if not email or not otp or not new_password:

        return jsonify({
            "success": False,
            "message": "Email, OTP and new password are required."
        }), 400

    if not is_strong_password(new_password):

        return jsonify({
            "success": False,
            "message": "Please enter a strong password. Use at least 8 characters with uppercase, lowercase, number and special character."
        }), 400

    reset = PasswordReset.query.filter_by(
        email=email,
        used=False
    ).order_by(
        PasswordReset.created_at.desc()
    ).first()

    if not reset:

        return jsonify({
            "success": False,
            "message": "Invalid or expired reset request. Please request a new OTP."
        }), 400

    if datetime.utcnow() > reset.expires_at:

        reset.used = True
        db.session.commit()

        return jsonify({
            "success": False,
            "message": "OTP has expired. Please request a new OTP."
        }), 400

    if reset.attempts >= 5:

        return jsonify({
            "success": False,
            "message": "Too many incorrect OTP attempts. Please request a new OTP."
        }), 429

    if not check_password_hash(reset.otp_hash, otp):

        reset.attempts += 1
        db.session.commit()

        remaining = max(0, 5 - reset.attempts)

        return jsonify({
            "success": False,
            "message": f"Invalid OTP. {remaining} attempt(s) remaining."
        }), 400

    user = db.session.get(User, reset.user_id)

    if not user:

        reset.used = True
        db.session.commit()

        return jsonify({
            "success": False,
            "message": "Account could not be found."
        }), 404

    try:

        user.password_hash = generate_password_hash(
            new_password
        )

        reset.verified = True
        reset.used = True

        # Invalidate any other active reset requests
        PasswordReset.query.filter(
            PasswordReset.user_id == user.id,
            PasswordReset.id != reset.id,
            PasswordReset.used == False
        ).update(
            {"used": True},
            synchronize_session=False
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Password changed successfully.",
            "role": user.role
        }), 200

    except Exception as e:

        db.session.rollback()

        print("RESET PASSWORD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to change password. Please try again."
        }), 500
