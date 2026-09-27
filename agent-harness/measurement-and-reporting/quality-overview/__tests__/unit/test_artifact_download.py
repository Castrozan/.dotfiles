from hashlib import sha256
import importlib.util
from pathlib import Path
import stat
import subprocess
import sys
from zipfile import ZipFile, ZipInfo

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "publishing/download_artifacts.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPECIFICATION = importlib.util.spec_from_file_location(
    "download_artifacts", MODULE_PATH
)
DOWNLOAD = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(DOWNLOAD)


def archive_at(path, entries):
    with ZipFile(path, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def test_exact_identifier_download_checks_digest_and_preserves_bytes(
    tmp_path, monkeypatch
):
    archive = tmp_path / "source.zip"
    digest = archive_at(
        archive,
        [("bats-unit/report.xml", b"<testsuite/>"), ("opaque.bin", b"\x00\xff")],
    )
    calls = []

    def github_download(command, **arguments):
        calls.append(command)
        arguments["stdout"].write(archive.read_bytes())

    monkeypatch.setattr(DOWNLOAD.subprocess, "run", github_download)
    destination = tmp_path / "bats-junit"
    DOWNLOAD.download_artifact({"id": 456, "digest": digest}, destination)
    assert calls == [
        [
            "gh",
            "api",
            "--method",
            "GET",
            "--",
            "repos/Castrozan/.dotfiles/actions/artifacts/456/zip",
        ]
    ]
    assert (destination / "opaque.bin").read_bytes() == b"\x00\xff"
    assert (destination / "bats-unit/report.xml").read_bytes() == b"<testsuite/>"
    assert not list(tmp_path.glob("quality-artifact-*"))


@pytest.mark.parametrize("name", ["../escape", "/absolute", "back\\slash"])
def test_unsafe_archive_paths_are_rejected_before_extraction(tmp_path, name):
    archive = tmp_path / "source.zip"
    digest = archive_at(archive, [("valid", "keep"), (name, "reject")])
    with pytest.raises(ValueError, match="unsafe"):
        DOWNLOAD.extract_archive(archive, tmp_path / "output", digest)
    assert not (tmp_path / "output").exists()


def test_symlinks_duplicates_and_extraction_limit_are_rejected(tmp_path, monkeypatch):
    archive = tmp_path / "source.zip"
    link = ZipInfo("link")
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    digest = archive_at(archive, [(link, "../escape")])
    with pytest.raises(ValueError, match="unsafe"):
        DOWNLOAD.extract_archive(archive, tmp_path / "output", digest)
    with pytest.warns(UserWarning, match="Duplicate"):
        digest = archive_at(archive, [("same", "one"), ("same", "two")])
    with pytest.raises(ValueError, match="duplicate"):
        DOWNLOAD.extract_archive(archive, tmp_path / "output", digest)
    digest = archive_at(archive, [("valid", "larger than limit")])
    monkeypatch.setattr(DOWNLOAD, "MAXIMUM_EXTRACTED_BYTES", 1)
    with pytest.raises(ValueError, match="limits"):
        DOWNLOAD.extract_archive(archive, tmp_path / "output", digest)


def test_corrupt_archive_is_rejected_before_extraction(tmp_path):
    archive = tmp_path / "source.zip"
    archive_at(archive, [("valid", "content")])
    with pytest.raises(ValueError, match="digest"):
        DOWNLOAD.extract_archive(archive, tmp_path / "output", "sha256:" + "0" * 64)
    assert not (tmp_path / "output").exists()


def test_one_failed_download_preserves_other_evidence_and_records_failure(
    tmp_path, monkeypatch
):
    calls = []

    def download(selection, destination):
        calls.append(selection["id"])
        if selection["id"] == 1:
            raise subprocess.TimeoutExpired("gh", 60)
        destination.mkdir()
        (destination / "report.xml").write_text("kept")

    monkeypatch.setattr(DOWNLOAD, "download_artifact", download)
    context = {
        "artifacts": {
            name: {"id": number, "digest": "sha256:" + "a" * 64}
            for number, name in enumerate(DOWNLOAD.ARTIFACT_PRODUCERS, 1)
        }
    }
    DOWNLOAD.download_selected(context, tmp_path)
    assert calls == [1, 2, 3, 4]
    assert context["artifacts"]["bats-junit"]["id"] is None
    assert "TimeoutExpired" in context["artifacts"]["bats-junit"]["reason"]
    assert (tmp_path / "python-junit/report.xml").read_text() == "kept"
