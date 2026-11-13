import hashlib
import json
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import publish_report_artifacts as subject
from ingestion_snapshot_publisher import IngestionRefusedError
from test_publish_report_artifacts import (
    ALLOWED_PREFIX,
    REVISION,
    RUN_ATTEMPT,
    RUN_ID,
    make_payload,
    publish,
    stubbed_collaborators,
    write_tree,
)

DIRECTORY_NAMES = ["assets", "données"]
LEAF_NAMES = st.text(
    alphabet=st.characters(exclude_categories=("Cs", "Cc"), exclude_characters="/\\"),
    min_size=1,
    max_size=10,
).filter(lambda name: name not in (".", ".."))


def sha256_of(body_bytes):
    return hashlib.sha256(body_bytes).hexdigest()


def test_publishes_nested_unicode_and_binary_files_with_exact_bytes(tmp_path):
    binary_body = bytes(range(256))
    unicode_json_body = '{"naïve": true}'.encode("utf-8")
    directory = write_tree(
        tmp_path,
        {
            "index.html": b"<html>entry</html>",
            "assets/données.json": unicode_json_body,
            "assets/blob.bin": binary_body,
        },
    )
    with stubbed_collaborators() as recorded:
        manifest = publish(directory)
    assert [publication.object_key for publication in recorded.publications] == [
        f"{ALLOWED_PREFIX}assets/blob.bin",
        f"{ALLOWED_PREFIX}assets/données.json",
        f"{ALLOWED_PREFIX}index.html",
    ]
    assert [publication.body_bytes for publication in recorded.publications] == [
        binary_body,
        unicode_json_body,
        b"<html>entry</html>",
    ]
    assert manifest == {
        "workflow": {
            "repository": "Castrozan/.dotfiles",
            "revision": REVISION,
            "runId": RUN_ID,
            "runAttempt": RUN_ATTEMPT,
        },
        "artifacts": [
            {
                "objectKey": f"{ALLOWED_PREFIX}assets/blob.bin",
                "byteLength": 256,
                "sha256": sha256_of(binary_body),
                "contentType": "application/octet-stream",
            },
            {
                "objectKey": f"{ALLOWED_PREFIX}assets/données.json",
                "byteLength": len(unicode_json_body),
                "sha256": sha256_of(unicode_json_body),
                "contentType": "application/json",
            },
            {
                "objectKey": f"{ALLOWED_PREFIX}index.html",
                "byteLength": len(b"<html>entry</html>"),
                "sha256": sha256_of(b"<html>entry</html>"),
                "contentType": "text/html",
            },
        ],
    }


def test_partial_publication_failure_raises_after_only_acknowledged_artifacts(tmp_path):
    directory = write_tree(tmp_path, {"assets/app.js": b"1", "index.html": b"2"})
    with stubbed_collaborators(
        failing_object_keys=frozenset({f"{ALLOWED_PREFIX}index.html"})
    ) as recorded:
        with pytest.raises(IngestionRefusedError, match="index.html"):
            publish(directory)
    assert [publication.object_key for publication in recorded.publications] == [
        f"{ALLOWED_PREFIX}assets/app.js"
    ]


def test_cli_prints_manifest_and_exits_zero(tmp_path, capsys):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(make_payload()), encoding="utf-8")
    directory = write_tree(tmp_path / "tree", {"index.html": b"<html>"})
    with stubbed_collaborators():
        exit_status = subject.main([str(payload_path), str(directory), ALLOWED_PREFIX])
    printed = capsys.readouterr().out
    assert exit_status == 0
    assert (
        json.loads(printed)["artifacts"][0]["objectKey"]
        == f"{ALLOWED_PREFIX}index.html"
    )
    assert "test-secret" not in printed


def test_cli_exits_nonzero_on_refusal_and_on_wrong_arity(tmp_path, capsys):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(make_payload()), encoding="utf-8")
    directory = write_tree(tmp_path / "tree", {"index.html": b"<html>"})
    refusal = IngestionRefusedError("identity refused")
    with stubbed_collaborators(refused_environment=refusal):
        refused_status = subject.main(
            [str(payload_path), str(directory), ALLOWED_PREFIX]
        )
    assert refused_status == 1
    assert "identity refused" in capsys.readouterr().err
    assert subject.main([str(payload_path)]) == 1


@settings(max_examples=40, deadline=None)
@given(
    files=st.dictionaries(
        st.tuples(st.sampled_from(DIRECTORY_NAMES), LEAF_NAMES).map("/".join),
        st.binary(max_size=200),
        min_size=1,
        max_size=8,
    )
)
def test_every_nested_tree_publishes_exact_keys_bytes_and_digests(files):
    with tempfile.TemporaryDirectory() as root:
        directory = write_tree(root, files)
        with stubbed_collaborators() as recorded:
            manifest = publish(directory)
    published_bodies = {
        publication.object_key: publication.body_bytes
        for publication in recorded.publications
    }
    assert published_bodies == {
        f"{ALLOWED_PREFIX}{relative_path}": body_bytes
        for relative_path, body_bytes in files.items()
    }
    manifest_digests = {
        artifact["objectKey"]: (artifact["byteLength"], artifact["sha256"])
        for artifact in manifest["artifacts"]
    }
    assert manifest_digests == {
        f"{ALLOWED_PREFIX}{relative_path}": (len(body_bytes), sha256_of(body_bytes))
        for relative_path, body_bytes in files.items()
    }
