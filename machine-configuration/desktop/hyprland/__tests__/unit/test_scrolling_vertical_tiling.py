from pathlib import Path


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
        "bindd = SUPER, E, Toggle vertical tiling, layoutmsg, consume_or_expel prev"
    ]
