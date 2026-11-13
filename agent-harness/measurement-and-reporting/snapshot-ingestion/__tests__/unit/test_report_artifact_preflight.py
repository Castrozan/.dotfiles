from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

import publish_report_artifacts as subject
import report_artifact_sources as artifact_sources
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


def test_tree_file_count_is_bounded_before_any_publication(tmp_path):
    directory = write_tree(
        tmp_path, {f"file-{index}.txt": b"" for index in range(1025)}
    )
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError):
            publish(directory)
    assert recorded.publications == []


def test_tree_total_bytes_are_bounded_before_any_publication(tmp_path):
    files = {f"file-{index}.bin": b"x" * 4_000_000 for index in range(8)}
    directory = write_tree(tmp_path, {**files, "extra.txt": b"x"})
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError):
            publish(directory)
    assert recorded.publications == []


def test_empty_directories_count_toward_the_traversal_bound(tmp_path):
    directory = write_tree(tmp_path, {"index.html": b"x"})
    for index in range(4096):
        (directory / f"empty-{index}").mkdir()
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError):
            publish(directory)
    assert recorded.publications == []


@given(
    file_sizes=st.lists(st.integers(min_value=0, max_value=8), max_size=8),
    empty_directory_count=st.integers(min_value=0, max_value=8),
    entry_limit=st.integers(min_value=1, max_value=12),
    file_limit=st.integers(min_value=1, max_value=8),
    byte_limit=st.integers(min_value=0, max_value=24),
)
def test_tree_budgets_refuse_exactly_when_whole_tree_totals_exceed_them(
    file_sizes, empty_directory_count, entry_limit, file_limit, byte_limit
):
    import tempfile

    from test_publish_report_artifacts import ALLOWED_PREFIX

    entry_total = 1 + len(file_sizes) + empty_directory_count
    within_budget = (
        bool(file_sizes)
        and entry_total <= entry_limit
        and len(file_sizes) <= file_limit
        and sum(file_sizes) <= byte_limit
    )
    budgets = {
        "MAXIMUM_REPORT_TREE_ENTRY_COUNT": entry_limit,
        "MAXIMUM_REPORT_TREE_FILE_COUNT": file_limit,
        "MAXIMUM_REPORT_TREE_BYTE_LENGTH": byte_limit,
    }
    with tempfile.TemporaryDirectory() as root:
        directory = Path(root) / "report"
        (directory / "nested").mkdir(parents=True)
        for index in range(empty_directory_count):
            (directory / f"empty-{index}").mkdir()
        for index, size in enumerate(file_sizes):
            (directory / "nested" / f"file-{index}.bin").write_bytes(b"x" * size)
        with patch.multiple(artifact_sources, **budgets):
            with stubbed_collaborators() as recorded:
                if within_budget:
                    manifest = publish(directory)
                else:
                    with pytest.raises(IngestionRefusedError):
                        publish(directory)
                    assert recorded.publications == []
    if within_budget:
        published_keys = sorted(
            artifact["objectKey"] for artifact in manifest["artifacts"]
        )
        expected_keys = sorted(
            f"{ALLOWED_PREFIX}nested/file-{index}.bin"
            for index in range(len(file_sizes))
        )
        assert published_keys == expected_keys


def test_file_count_at_the_default_bound_is_accepted(tmp_path):
    from test_publish_report_artifacts import ALLOWED_PREFIX

    directory = write_tree(
        tmp_path, {f"file-{index}.txt": b"" for index in range(1024)}
    )
    with stubbed_collaborators():
        manifest = publish(directory)
    assert len(manifest["artifacts"]) == 1024
    assert manifest["artifacts"][-1]["objectKey"].startswith(ALLOWED_PREFIX)


def test_entry_count_at_the_default_bound_is_accepted(tmp_path):
    from test_publish_report_artifacts import ALLOWED_PREFIX

    directory = write_tree(tmp_path, {"index.html": b"x"})
    for index in range(4095):
        (directory / f"empty-{index}").mkdir()
    with stubbed_collaborators():
        manifest = publish(directory)
    assert [artifact["objectKey"] for artifact in manifest["artifacts"]] == [
        f"{ALLOWED_PREFIX}index.html"
    ]


def test_total_bytes_at_the_default_bound_are_accepted(tmp_path):
    files = {f"file-{index}.bin": b"x" * 4_000_000 for index in range(8)}
    directory = write_tree(tmp_path, files)
    with stubbed_collaborators():
        manifest = publish(directory)
    assert len(manifest["artifacts"]) == 8
