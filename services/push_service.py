import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

from models import PushSubscription


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def send_push_notification(subscription, title, message, data=None):
    private_key_file = os.getenv("VAPID_PRIVATE_KEY_FILE")
    claims_email = os.getenv("VAPID_CLAIMS_EMAIL")

    if not private_key_file or not claims_email:
        print("VAPID configuration missing.")
        return False

    private_key_path = Path(private_key_file)

    if not private_key_path.is_absolute():
        private_key_path = BASE_DIR / private_key_path

    if not private_key_path.exists():
        print(f"VAPID private key not found: {private_key_path}")
        return False

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    payload = {
        "title": title,
        "body": message,
        "data": data or {},
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=str(private_key_path),
            vapid_claims={
                "sub": claims_email,
            },
        )

        return True

    except WebPushException as exc:
        print(f"Web Push failed: {exc}")
        return False

    except Exception as exc:
        print(f"Unexpected Web Push error: {exc}")
        return False


def send_push_to_user(user_id, title, message, data=None):
    subscriptions = PushSubscription.query.filter_by(
        user_id=user_id,
        enabled=True
    ).all()

    sent_count = 0

    for subscription in subscriptions:
        if send_push_notification(
            subscription,
            title,
            message,
            data
        ):
            sent_count += 1

    return sent_count
