from pathlib import Path
from unittest.mock import call, patch

import scrolling_vertical_tiling_toggle as script


HYPRLAND_DIRECTORY = Path(__file__).parents[2]


def test_super_e_toggles_tiling_while_scrolling_stays_vertical():
    appearance = (
        HYPRLAND_DIRECTORY / "program-configuration" / "conf.d" / "appearance.conf"
    ).read_text()
    bindings = (
        HYPRLAND_DIRECTORY / "program-configuration" / "conf.d" / "bindings.conf"
    ).read_text()
    super_e_bindings = [
        line.strip()
        for line in bindings.splitlines()
        if line.startswith("bindd = SUPER, E,")
    ]

    assert "direction = down" in appearance
    assert super_e_bindings == [
        "bindd = SUPER, E, Toggle vertical tiling, exec, hypr-scrolling-vertical-tiling-toggle"
    ]


def test_toggle_uses_the_previous_strip_when_available():
    with patch.object(script, "run_hyprctl", return_value="ok\n") as run_hyprctl:
        assert script.toggle_vertical_tiling() == "ok"

    run_hyprctl.assert_called_once_with(
        "dispatch", "layoutmsg", "consume_or_expel prev"
    )


def test_toggle_uses_the_next_strip_at_the_previous_boundary():
    with patch.object(
        script,
        "run_hyprctl",
        side_effect=["no adjacent column\n", "ok\n"],
    ) as run_hyprctl:
        assert script.toggle_vertical_tiling() == "ok"

    assert run_hyprctl.call_args_list == [
        call("dispatch", "layoutmsg", "consume_or_expel prev"),
        call("dispatch", "layoutmsg", "consume_or_expel next"),
    ]
