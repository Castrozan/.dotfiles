import floor_cli
import listener_runtime


def run_floor_cli(monkeypatch, tmp_path, *arguments):
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    monkeypatch.setattr(floor_cli.sys, "argv", ["avatar-claim-floor", *arguments])
    try:
        floor_cli.main()
    except SystemExit as finished:
        return finished.code
    return 0
