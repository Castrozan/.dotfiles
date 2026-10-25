USERS_DATABASE = {}

def find_user_by_email(email):
    for user_id, user in USERS_DATABASE.items():
        if user["email"] == email:
            return user
    return None

def save_user(user):
    import uuid
    user_id = str(uuid.uuid4())
    USERS_DATABASE[user_id] = user
    return user_id
