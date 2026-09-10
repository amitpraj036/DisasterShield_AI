from flask import Flask, render_template, session, redirect
from flask_migrate import Migrate

from config import Config
from models import db, User

from routes.auth import auth_bp
from routes.alerts import alerts_bp
from routes.risk import risk_bp
from routes.reports import reports_bp
from routes.data import data_bp
from routes.admin import admin_bp
from routes.gis import gis_bp
from routes.emergency import emergency_bp
from routes.safety import safety_bp


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Database
    db.init_app(app)

    # Flask-Migrate
    Migrate(app, db)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(gis_bp)
    app.register_blueprint(emergency_bp)
    app.register_blueprint(safety_bp)

    @app.route("/")
    def home():
     return redirect("/citizen/login")


    @app.route("/health")
    def health():
        return {
            "status": "healthy"
        }
    # =========================
    # CITIZEN PORTAL
    # =========================

    @app.route("/citizen/register")
    def citizen_register():
        user_id = session.get("user_id")

        if user_id:
            user = db.session.get(User, user_id)

            if user:
                if user.role == "citizen":
                    return redirect("/citizen")
                if user.role == "admin":
                    return redirect("/admin")

        return render_template("citizen_register.html")


    @app.route("/citizen/login")
    def citizen_login():
        user_id = session.get("user_id")

        if user_id:
            user = db.session.get(User, user_id)

            if user:
                if user.role == "citizen":
                    return redirect("/citizen")
                if user.role == "admin":
                    return redirect("/admin")

        return render_template("citizen_login.html")


    @app.route("/citizen")
    def citizen_dashboard():
        user_id = session.get("user_id")

        if not user_id:
            return redirect("/citizen/login")

        user = db.session.get(User, user_id)

        if not user:
            session.clear()
            return redirect("/citizen/login")

        if user.role != "citizen":
            return redirect("/admin")

        return render_template(
            "citizen_dashboard.html",
            user=user
        )
    @app.route("/citizen/map")
    def citizen_map():
        return render_template("map.html")

    @app.route("/citizen/report")
    def citizen_report():
        user_id = session.get("user_id")

        if not user_id:
            return redirect("/citizen/login")

        user = db.session.get(User, user_id)

        if not user:
            session.clear()
            return redirect("/citizen/login")

        if user.role != "citizen":
            return redirect("/admin")

        return render_template("report_disaster.html")

    # Browser admin login page
    @app.route("/admin/login")
    def admin_login():
        user_id = session.get("user_id")

        if user_id:
            user = db.session.get(User, user_id)

            if user and user.role == "admin":
                return redirect("/admin")

        return render_template("admin_login.html")

    # Admin dashboard
    @app.route("/admin")
    def admin_dashboard():
        user_id = session.get("user_id")

        if not user_id:
            return redirect("/admin/login")

        user = db.session.get(User, user_id)

        if not user:
            session.clear()
            return redirect("/admin/login")

        if user.role != "admin":
            return {
                "success": False,
                "message": "Admin access required"
            }, 403

        return render_template("admin.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
