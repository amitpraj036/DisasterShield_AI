from getpass import getpass

from app import app
from models import db, User


with app.app_context():

    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()

    password = getpass("Admin password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Error: Passwords do not match.")
        raise SystemExit(1)

    if len(password) < 8:
        print("Error: Password must contain at least 8 characters.")
        raise SystemExit(1)

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        print("Error: Email already exists.")
        raise SystemExit(1)

    admin = User(
        name=name,
        email=email,
        role="admin"
    )

    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    print("Admin account created successfully.")
    print(f"Admin ID: {admin.id}")
    print(f"Email: {admin.email}")
