import re

from render_baseline_dashboard_html import ATRIUM_QUALITY_URL, render_dashboard_html

SINGLE_REVISION = [
    {
        "date": "2026-01-01",
        "commit": "abc1234",
        "passed": 9,
        "total": 10,
        "rate": 90,
        "usage": {
            "invocations": 4,
            "measured_invocations": 4,
            "input_tokens": 120,
            "cached_input_tokens": 80,
            "cache_write_input_tokens": 10,
            "output_tokens": 20,
            "reasoning_output_tokens": 5,
        },
    }
]

SINGLE_REVISION_SUMMARY = {
    "latest": SINGLE_REVISION[0],
    "peak": {"rate": 90, "date": "2026-01-01", "commit": "abc1234"},
    "trough": {"rate": 90, "date": "2026-01-01", "commit": "abc1234"},
    "count": 1,
    "first_date": "2026-01-01",
    "last_date": "2026-01-01",
    "suite_min": 10,
    "suite_max": 10,
}


class TestBaselineDashboardLinksWhenFramedInsideAtrium:
    def test_has_no_relative_parent_links_that_404_on_the_bucket(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert re.findall(r'href="\.\.[^"]*"', html) == []

    def test_omits_the_self_contained_top_navigation_chrome(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert "<nav" not in html

    def test_quality_footer_link_targets_the_atrium_route_in_the_top_frame(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert (
            f'<a href="{ATRIUM_QUALITY_URL}" target="_top">how quality is measured</a>'
            in html
        )

    def test_external_design_notes_link_escapes_the_iframe(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert (
            '<a href="https://github.com/Castrozan/.dotfiles/issues/70" '
            'target="_top">design notes</a>' in html
        )


class TestBaselineDashboardGateAndFreshness:
    def test_surfaces_latest_eval_token_usage(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert "latest eval tokens" in html
        assert "120 input" in html
        assert "20 output" in html
        assert "4/4 measured" in html
        assert "input tokens" in html
        assert "cache write" in html
        assert "reasoning tokens" in html

    def test_lists_the_regression_delta_gate_alongside_the_floors(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert "previous baseline" in html
        assert "&le; 5%" in html

    def test_surfaces_the_latest_baseline_age_when_provided(self):
        html = render_dashboard_html(
            SINGLE_REVISION, SINGLE_REVISION_SUMMARY, latest_baseline_age_days=3
        )

        assert "3 days ago" in html
        assert "recorded 2026-01-01" in html

    def test_omits_the_freshness_line_without_an_age(self):
        html = render_dashboard_html(SINGLE_REVISION, SINGLE_REVISION_SUMMARY)

        assert "days ago" not in html
