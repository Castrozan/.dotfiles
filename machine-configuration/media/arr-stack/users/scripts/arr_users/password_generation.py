import secrets

FRIEND_PASSWORD_ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
FRIEND_PASSWORD_LENGTH = 20


def generate_friend_password(length=FRIEND_PASSWORD_LENGTH):
    return "".join(secrets.choice(FRIEND_PASSWORD_ALPHABET) for _ in range(length))
