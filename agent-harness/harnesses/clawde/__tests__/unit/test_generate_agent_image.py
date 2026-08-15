import base64
from datetime import date

import generate_agent_image
import pytest
from agent_media_workspace import MediaRequestRefused

TODAY = date(2026, 8, 15)


def stub_provider(monkeypatch, recorder, attribute="post_json"):
    def answer(*call, **_):
        recorder.append(call)
        return {"data": [{"b64_json": base64.b64encode(b"png-bytes").decode()}]}

    monkeypatch.setattr(generate_agent_image, attribute, answer)


def image_arguments(**overrides):
    flags = [item for pair in overrides.items() for item in pair]
    return generate_agent_image.parse_command_line_arguments(
        ["--prompt", "um gato irritado", *flags]
    )


def test_a_drawn_image_lands_in_the_workspace(media_agent_workspace, monkeypatch):
    calls = []
    stub_provider(monkeypatch, calls)

    media_file = generate_agent_image.generate_agent_image(
        media_agent_workspace, image_arguments(), TODAY
    )

    assert media_file.parent == media_agent_workspace / "media"
    assert media_file.read_bytes() == b"png-bytes"
    assert calls[0][0] == generate_agent_image.GENERATIONS_URL


def test_a_reference_switches_the_call_to_editing(media_agent_workspace, monkeypatch):
    earlier = media_agent_workspace / "media" / "image-earlier.png"
    earlier.parent.mkdir(parents=True)
    earlier.write_bytes(b"png")
    calls = []
    stub_provider(monkeypatch, calls, attribute="post_multipart")

    generate_agent_image.generate_agent_image(
        media_agent_workspace, image_arguments(**{"--reference": str(earlier)}), TODAY
    )

    assert calls[0][0] == generate_agent_image.EDITS_URL
    assert calls[0][3] == [("image[]", earlier.resolve(), "image/png")]


def test_a_reference_the_provider_cannot_read_is_refused(
    media_agent_workspace, monkeypatch
):
    animated = media_agent_workspace / "media" / "image-earlier.gif"
    animated.parent.mkdir(parents=True)
    animated.write_bytes(b"gif")
    calls = []
    stub_provider(monkeypatch, calls, attribute="post_multipart")

    with pytest.raises(MediaRequestRefused, match="has to be a"):
        generate_agent_image.generate_agent_image(
            media_agent_workspace,
            image_arguments(**{"--reference": str(animated)}),
            TODAY,
        )

    assert calls == []


def test_a_reference_off_the_machine_is_refused_before_any_call(
    media_agent_workspace, tmp_path
):
    stranger = tmp_path / "id_rsa"
    stranger.write_text("private", encoding="utf-8")

    with pytest.raises(MediaRequestRefused, match="refusing to upload"):
        generate_agent_image.generate_agent_image(
            media_agent_workspace,
            image_arguments(**{"--reference": str(stranger)}),
            TODAY,
        )


def test_a_provider_answering_with_no_image_is_reported(
    media_agent_workspace, monkeypatch
):
    monkeypatch.setattr(
        generate_agent_image, "post_json", lambda *_, **__: {"data": []}
    )

    with pytest.raises(MediaRequestRefused, match="no image"):
        generate_agent_image.generate_agent_image(
            media_agent_workspace, image_arguments(), TODAY
        )


def test_a_spent_budget_stops_the_call_rather_than_the_download(
    media_agent_workspace, monkeypatch
):
    calls = []
    stub_provider(monkeypatch, calls)
    monkeypatch.setattr(generate_agent_image, "DAILY_LIMIT", 1)

    generate_agent_image.generate_agent_image(
        media_agent_workspace, image_arguments(), TODAY
    )
    with pytest.raises(MediaRequestRefused, match="budget is spent"):
        generate_agent_image.generate_agent_image(
            media_agent_workspace, image_arguments(), TODAY
        )

    assert len(calls) == 1
