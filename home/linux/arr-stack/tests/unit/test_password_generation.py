import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import password_generation


def test_generated_password_has_default_length():
    password = password_generation.generate_friend_password()
    assert len(password) == password_generation.FRIEND_PASSWORD_LENGTH


def test_generated_password_uses_unambiguous_alphabet_only():
    password = password_generation.generate_friend_password(200)
    assert set(password) <= set(password_generation.FRIEND_PASSWORD_ALPHABET)
    assert not set(password) & set("0O1lI")


def test_generated_passwords_differ():
    first = password_generation.generate_friend_password()
    second = password_generation.generate_friend_password()
    assert first != second
