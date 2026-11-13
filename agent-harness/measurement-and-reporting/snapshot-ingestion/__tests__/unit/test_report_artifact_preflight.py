from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

import publish_report_artifacts as subject
from ingestion_snapshot_publisher import IngestionRefusedError
from test_publish_report_artifacts import publish, stubbed_collaborators, write_tree

FORBIDDEN_FILENAME_CHARACTERS = [chr(value) for value in range(1, 32)] + [
    chr(127),
    "\\",
]


@pytest.mark.parametrize("character", FORBIDDEN_FILENAME_CHARACTERS)
def test_unrepresentable_worker_keys_are_refused_before_any_publication(
    tmp_path, character
):
    directory = write_tree(tmp_path, {"asset.js": b"1", f"bad{character}.txt": b"2"})
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError):
            publish(directory)
    assert recorded.publications == []


@given(extra_units=st.integers(min_value=1, max_value=100))
def test_full_object_keys_above_worker_limit_are_refused_before_publication(
    extra_units,
):
    import tempfile

    from test_publish_report_artifacts import ALLOWED_PREFIX

    target_units = 512 + extra_units - len(ALLOWED_PREFIX)
    relative_path = f"{'a' * 200}/{'b' * 200}/{'c' * (target_units - 402)}"
    with tempfile.TemporaryDirectory() as root:
        directory = write_tree(root, {"asset.js": b"1", relative_path: b"2"})
        with stubbed_collaborators() as recorded:
            with pytest.raises(IngestionRefusedError):
                publish(directory)
    assert recorded.publications == []


def test_mutated_source_is_refused_before_its_body_is_published(tmp_path):
    directory = write_tree(tmp_path, {"index.html": b"before"})
    collect_sources = subject.collect_artifact_sources

    def collect_then_mutate(*arguments):
        sources = collect_sources(*arguments)
        (directory / "index.html").write_bytes(b"after!")
        return sources

    with stubbed_collaborators() as recorded:
        with patch.object(subject, "collect_artifact_sources", collect_then_mutate):
            with pytest.raises(IngestionRefusedError):
                publish(directory)
    assert recorded.publications == []


@pytest.mark.parametrize("extra_units", [0, 1])
def test_unicode_keys_use_the_workers_utf16_boundary(tmp_path, extra_units):
    from test_publish_report_artifacts import ALLOWED_PREFIX

    directory_segments = ["😀" * 50] * 4
    directory_prefix = "/".join(directory_segments) + "/"
    used_units = len(f"{ALLOWED_PREFIX}{directory_prefix}".encode("utf-16-le")) // 2
    relative_path = directory_prefix + "x" * (512 + extra_units - used_units)
    directory = write_tree(tmp_path, {relative_path: b"data"})
    with stubbed_collaborators() as recorded:
        if extra_units:
            with pytest.raises(IngestionRefusedError):
                publish(directory)
            assert recorded.publications == []
        else:
            manifest = publish(directory)
            assert (
                manifest["artifacts"][0]["objectKey"]
                == f"{ALLOWED_PREFIX}{relative_path}"
            )
