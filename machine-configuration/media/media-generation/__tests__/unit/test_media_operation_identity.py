import json

import pytest

import media_image_cli
from media_image.contract import ImageError
from media_movie.discovery import example_movie_request
from media_movie.request_reader import read_movie_request


@pytest.mark.parametrize("value", ["", None, False, 0, "bad", "../escape"])
def test_supplied_movie_identity_is_validated_before_any_dispatch(value):
    document = example_movie_request()
    document["operation_id"] = value
    with pytest.raises(ImageError, match="invalid_operation_id"):
        read_movie_request(document)


def test_empty_image_identity_does_not_read_credentials_or_dispatch(
    tmp_path, monkeypatch, capsys
):
    def fail_factory(provider):
        pytest.fail("invalid operation reached provider factory")

    monkeypatch.setattr(media_image_cli, "create_image_provider", fail_factory)
    assert (
        media_image_cli.main(
            [
                "--state-directory",
                str(tmp_path),
                "generate",
                "--provider",
                "openai",
                "--model",
                "gpt-image-2.5-flare",
                "--aspect-ratio",
                "1:1",
                "--quality",
                "low",
                "--prompt",
                "Mountain",
                "--operation-id",
                "",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().err)["error"] == "invalid_operation_id"
    assert not list(tmp_path.iterdir())
