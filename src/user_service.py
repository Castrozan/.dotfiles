from src.user_repository import find_user_by_email, save_user
from src.notification_sender import send_welcome_notification

def register_new_user(registration_data):
    email = registration_data.get("email")
    existing = find_user_by_email(email)
    if existing:
        raise ValueError("email already registered")
    user = {"email": email, "name": registration_data.get("name")}
    save_user(user)
    send_welcome_notification(user)
    return user
