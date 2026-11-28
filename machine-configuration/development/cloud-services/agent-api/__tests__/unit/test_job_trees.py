import io
import tarfile
import uuid

import pytest

from agent_api_job.errors import JobError
from agent_api_job.storage import write_json
from agent_api_job.transfer import send_path
from agent_api_job.trees import DEFAULT_MAXIMUM_BYTES, receive_tree

TREE_KEY = "ab" * 16


def archive_of(files):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    stream.seek(0)
    return stream


def archive_with_members(members):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for member in members:
            archive.addfile(member, io.BytesIO(b"x" * member.size))
    stream.seek(0)
    return stream


def file_member(name):
    member = tarfile.TarInfo(name)
    member.size = 1
    return member


def symlink_member(name, target):
    member = tarfile.TarInfo(name)
    member.type = tarfile.SYMTYPE
    member.linkname = str(target)
    return member


def test_receive_deletes_a_file_the_previous_copy_delivered_and_keeps_a_job_file(
    tmp_path,
):
    root = tmp_path / "state"
    receive_tree(
        root,
        TREE_KEY,
        archive_of({"kept.txt": b"one", "src/dropped.c": b"two"}),
        DEFAULT_MAXIMUM_BYTES,
    )
    tree = root / "trees" / TREE_KEY
    (tree / "build-output.bin").write_bytes(b"made by the job")
    receive_tree(
        root, TREE_KEY, archive_of({"kept.txt": b"three"}), DEFAULT_MAXIMUM_BYTES
    )
    assert not (tree / "src/dropped.c").exists()
    assert (tree / "build-output.bin").read_bytes() == b"made by the job"
    assert (tree / "kept.txt").read_bytes() == b"three"


def escaping_members(outside):
    return {
        "parent": [file_member("../escape.txt")],
        "absolute": [file_member(str(outside / "escape.txt"))],
        "symlink": [
            symlink_member("link", outside),
            file_member("link/escape.txt"),
        ],
    }


@pytest.mark.parametrize("escape", ["parent", "absolute", "symlink"])
def test_receive_refuses_a_member_that_escapes_the_tree(tmp_path, escape):
    outside = tmp_path / "outside"
    outside.mkdir()
    stream = archive_with_members(escaping_members(outside)[escape])
    with pytest.raises(JobError, match="unsafe_member"):
        receive_tree(tmp_path / "state", TREE_KEY, stream, DEFAULT_MAXIMUM_BYTES)
    assert list(tmp_path.rglob("escape.txt")) == []


def test_send_refuses_a_path_outside_the_job_working_directory(tmp_path):
    root = tmp_path / "state"
    job = str(uuid.uuid4())
    working_directory = tmp_path / "work"
    working_directory.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    (working_directory / "link").symlink_to(secret)
    job_directory = root / "jobs" / job
    job_directory.mkdir(parents=True)
    write_json(
        job_directory / "spec.json",
        {"runner": "supervisor", "working_directory": str(working_directory)},
    )
    for path in ("../secret.txt", str(secret), "link"):
        stream = io.BytesIO()
        with pytest.raises(JobError, match="invalid_path"):
            send_path(root, job, path, stream)
        assert stream.getvalue() == b""
