import stat
import sys
from pathlib import Path

import write_credentials_env_file
from write_credentials_env_file import (
    main,
    read_existing_credentials,
    read_secret_backed_credentials,
)


def run_main(monkeypatch, output_path, literals=(), secret_files=(), timeout="0"):
    argv = ["write-credentials-env-file", "--output-path", str(output_path)]
    for literal in literals:
        argv += ["--literal", literal]
    for secret_file in secret_files:
        argv += ["--from-secret-file", secret_file]
    argv += ["--secret-timeout-seconds", timeout]
    monkeypatch.setattr(sys, "argv", argv)
    return main()


def test_writes_literals_and_secret_values_sorted(tmp_path, monkeypatch):
    secret_file = tmp_path / "token"
    secret_file.write_text("s3cret\n")
    output_path = tmp_path / "config" / ".env"

    exit_code = run_main(
        monkeypatch,
        output_path,
        literals=["ZETA=last", "ALPHA=first"],
        secret_files=[f"TOKEN={secret_file}"],
    )

    assert exit_code == 0
    assert output_path.read_text() == "ALPHA=first\nTOKEN=s3cret\nZETA=last\n"


def test_written_file_is_owner_readable_only(tmp_path, monkeypatch):
    output_path = tmp_path / ".env"

    run_main(monkeypatch, output_path, literals=["ALPHA=first"])

    assert stat.S_IMODE(output_path.stat().st_mode) == 0o600


def test_credentials_are_private_before_the_first_write(tmp_path, monkeypatch):
    output_path = tmp_path / ".env"
    original_replace = write_credentials_env_file.os.replace
    published_credentials = []

    def inspect_publication(source, destination):
        source_path = Path(source)
        assert stat.S_IMODE(source_path.stat().st_mode) == 0o600
        published_credentials.append(source_path.read_text())
        return original_replace(source, destination)

    monkeypatch.setattr(write_credentials_env_file.os, "replace", inspect_publication)

    assert run_main(monkeypatch, output_path, literals=["TOKEN=secret"]) == 0
    assert published_credentials == ["TOKEN=secret\n"]


def test_replaces_a_destination_symlink_without_overwriting_its_target(
    tmp_path, monkeypatch
):
    target = tmp_path / "unrelated"
    target.write_text("KEPT=original\n")
    output_path = tmp_path / ".env"
    output_path.symlink_to(target)

    assert run_main(monkeypatch, output_path, literals=["TOKEN=secret"]) == 0

    assert not output_path.is_symlink()
    assert target.read_text() == "KEPT=original\n"
    assert output_path.read_text() == "KEPT=original\nTOKEN=secret\n"


def test_preserves_keys_the_caller_does_not_declare(tmp_path, monkeypatch):
    output_path = tmp_path / ".env"
    output_path.write_text("KEPT=value\nALPHA=stale\n")

    run_main(monkeypatch, output_path, literals=["ALPHA=fresh"])

    assert output_path.read_text() == "ALPHA=fresh\nKEPT=value\n"


def test_leaves_the_file_untouched_when_nothing_changed(tmp_path, monkeypatch):
    output_path = tmp_path / ".env"
    run_main(monkeypatch, output_path, literals=["ALPHA=first"])
    modification_time_before = output_path.stat().st_mtime_ns

    run_main(monkeypatch, output_path, literals=["ALPHA=first"])

    assert output_path.stat().st_mtime_ns == modification_time_before


def test_refuses_to_write_when_a_secret_file_is_missing(tmp_path, monkeypatch):
    output_path = tmp_path / ".env"
    output_path.write_text("TOKEN=previously-materialized\n")

    exit_code = run_main(
        monkeypatch,
        output_path,
        literals=["ALPHA=first"],
        secret_files=[f"TOKEN={tmp_path / 'absent'}"],
    )

    assert exit_code == 1
    assert output_path.read_text() == "TOKEN=previously-materialized\n"


def test_refuses_to_write_when_a_secret_file_is_empty(tmp_path, monkeypatch):
    empty_secret_file = tmp_path / "token"
    empty_secret_file.write_text("\n")
    output_path = tmp_path / ".env"

    exit_code = run_main(
        monkeypatch,
        output_path,
        secret_files=[f"TOKEN={empty_secret_file}"],
    )

    assert exit_code == 1
    assert not output_path.exists()


def test_reports_every_unresolved_secret_rather_than_the_first(tmp_path):
    resolved, unresolved = read_secret_backed_credentials(
        [
            ("FIRST", str(tmp_path / "absent-one")),
            ("SECOND", str(tmp_path / "absent-two")),
        ],
        timeout_seconds=0,
    )

    assert resolved == {}
    assert len(unresolved) == 2
    assert "FIRST" in unresolved[0]
    assert "SECOND" in unresolved[1]


def test_existing_credentials_ignore_comments_and_blank_lines(tmp_path):
    output_path = tmp_path / ".env"
    output_path.write_text("# comment\n\nALPHA=first\nnot-a-pair\n")

    assert read_existing_credentials(output_path) == {"ALPHA": "first"}
