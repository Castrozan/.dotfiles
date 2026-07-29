import json

import ambient_canvas_browser as browser
import recorded_loop_capture_plan as capture_plan


def build_display_report(*display_entries):
    return json.dumps(
        {"SPDisplaysDataType": [{"spdisplays_ndrvs": list(display_entries)}]}
    )


def test_screen_dimensions_come_from_the_point_resolution_not_the_pixel_resolution():
    display_report = build_display_report(
        {
            "_spdisplays_resolution": "1512 x 982 @ 120.00Hz",
            "spdisplays_pixelresolution": "spdisplays_3024x1964Retina",
            "spdisplays_main": "spdisplays_yes",
        }
    )
    assert browser.parse_screen_dimensions(display_report) == (1512, 982)


def test_screen_dimensions_pick_the_main_display_over_an_attached_one():
    display_report = build_display_report(
        {"_spdisplays_resolution": "3840 x 2160 @ 60.00Hz"},
        {
            "_spdisplays_resolution": "1512 x 982 @ 120.00Hz",
            "spdisplays_main": "spdisplays_yes",
        },
    )
    assert browser.parse_screen_dimensions(display_report) == (1512, 982)


def test_screen_dimensions_fall_back_to_the_first_display_without_a_main_flag():
    display_report = build_display_report(
        {"_spdisplays_resolution": "1920 x 1080 @ 165.00Hz"}
    )
    assert browser.parse_screen_dimensions(display_report) == (1920, 1080)


def test_screen_dimensions_fall_back_when_no_display_is_reported():
    assert browser.parse_screen_dimensions(build_display_report()) == (
        browser.FALLBACK_SCREEN_WIDTH,
        browser.FALLBACK_SCREEN_HEIGHT,
    )


def test_screen_dimensions_fall_back_when_the_report_is_not_json():
    assert browser.parse_screen_dimensions("not a display report") == (
        browser.FALLBACK_SCREEN_WIDTH,
        browser.FALLBACK_SCREEN_HEIGHT,
    )


def test_screen_dimensions_fall_back_when_the_resolution_is_unparseable():
    display_report = build_display_report({"_spdisplays_resolution": "unknown"})
    assert browser.parse_screen_dimensions(display_report) == (
        browser.FALLBACK_SCREEN_WIDTH,
        browser.FALLBACK_SCREEN_HEIGHT,
    )


def test_reading_screen_dimensions_never_shells_out_to_finder_automation():
    assert "osascript" not in browser.DISPLAY_REPORT_COMMAND
    assert browser.DISPLAY_REPORT_COMMAND[0].endswith("system_profiler")
    assert browser.DISPLAY_REPORT_TIMEOUT_SECONDS > 0


def test_centered_geometry_is_fraction_of_screen_and_centered():
    width, height, left, top = browser.resolve_centered_window_geometry(2000, 1000)
    assert width == 1440
    assert height == 720
    assert left == 280
    assert top == 140


def test_capture_pixel_dimensions_are_unchanged_on_a_sixteen_by_nine_display():
    assert capture_plan.resolve_capture_pixel_dimensions(1920, 1080) == (1920, 1080)


def test_capture_pixel_dimensions_follow_a_three_by_two_display():
    assert capture_plan.resolve_capture_pixel_dimensions(1512, 982) == (1662, 1080)


def test_capture_pixel_width_stays_even_so_the_encoder_accepts_every_display():
    for screen_width in range(1000, 4000, 7):
        capture_width, _ = capture_plan.resolve_capture_pixel_dimensions(
            screen_width, 982
        )
        assert capture_width % 2 == 0


def test_capture_aspect_tracks_the_display_within_one_pixel():
    capture_width, capture_height = capture_plan.resolve_capture_pixel_dimensions(
        1512, 982
    )
    assert abs(capture_width - capture_height * 1512 / 982) <= 1


def test_capture_pixel_dimensions_fall_back_when_the_screen_reads_degenerate():
    assert capture_plan.resolve_capture_pixel_dimensions(0, 0) == (
        capture_plan.FALLBACK_CAPTURE_PIXEL_WIDTH,
        capture_plan.CAPTURE_PIXEL_HEIGHT,
    )
