import json
import sys
import tempfile
from pathlib import Path

import pytest

import dotfiles_housekeeping_slices


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    written = []

    def write(relative_path, content):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)
        written.append(relative_path)

    monkeypatch.setattr(
        dotfiles_housekeeping_slices,
        "tracked_files",
        lambda _root, subtree: [name for name in written if name.startswith(subtree)],
    )
    return root, write


def run_slicer(monkeypatch, capsys, root, subtree):
    monkeypatch.setattr(
        sys,
        "argv",
        ["dotfiles-housekeeping-slices", "--root", str(root), "--subtree", subtree],
    )
    dotfiles_housekeeping_slices.main()
    return json.loads(capsys.readouterr().out)


def lines_of(count, word):
    return "\n".join(f"{word} {number}" for number in range(count)) + "\n"


def test_numbers_every_file_from_one_under_its_own_header(
    checkout, monkeypatch, capsys
):
    root, write = checkout
    write("module/first.py", "alpha\nbeta\n")
    write("module/second.py", "gamma\n")
    report = run_slicer(monkeypatch, capsys, root, "module")
    artifact = Path(report["slices"][0]).read_text()
    assert report["files"] == 2 and report["lines"] == 3
    assert "=== module/first.py (2 lines)\n    1  alpha\n    2  beta" in artifact
    assert "=== module/second.py (1 lines)\n    1  gamma" in artifact


def test_splits_into_one_slice_per_target_share_of_lines(checkout, monkeypatch, capsys):
    root, write = checkout
    for index in range(7):
        write(f"module/file_{index}.py", lines_of(1000, "line"))
    report = run_slicer(monkeypatch, capsys, root, "module")
    assert len(report["slices"]) == 3
    sliced_headers = [
        Path(artifact).read_text().count("=== ") for artifact in report["slices"]
    ]
    assert sum(sliced_headers) == 7


def test_skips_binary_and_oversized_files(checkout, monkeypatch, capsys):
    root, write = checkout
    write("module/kept.py", "kept\n")
    write("module/image.png", b"\x89PNG\x00data")
    write(
        "module/generated.json",
        lines_of(dotfiles_housekeeping_slices.MAXIMUM_LINES_PER_FILE + 1, "row"),
    )
    report = run_slicer(monkeypatch, capsys, root, "module")
    artifact = Path(report["slices"][0]).read_text()
    assert report["files"] == 1
    assert "image.png" not in artifact and "generated.json" not in artifact


def test_a_subtree_too_large_names_its_subdirectories_instead(
    checkout, monkeypatch, capsys
):
    root, write = checkout
    for index in range(14):
        write(f"tree/branch_{index % 2}/file_{index}.py", lines_of(3000, "line"))
    report = run_slicer(monkeypatch, capsys, root, "tree/")
    assert "slices" not in report
    assert report["error"].endswith(
        "audit one of its subdirectories instead: "
        "tree/branch_0 (21000 lines), tree/branch_1 (21000 lines)"
    )


def test_an_absolute_subtree_is_read_relative_to_the_root(
    checkout, monkeypatch, capsys
):
    root, write = checkout
    write("module/kept.py", "kept\n")
    report = run_slicer(monkeypatch, capsys, root, str(root / "module"))
    assert report["files"] == 1


def test_an_empty_subtree_reports_an_error(checkout, monkeypatch, capsys):
    root, _ = checkout
    report = run_slicer(monkeypatch, capsys, root, "missing")
    assert report == {"error": "missing holds no tracked text files"}
