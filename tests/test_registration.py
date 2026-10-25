from src.user_service import register_new_user
from src.user_repository import USERS_DATABASE, find_user_by_email

def test_register_new_user_creates_user():
    USERS_DATABASE.clear()
    result = register_new_user({"email": "test@example.com", "name": "Test"})
    assert result["email"] == "test@example.com"

def test_register_duplicate_email_raises():
    USERS_DATABASE.clear()
    register_new_user({"email": "dup@example.com", "name": "First"})
    try:
        register_new_user({"email": "dup@example.com", "name": "Second"})
        assert False, "should have raised"
    except ValueError:
        pass

def test_registered_user_can_be_found_by_email():
    USERS_DATABASE.clear()
    register_new_user({"email": "found@example.com", "name": "Found"})
    assert find_user_by_email("found@example.com") == {"email": "found@example.com", "name": "Found"}
