import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "scripts"
    / "record-capture-verdict.py"
)
module_specification = importlib.util.spec_from_file_location(
    "record_capture_verdict", SCRIPT_PATH
)
loaded_verdict_recording_module = importlib.util.module_from_spec(module_specification)
assert module_specification.loader is not None
module_specification.loader.exec_module(loaded_verdict_recording_module)


def write_capture(capture_inbox_directory: Path, name: str, body: str) -> Path:
    capture_inbox_directory.mkdir(parents=True, exist_ok=True)
    capture_path = capture_inbox_directory / name
    capture_path.write_text(body, encoding="utf-8")
    return capture_path


def test_the_verdict_block_is_appended_as_queryable_inline_fields(tmp_path):
    capture_path = write_capture(tmp_path, "Tweet from A.md", "captured body\n")

    recording_outcome = loaded_verdict_recording_module.record_capture_verdict(
        capture_path, "adopt", "wired into the herdr module", "Second Brain/Atlas/Tools"
    )

    assert recording_outcome == "recorded"
    assert capture_path.read_text(encoding="utf-8") == (
        "captured body\n\n"
        "#agent-work-done\n"
        "verdict:: adopt\n"
        "outcome:: wired into the herdr module\n"
        "entry:: [[Second Brain/Atlas/Tools]]\n"
    )


def test_an_omitted_entry_leaves_the_link_field_out(tmp_path):
    capture_path = write_capture(tmp_path, "Tweet from A.md", "captured body\n")

    loaded_verdict_recording_module.record_capture_verdict(
        capture_path, "drop", "dead link", None
    )

    assert "entry::" not in capture_path.read_text(encoding="utf-8")


def test_an_entry_already_wrapped_in_brackets_is_not_double_wrapped(tmp_path):
    capture_path = write_capture(tmp_path, "Tweet from A.md", "captured body\n")

    loaded_verdict_recording_module.record_capture_verdict(
        capture_path, "reference", "filed only", "[[Second Brain/Atlas/Tools]]"
    )

    assert "entry:: [[Second Brain/Atlas/Tools]]\n" in capture_path.read_text(
        encoding="utf-8"
    )


def test_an_already_recorded_capture_is_refused_rather_than_stamped_twice(tmp_path):
    capture_path = write_capture(
        tmp_path,
        "Tweet from A.md",
        "captured body\n\n#agent-work-done\nverdict:: drop\n",
    )
    body_before_recording = capture_path.read_text(encoding="utf-8")

    recording_outcome = loaded_verdict_recording_module.record_capture_verdict(
        capture_path, "adopt", "second opinion", None
    )

    assert recording_outcome == "already-recorded"
    assert capture_path.read_text(encoding="utf-8") == body_before_recording


def test_a_capture_resolves_by_bare_name_by_stem_and_by_full_path(tmp_path):
    capture_path = write_capture(tmp_path, "Tweet from A.md", "captured body\n")

    assert (
        loaded_verdict_recording_module.resolve_capture_path(
            tmp_path, "Tweet from A.md"
        )
        == capture_path
    )
    assert (
        loaded_verdict_recording_module.resolve_capture_path(tmp_path, "Tweet from A")
        == capture_path
    )
    assert loaded_verdict_recording_module.resolve_capture_path(
        tmp_path, str(capture_path)
    ) == Path(str(capture_path))


def test_an_unresolvable_capture_fails_loudly(tmp_path):
    with pytest.raises(FileNotFoundError):
        loaded_verdict_recording_module.resolve_capture_path(tmp_path, "absent capture")
