import json
import os
import stat


def test_merge_enforces_wildcard_and_policy_leaves(enforcer):
    config = {
        "security": {
            "allowClipboard": False,
            "enableActionGuards": True,
            "allowedDomains": ["localhost"],
        }
    }
    enforcer.merge_enforced_leaves_preserving_everything_else(
        config, enforcer.full_access_security_and_headed_default_policy
    )
    security = config["security"]
    assert security["allowedDomains"] == ["*"]
    assert security["downloadAllowedDomains"] == ["*"]
    assert security["allowClipboard"] is True
    assert security["allowStateExport"] is True
    assert security["enableActionGuards"] is False
    assert security["attach"]["allowHosts"] == ["*"]
    assert security["idpi"]["enabled"] is False
    assert config["instanceDefaults"]["mode"] == "headed"


def test_merge_preserves_token_paths_and_unrelated_nested_keys(enforcer):
    config = {
        "server": {"token": "keepme", "port": "9999", "stateDir": "/keep/this"},
        "browser": {"binary": "/keep/chrome"},
        "security": {"uploadMaxFiles": 8, "idpi": {"scanTimeoutSec": 5}},
        "autoSolver": {"credentials": {"login": {"secret": "keep"}}},
    }
    enforcer.merge_enforced_leaves_preserving_everything_else(
        config, enforcer.full_access_security_and_headed_default_policy
    )
    assert config["server"] == {
        "token": "keepme",
        "port": "9999",
        "stateDir": "/keep/this",
    }
    assert config["browser"] == {"binary": "/keep/chrome"}
    assert config["security"]["uploadMaxFiles"] == 8
    assert config["security"]["idpi"]["scanTimeoutSec"] == 5
    assert config["autoSolver"]["credentials"]["login"]["secret"] == "keep"


def test_token_preserved_verbatim_when_present(enforcer):
    config = {"server": {"token": "verbatimtoken"}}
    enforcer.ensure_server_bearer_token_exists_so_a_fresh_machine_starts_authenticated(
        config
    )
    assert config["server"]["token"] == "verbatimtoken"


def test_token_generated_only_when_absent(enforcer):
    config = {}
    enforcer.ensure_server_bearer_token_exists_so_a_fresh_machine_starts_authenticated(
        config
    )
    generated = config["server"]["token"]
    assert len(generated) == 48
    assert all(character in "0123456789abcdef" for character in generated)


def test_non_dict_server_is_coerced_without_crashing(enforcer):
    config = {"server": None}
    enforcer.ensure_server_bearer_token_exists_so_a_fresh_machine_starts_authenticated(
        config
    )
    assert isinstance(config["server"], dict)
    assert config["server"]["token"]


def test_main_writes_full_access_policy_preserving_token(enforcer, config_path):
    config_path.write_text(
        json.dumps({"server": {"token": "livetoken", "stateDir": "/live"}})
    )
    enforcer.main()
    written = json.loads(config_path.read_text())
    assert written["server"]["token"] == "livetoken"
    assert written["server"]["stateDir"] == "/live"
    assert written["security"]["allowedDomains"] == ["*"]
    assert written["security"]["enableActionGuards"] is False
    assert written["instanceDefaults"]["mode"] == "headed"


def test_main_does_not_rewrite_an_already_compliant_config(
    enforcer, config_path, compliant_config
):
    config_path.write_text(json.dumps(compliant_config()))
    before_bytes = config_path.read_bytes()
    enforcer.main()
    assert config_path.read_bytes() == before_bytes


def test_main_leaves_malformed_json_untouched(enforcer, config_path):
    config_path.write_text("{ this is not json")
    before_bytes = config_path.read_bytes()
    enforcer.main()
    assert config_path.read_bytes() == before_bytes


def test_main_leaves_non_object_root_untouched(enforcer, config_path):
    config_path.write_text("[]")
    before_bytes = config_path.read_bytes()
    enforcer.main()
    assert config_path.read_bytes() == before_bytes


def test_main_coerces_non_dict_server_without_aborting(enforcer, config_path):
    config_path.write_text(json.dumps({"server": None}))
    enforcer.main()
    written = json.loads(config_path.read_text())
    assert isinstance(written["server"], dict)
    assert written["server"]["token"]
    assert written["security"]["allowedDomains"] == ["*"]


def test_main_writes_owner_only_permissions(enforcer, config_path):
    config_path.write_text(json.dumps({"server": {"token": "t"}}))
    enforcer.main()
    mode = stat.S_IMODE(os.stat(config_path).st_mode)
    assert mode == 0o600
