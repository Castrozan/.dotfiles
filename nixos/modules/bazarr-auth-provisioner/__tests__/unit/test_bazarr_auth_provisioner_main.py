import importlib.util
import os
import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "bazarr_auth_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))


def load_main_module():
    specification = importlib.util.spec_from_file_location(
        "bazarr_auth_main", PROVISIONER_PACKAGE_DIRECTORY_PATH / "__main__.py"
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


main_module = load_main_module()

DISABLED_CONFIG_TEXT = (
    "general:\n  port: 6767\nauth:\n  apikey: keepme\n  type: null\n  username: ''\n"
)


def test_read_secret_value_returns_empty_for_missing_path():
    assert main_module.read_secret_value("") == ""
    assert main_module.read_secret_value("/no/such/secret/file") == ""


def test_read_secret_value_strips_trailing_whitespace(tmp_path):
    secret = tmp_path / "secret"
    secret.write_text("hunter2\n")
    assert main_module.read_secret_value(str(secret)) == "hunter2"


def test_parse_owner_splits_uid_and_gid():
    assert main_module.parse_owner("1000:100") == (1000, 100)


def test_load_config_lines_returns_none_when_absent(tmp_path):
    assert main_module.load_config_lines(str(tmp_path / "missing.yaml")) is None


def test_write_config_lines_writes_atomically_with_mode_and_ownership(tmp_path):
    target = tmp_path / "config.yaml"
    target.write_text("stale\n")
    main_module.write_config_lines(
        str(target), ["auth:", "  type: form"], os.getuid(), os.getgid()
    )
    assert target.read_text() == "auth:\n  type: form\n"
    assert (target.stat().st_mode & 0o777) == 0o644


def prepare_main(monkeypatch, tmp_path, username="lucas", password="pw"):
    secret = tmp_path / "secret"
    secret.write_text(password)
    config = tmp_path / "config.yaml"
    config.write_text(DISABLED_CONFIG_TEXT)
    monkeypatch.setenv("BAZARR_AUTH_CONFIG_FILE", str(config))
    monkeypatch.setenv("BAZARR_AUTH_CONTAINER_NAME", "arr-bazarr")
    monkeypatch.setenv("BAZARR_AUTH_LOGIN_USERNAME", username)
    monkeypatch.setenv("BAZARR_AUTH_PASSWORD_FILE", str(secret) if password else "")
    monkeypatch.setenv("BAZARR_AUTH_FILE_OWNER", f"{os.getuid()}:{os.getgid()}")
    calls = {"stop": 0, "start": 0}
    monkeypatch.setattr(
        main_module,
        "stop_container",
        lambda name: calls.__setitem__("stop", calls["stop"] + 1),
    )
    monkeypatch.setattr(
        main_module,
        "start_container",
        lambda name: calls.__setitem__("start", calls["start"] + 1),
    )
    return config, calls


def test_main_skips_when_password_missing(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path, password="")
    monkeypatch.setattr(main_module, "container_is_running", lambda name: True)
    main_module.main()
    assert calls == {"stop": 0, "start": 0}
    assert config.read_text() == DISABLED_CONFIG_TEXT


def test_main_short_circuits_when_already_matching(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path)
    password_hash = main_module.md5_hex("pw")
    config.write_text(
        f"auth:\n  apikey: keepme\n  type: form\n  username: lucas\n  password: {password_hash}\n"
    )
    checked = {"running": False}
    monkeypatch.setattr(
        main_module,
        "container_is_running",
        lambda name: checked.__setitem__("running", True) or True,
    )
    main_module.main()
    assert calls == {"stop": 0, "start": 0}
    assert checked["running"] is False


def test_main_bounces_running_container_and_writes(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path)
    monkeypatch.setattr(main_module, "container_is_running", lambda name: True)
    main_module.main()
    assert calls == {"stop": 1, "start": 1}
    values = main_module.parse_auth_block(config.read_text().splitlines())
    assert values["type"] == "form"
    assert values["username"] == "lucas"
    assert values["password"] == main_module.md5_hex("pw")
    assert values["apikey"] == "keepme"


def test_main_leaves_stopped_container_down(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path)
    monkeypatch.setattr(main_module, "container_is_running", lambda name: False)
    main_module.main()
    assert calls == {"stop": 0, "start": 0}
    assert (
        main_module.parse_auth_block(config.read_text().splitlines())["type"] == "form"
    )


def test_main_skips_when_config_absent(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path)
    config.unlink()
    monkeypatch.setattr(main_module, "container_is_running", lambda name: True)
    main_module.main()
    assert calls == {"stop": 0, "start": 0}


def test_main_skips_when_username_missing(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path, username="")
    original_text = config.read_text()
    monkeypatch.setattr(main_module, "container_is_running", lambda name: True)
    main_module.main()
    assert calls == {"stop": 0, "start": 0}
    assert config.read_text() == original_text


def test_main_reloads_config_after_stopping_container(monkeypatch, tmp_path):
    config, calls = prepare_main(monkeypatch, tmp_path)

    def stop_and_rewrite_config(name):
        calls["stop"] += 1
        config.write_text(DISABLED_CONFIG_TEXT + "extra:\n  sentinel: postStop\n")

    monkeypatch.setattr(main_module, "container_is_running", lambda name: True)
    monkeypatch.setattr(main_module, "stop_container", stop_and_rewrite_config)
    main_module.main()
    written_text = config.read_text()
    assert "sentinel: postStop" in written_text
    values = main_module.parse_auth_block(written_text.splitlines())
    assert values["type"] == "form" and values["username"] == "lucas"
    assert calls["start"] == 1
