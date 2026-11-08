import json

from hypothesis import given
from hypothesis import strategies as st

from origins.routing import origin_identifier, resolve_origin
from origins.transport import OriginTransport, OriginUnavailable
from origins.web_page import readable_text
from origins.x_com import x_status_reference
from origins.youtube import subtitle_choice, transcript_from_vtt, youtube_video_id

handles = st.from_regex(r"[A-Za-z0-9_]{1,15}", fullmatch=True)
status_ids = st.integers(min_value=1, max_value=10**19).map(str)
video_ids = st.from_regex(r"[A-Za-z0-9_-]{11}", fullmatch=True)


@given(handles, status_ids, st.sampled_from(["x.com", "twitter.com", "mobile.x.com"]))
def test_any_status_link_yields_its_author_and_id(handle, status_id, host):
    assert x_status_reference(f"https://{host}/{handle}/status/{status_id}?s=20") == (
        handle,
        status_id,
    )


@given(video_ids)
def test_every_youtube_link_shape_yields_the_same_video_id(video_id):
    links = [
        f"https://www.youtube.com/watch?v={video_id}&t=3",
        f"https://youtu.be/{video_id}",
        f"https://youtube.com/shorts/{video_id}?is=abc",
        f"https://m.youtube.com/watch?v={video_id}",
    ]
    assert {youtube_video_id(link) for link in links} == {video_id}
    assert origin_identifier(links[2]) == video_id


def scripted_transport(responses: dict) -> OriginTransport:
    def run(arguments: list[str]) -> str:
        key = next(
            (pattern for pattern in responses if pattern in " ".join(arguments)), None
        )
        if key is None:
            raise OriginUnavailable(f"unexpected command {arguments}")
        return responses[key]

    return OriginTransport(command_runner=run)


def test_an_x_post_reports_text_quote_media_and_expanded_links():
    post = {
        "tweet": {
            "text": "pass the lint",
            "author": {"screen_name": "alexgraveley"},
            "raw_text": {
                "facets": [{"type": "url", "replacement": "https://example.com/full"}]
            },
            "media": {"all": [{"type": "photo"}]},
            "quote": {"text": "91 paths to 12", "author": {"screen_name": "bentlegen"}},
            "article": {"title": "Complexity", "preview_text": "why"},
        }
    }
    transport = scripted_transport(
        {
            "api.fxtwitter.com/alexgraveley/status/9": json.dumps(post)
            + "\nu\napplication/json"
        }
    )

    origin = resolve_origin("https://x.com/alexgraveley/status/9", transport)

    assert origin["links"] == ["https://example.com/full"]
    assert origin["quoted"]["author"] == "bentlegen"
    assert origin["article"] == {"title": "Complexity", "preview": "why"}
    assert origin["needs_browser"] is False


def test_an_image_only_post_asks_for_the_browser():
    post = {"tweet": {"text": "", "media": {"all": [{"type": "photo"}]}}}
    transport = scripted_transport(
        {"fxtwitter": json.dumps(post) + "\nu\napplication/json"}
    )

    assert (
        resolve_origin("https://x.com/a/status/1", transport)["needs_browser"] is True
    )


def test_login_walled_and_failed_origins_ask_for_the_browser():
    assert (
        resolve_origin("https://www.instagram.com/reel/abc/", scripted_transport({}))[
            "needs_browser"
        ]
        is True
    )
    assert (
        resolve_origin("https://example.com/page", scripted_transport({}))[
            "needs_browser"
        ]
        is True
    )


def test_a_client_rendered_page_asks_for_the_browser_and_a_real_article_does_not():
    shell = "<html><head><title>App</title><script>var x</script></head><body><div id=root></div></body></html>"
    article = f"<html><head><title>Post</title></head><body><nav>menu</nav><p>{'word ' * 100}</p></body></html>"
    transport = scripted_transport(
        {
            "shell.example": f"{shell}\nhttps://shell.example\ntext/html",
            "post.example": f"{article}\nhttps://post.example/final\ntext/html",
        }
    )

    assert resolve_origin("https://shell.example", transport)["needs_browser"] is True
    read = resolve_origin("https://post.example", transport)
    assert read["needs_browser"] is False
    assert read["effective_url"] == "https://post.example/final"
    assert read["title"] == "Post"


def test_readable_text_skips_scripts_and_styles():
    title, text = readable_text(
        "<title>T</title><style>p{}</style><script>alert(1)</script><p>kept</p>"
    )

    assert (title, text) == ("T", "kept")


def test_auto_captions_collapse_repeated_cues_into_one_transcript():
    vtt = "WEBVTT\nKind: captions\n\n00:00:00.000 --> 00:00:01.000\nhello <c>there</c>\n\n00:00:01.000 --> 00:00:02.000\nhello there\n\n00:00:02.000 --> 00:00:03.000\ngeneral\n"

    assert transcript_from_vtt(vtt) == "hello there general"


def test_one_subtitle_track_is_chosen_to_stay_under_rate_limits():
    assert subtitle_choice(
        {
            "language": "en-US",
            "automatic_captions": {"fr-orig": [], "en-orig": [], "en": []},
        }
    ) == ("--write-auto-subs", "en-orig")
    assert subtitle_choice({"language": "pt", "subtitles": {"pt-BR": []}}) == (
        "--write-subs",
        "pt-BR",
    )
    assert subtitle_choice({"automatic_captions": {}}) is None


def test_a_deleted_post_asks_for_the_browser_with_its_reason():
    transport = scripted_transport(
        {
            "fxtwitter": json.dumps({"code": 404, "tweet": None})
            + "\nu\napplication/json"
        }
    )

    origin = resolve_origin("https://x.com/a/status/7", transport)

    assert origin["needs_browser"] is True
    assert "deleted" in origin["browser_reason"]
