SENT_NOTIFICATIONS = []

def send_welcome_notification(user):
    notification = {
        "to": user["email"],
        "subject": f"Welcome {user['name']}",
        "body": "Thanks for signing up!",
    }
    SENT_NOTIFICATIONS.append(notification)
    return notification
