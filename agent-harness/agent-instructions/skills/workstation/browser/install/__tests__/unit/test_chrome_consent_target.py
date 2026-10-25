import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/chrome-devtools"))

import chrome_consent_target as target


@pytest.mark.parametrize("flattened", [False, True])
@pytest.mark.parametrize("mismatched", [False, True])
def test_native_profile_identity_handles_chrome_process_titles(
    tmp_path, monkeypatch, flattened, mismatched
):
    process = tmp_path / "proc/123"
    process.mkdir(parents=True)
    package = tmp_path / "chrome-package"
    executable = package / "share/google/chrome/chrome"
    executable.parent.mkdir(parents=True)
    executable.touch()
    (process / "exe").symlink_to(executable)
    profile = tmp_path / "chrome-global"
    arguments = [
        str(executable),
        f"--user-data-dir={tmp_path / 'other' if mismatched else profile}",
        "--class=chrome-global",
    ]
    separator = " " if flattened else "\0"
    (process / "cmdline").write_bytes((separator.join(arguments) + "\0").encode())
    (process / "stat").write_text("123 (chrome) " + " ".join(["S", *["0"] * 18, "456"]))
    monkeypatch.setattr(
        target,
        "Path",
        lambda value: tmp_path / "proc" if value == "/proc" else Path(value),
    )
    if mismatched:
        with pytest.raises(RuntimeError, match="managed Chrome Global profile"):
            target.chrome_identity(123, str(profile), str(package))
    else:
        assert target.chrome_identity(123, str(profile), str(package)) == "456"


@pytest.mark.parametrize("count", [0, 2])
def test_missing_or_multiple_global_windows_are_ambiguous(monkeypatch, count):
    import json

    clients = [{"class": "chrome-global", "mapped": True} for _ in range(count)]
    monkeypatch.setattr(target, "run_tool", lambda *args: json.dumps(clients))
    with pytest.raises(RuntimeError, match="exactly one managed Chrome window"):
        target.current_target({})


@pytest.mark.parametrize("flag", ["hidden", "fullscreen", "fullscreenClient"])
def test_hidden_or_fullscreen_window_cannot_receive_approval(monkeypatch, flag):
    import json

    client = {"class": "chrome-global", "mapped": True, flag: True}
    monkeypatch.setattr(target, "run_tool", lambda *args: json.dumps([client]))
    with pytest.raises(RuntimeError, match="visible and outside fullscreen"):
        target.current_target({})
