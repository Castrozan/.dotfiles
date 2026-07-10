import importlib.util
import sys
import urllib.error
from pathlib import Path

import pytest

ARR_STATUS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_status"
)
sys.path.insert(0, str(ARR_STATUS_PACKAGE_DIRECTORY_PATH))


def load_cli_module():
    module_specification = importlib.util.spec_from_file_location(
        "arr_status_cli", ARR_STATUS_PACKAGE_DIRECTORY_PATH / "__main__.py"
    )
    module = importlib.util.module_from_spec(module_specification)
    module_specification.loader.exec_module(module)
    return module


cli = load_cli_module()


def make_line(title, stage, progress=None, arr_reachable=True):
    return cli.status_assembly.MediaStatusLine(
        title=title,
        year="2018",
        media_type="tv",
        requested_by="lucas",
        stage=stage,
        progress=progress,
        arr_reachable=arr_reachable,
    )


def test_parser_accepts_no_title():
    assert cli.build_argument_parser().parse_args([]).title is None


def test_parser_accepts_title():
    assert cli.build_argument_parser().parse_args(["slime"]).title == "slime"


def test_main_prints_download_progress(monkeypatch, capsys):
    line = make_line(
        "Slime", "partial", progress={"percent": 33, "time_left": "00:09:58"}
    )
    monkeypatch.setattr(cli, "gather_status_lines", lambda: [line])
    monkeypatch.setattr(sys, "argv", ["arr-status"])
    cli.main()
    printed = capsys.readouterr().out
    assert "Slime (2018)" in printed
    assert "downloading 33%" in printed


def test_main_filters_by_title(monkeypatch, capsys):
    lines = [make_line("Slime", "partial"), make_line("Frieren", "available")]
    monkeypatch.setattr(cli, "gather_status_lines", lambda: lines)
    monkeypatch.setattr(sys, "argv", ["arr-status", "frier"])
    cli.main()
    printed = capsys.readouterr().out
    assert "Frieren" in printed
    assert "Slime" not in printed


def test_main_reports_no_matches(monkeypatch, capsys):
    monkeypatch.setattr(cli, "gather_status_lines", lambda: [])
    monkeypatch.setattr(sys, "argv", ["arr-status", "ghost"])
    cli.main()
    assert "no matching requests" in capsys.readouterr().out


def test_main_maps_url_error_to_exit_one(monkeypatch):
    def raise_url_error():
        raise urllib.error.URLError("refused")

    monkeypatch.setattr(cli, "gather_status_lines", raise_url_error)
    monkeypatch.setattr(sys, "argv", ["arr-status"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_main_maps_http_error_to_exit_one(monkeypatch):
    def raise_http_error():
        raise urllib.error.HTTPError("http://jellyseerr", 500, "boom", {}, None)

    monkeypatch.setattr(cli, "gather_status_lines", raise_http_error)
    monkeypatch.setattr(sys, "argv", ["arr-status"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1
