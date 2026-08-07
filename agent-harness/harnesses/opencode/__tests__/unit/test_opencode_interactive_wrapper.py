from pathlib import Path


OPENCODE_MODULE = Path(__file__).resolve().parents[2] / "opencode.nix"


def test_web_and_mini_run_sessions_receive_interactive_preferences():
    source = OPENCODE_MODULE.read_text(encoding="utf-8")

    noninteractive_command_case = source.split("case \"''${1:-}\" in", 1)[1].split(
        "*)", 1
    )[0]
    assert "web" not in noninteractive_command_case
    assert "run)" in source
    assert "--mini" in source
    assert "OPENCODE_INTERACTIVE_PREFERENCES_PATH" in source
    assert "applyInteractiveSessionOverlay() {" in source
    assert source.count("applyInteractiveSessionOverlay") >= 3
