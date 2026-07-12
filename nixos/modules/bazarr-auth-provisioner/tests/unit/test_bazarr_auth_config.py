import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "bazarr_auth_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import bazarr_auth_config

DISABLED_CONFIG = [
    "general:",
    "  port: 6767",
    "auth:",
    "  apikey: keepme",
    "  type: null",
    "  username: ''",
    "  password: ''",
    "backup:",
    "  folder: /config/backup",
]


def test_md5_hex_matches_bazarr_scheme_without_trailing_newline():
    assert bazarr_auth_config.md5_hex("secret") == "5ebe2294ecd0e0f08eab7690d2a6ee69"


def test_parse_auth_block_reads_only_auth_children_and_unquotes():
    values = bazarr_auth_config.parse_auth_block(DISABLED_CONFIG)
    assert values["apikey"] == "keepme"
    assert values["type"] == "null"
    assert values["username"] == ""
    assert values["password"] == ""
    assert "folder" not in values


def test_auth_already_matches_true_when_type_user_and_hash_align():
    values = {"type": "form", "username": "lucas", "password": "deadbeef"}
    assert bazarr_auth_config.auth_already_matches(values, "lucas", "deadbeef")


def test_auth_already_matches_false_when_disabled():
    values = bazarr_auth_config.parse_auth_block(DISABLED_CONFIG)
    assert not bazarr_auth_config.auth_already_matches(values, "lucas", "deadbeef")


def test_apply_forms_login_replaces_login_keys_in_place_and_preserves_rest():
    result = bazarr_auth_config.apply_forms_login(DISABLED_CONFIG, "lucas", "deadbeef")
    values = bazarr_auth_config.parse_auth_block(result)
    assert values["type"] == "form"
    assert values["username"] == "lucas"
    assert values["password"] == "deadbeef"
    assert values["apikey"] == "keepme"
    assert "general:" in result and "  port: 6767" in result
    assert "backup:" in result and "  folder: /config/backup" in result


def test_apply_forms_login_is_idempotent_after_first_application():
    once = bazarr_auth_config.apply_forms_login(DISABLED_CONFIG, "lucas", "deadbeef")
    twice = bazarr_auth_config.apply_forms_login(once, "lucas", "deadbeef")
    assert once == twice


def test_apply_forms_login_inserts_missing_login_keys_into_sparse_auth_block():
    sparse = ["auth:", "  apikey: keepme"]
    result = bazarr_auth_config.apply_forms_login(sparse, "lucas", "deadbeef")
    values = bazarr_auth_config.parse_auth_block(result)
    assert values["apikey"] == "keepme"
    assert values["type"] == "form"
    assert values["username"] == "lucas"
    assert values["password"] == "deadbeef"


def test_apply_forms_login_preserves_two_space_indentation():
    result = bazarr_auth_config.apply_forms_login(DISABLED_CONFIG, "lucas", "deadbeef")
    assert "  type: form" in result
    assert "  username: lucas" in result
    assert "  password: deadbeef" in result


def test_apply_forms_login_appends_auth_block_when_section_absent():
    no_auth_config = ["general:", "  port: 6767", "backup:", "  folder: /config/backup"]
    result = bazarr_auth_config.apply_forms_login(no_auth_config, "lucas", "deadbeef")
    values = bazarr_auth_config.parse_auth_block(result)
    assert values["type"] == "form"
    assert values["username"] == "lucas"
    assert values["password"] == "deadbeef"
    assert "general:" in result and "  port: 6767" in result
    assert "backup:" in result and "  folder: /config/backup" in result
