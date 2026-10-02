import json
import stat

import pytest

import write_glab_configuration


def test_writes_distinct_host_credentials_with_private_permissions(tmp_path):
    personal_token = tmp_path / "personal-token"
    personal_token.write_text("personal-secret\n")
    work_token = tmp_path / "work-token"
    work_token.write_text("work-secret\n")
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "editor": "vim",
                "hosts": {
                    "gitlab.com": {
                        "git_protocol": "https",
                        "token_file": str(personal_token),
                    },
                    "work.example": {
                        "git_protocol": "ssh",
                        "token_file": str(work_token),
                    },
                },
            }
        )
    )
    destination = tmp_path / "configuration" / "config.yml"

    write_glab_configuration.write_configuration(source, destination)
    write_glab_configuration.write_configuration(source, destination)

    configuration = json.loads(destination.read_text())
    assert configuration["editor"] == "vim"
    assert configuration["hosts"]["gitlab.com"] == {
        "git_protocol": "https",
        "token": "personal-secret",
    }
    assert configuration["hosts"]["work.example"] == {
        "git_protocol": "ssh",
        "token": "work-secret",
    }
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


def test_missing_secret_preserves_existing_configuration(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps({"hosts": {"gitlab.com": {"token_file": str(tmp_path / "missing")}}})
    )
    destination = tmp_path / "config.yml"
    destination.write_text("existing configuration")
    clock = iter([0.0, 31.0])
    monkeypatch.setattr(write_glab_configuration.time, "monotonic", lambda: next(clock))

    with pytest.raises(TimeoutError):
        write_glab_configuration.write_configuration(source, destination)

    assert destination.read_text() == "existing configuration"


def test_waits_for_agenix_to_materialize_secret(tmp_path, monkeypatch):
    token_file = tmp_path / "delayed-token"
    monkeypatch.setattr(
        write_glab_configuration.time,
        "sleep",
        lambda _interval: token_file.write_text("delayed-secret\n"),
    )

    assert write_glab_configuration.read_host_token(token_file) == "delayed-secret"
