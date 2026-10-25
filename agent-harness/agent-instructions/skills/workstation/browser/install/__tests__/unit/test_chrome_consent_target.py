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
