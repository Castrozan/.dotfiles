import types

from window_detection_test_helpers import build_screen


def test_the_menu_bar_height_is_measured_from_the_screen(daemon, monkeypatch):
    monkeypatch.setattr(
        daemon,
        "NSScreen",
        types.SimpleNamespace(
            screens=lambda: [build_screen(0.0, 0.0, 1080.0, visible_height=1050.0)]
        ),
    )

    assert daemon.get_tallest_menu_bar_height() == 30.0


def test_screen_corners_are_converted_into_window_list_coordinates(daemon, monkeypatch):
    monkeypatch.setattr(
        daemon,
        "NSScreen",
        types.SimpleNamespace(
            screens=lambda: [
                build_screen(0.0, 0.0, 1080.0),
                build_screen(1920.0, 200.0, 1440.0),
            ]
        ),
    )

    assert daemon.get_screen_bottom_left_corners() == {(0.0, 1080.0), (1920.0, 880.0)}


def test_the_per_application_menu_bar_strip_does_not_count_as_a_window(
    daemon, monkeypatch
):
    menu_bar_height = 30.0
    window_info_list = [
        {
            "kCGWindowLayer": 0,
            "kCGWindowOwnerPID": 111,
            "kCGWindowBounds": {"X": 0.0, "Y": 0.0, "Width": 1920.0, "Height": 30.0},
        },
        {
            "kCGWindowLayer": 0,
            "kCGWindowOwnerPID": 222,
            "kCGWindowBounds": {"X": 0.0, "Y": 30.0, "Width": 1920.0, "Height": 1050.0},
        },
        {
            "kCGWindowLayer": 25,
            "kCGWindowOwnerPID": 333,
            "kCGWindowBounds": {"X": 0.0, "Y": 0.0, "Width": 400.0, "Height": 400.0},
        },
    ]
    monkeypatch.setattr(
        daemon.Quartz,
        "CGWindowListCopyWindowInfo",
        lambda *_arguments: window_info_list,
    )

    assert daemon.get_process_identifiers_with_visible_windows(
        menu_bar_height, set()
    ) == {222}


def test_a_window_never_placed_on_a_screen_does_not_count_as_a_window(
    daemon, monkeypatch
):
    screen_bottom_left_corners = {(0.0, 1080.0)}
    window_info_list = [
        {
            "kCGWindowLayer": 0,
            "kCGWindowOwnerPID": 111,
            "kCGWindowBounds": {"X": 0.0, "Y": 580.0, "Width": 500.0, "Height": 500.0},
        },
        {
            "kCGWindowLayer": 0,
            "kCGWindowOwnerPID": 222,
            "kCGWindowBounds": {"X": 0.0, "Y": 30.0, "Width": 1920.0, "Height": 1050.0},
        },
        {
            "kCGWindowLayer": 0,
            "kCGWindowOwnerPID": 333,
            "kCGWindowBounds": {
                "X": 700.0,
                "Y": 400.0,
                "Width": 400.0,
                "Height": 400.0,
            },
        },
    ]
    monkeypatch.setattr(
        daemon.Quartz,
        "CGWindowListCopyWindowInfo",
        lambda *_arguments: window_info_list,
    )

    assert daemon.get_process_identifiers_with_visible_windows(
        30.0, screen_bottom_left_corners
    ) == {222, 333}
