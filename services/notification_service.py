import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_safety_alert_email(user, alert, distance_km):
    """Send a safety-zone warning email using the existing SMTP configuration."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username)

    if not smtp_username or not smtp_password:
        raise RuntimeError("Email service is not configured")

    severity = (alert.severity or "moderate").upper()
    distance_text = f"{distance_km:.2f} km"

    message = MIMEMultipart("alternative")
    message["Subject"] = f"🚨 {severity} Safety Alert — {alert.title}"
    message["From"] = f"DisasterShield AI <{smtp_from}>"
    message["To"] = user.email

    text_body = f"""DisasterShield AI\n\nHello {user.name},\n\nYou are currently about {distance_text} from an active disaster alert.\n\nAlert: {alert.title}\nSeverity: {severity}\nMessage: {alert.message}\n\nPlease check the DisasterShield AI map and follow official/local safety instructions.\n\nThis is an automated safety notification.\n"""

    html_body = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">
<div style="max-width:620px;margin:30px auto;background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 8px 30px rgba(20,40,80,.10);">
  <div style="background:linear-gradient(135deg,#0b1f3a,#1769aa);padding:28px 30px;color:#fff;">
    <div style="font-size:25px;font-weight:700;">🛡️ DisasterShield <span style="color:#67d5ff;">AI</span></div>
    <div style="font-size:13px;margin-top:6px;color:#d7ecf8;">Location-Based Safety Alert</div>
  </div>
  <div style="padding:32px 30px;">
    <h2 style="margin:0 0 12px;color:#14233b;">🚨 You are near a danger zone</h2>
    <p style="line-height:1.6;color:#667085;">Hello {user.name}, DisasterShield AI detected that your shared location is within the configured safety radius of an active alert.</p>
    <div style="padding:20px;background:#fff7ed;border-left:5px solid #f97316;border-radius:10px;margin:20px 0;">
      <div style="font-size:20px;font-weight:700;color:#9a3412;">{alert.title}</div>
      <div style="margin-top:8px;color:#7c2d12;"><strong>Severity:</strong> {severity}</div>
      <div style="margin-top:8px;color:#7c2d12;"><strong>Approx. distance:</strong> {distance_text}</div>
      <div style="margin-top:12px;line-height:1.6;color:#7c2d12;">{alert.message}</div>
    </div>
    <p style="line-height:1.6;color:#667085;"><strong>Please check the DisasterShield AI map and follow official/local safety instructions.</strong></p>
    <p style="font-size:12px;color:#98a2b3;">Location-based alerts require your explicit permission and only use the latest location shared by your browser.</p>
  </div>
  <div style="background:#101f35;padding:22px 30px;color:#d8e3ef;text-align:center;font-size:12px;">🛡️ DisasterShield AI • Automated safety notification</div>
</div>
</body>
</html>"""

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, user.email, message.as_string())
