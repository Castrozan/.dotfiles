from unittest.mock import Mock

import pytest

import shorts_retention
import shorts_runner
from shorts_store import read_document, write_document

LARGE = shorts_retention.INTERMEDIATE_MINIMUM_BYTES
REFERENCED = (
    "final.mp4",
    "media/edited-narration.wav",
    "evidence/beats/00.png",
    "evidence/playback.json",
    "agent-events.jsonl",
)


def write_file(directory, name, size):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


@pytest.fixture
def finished_run(tmp_path):
    directory = tmp_path / "runs" / "2026-11-14-0900"
    directory.mkdir(parents=True)
    write_document(
        directory / "episode.json",
        {
            "video": "final.mp4",
            "narration": {"file": "media/edited-narration.wav", "start_seconds": 0},
            "beats": [{"frame": "evidence/beats/00.png"}],
            "review": {"full_playback": {"evidence": "evidence/playback.json"}},
        },
    )
    for name in REFERENCED:
        write_file(directory, name, LARGE)
    write_file(directory, "research/decision.json", LARGE - 1)
    write_file(directory, "bin/composition", LARGE)
    write_file(directory, "native-render/job/render.mp4", LARGE * 2)
    write_file(directory, "research/references/reference.mp4", LARGE)
    return directory


def test_published_run_keeps_only_referenced_and_small_files(finished_run):
    write_document(finished_run / "status.json", {"status": "published"})
    record = shorts_retention.discard_intermediates(finished_run)
    for name in REFERENCED + ("research/decision.json", "episode.json"):
        assert (finished_run / name).is_file()
    assert not (finished_run / "bin").exists()
    assert not (finished_run / "native-render").exists()
    assert not (finished_run / "research/references").exists()
    assert record["discarded_bytes"] == LARGE * 4
    assert read_document(finished_run / "retention.json") == record


@pytest.mark.parametrize("status", ["held", "needs_inspection", "agent_finished"])
def test_unpublished_run_keeps_everything_for_debugging(finished_run, status):
    write_document(finished_run / "status.json", {"status": status})
    assert shorts_retention.discard_intermediates(finished_run) is None
    assert (finished_run / "native-render/job/render.mp4").is_file()
    assert (finished_run / "bin/composition").is_file()
    assert not (finished_run / "retention.json").exists()


def test_symlinked_file_is_not_followed(finished_run, tmp_path):
    outside = write_file(tmp_path, "outside.bin", LARGE)
    (finished_run / "link.bin").symlink_to(outside)
    write_document(finished_run / "status.json", {"status": "published"})
    shorts_retention.discard_intermediates(finished_run)
    assert outside.is_file()
    assert (finished_run / "link.bin").is_symlink()


def scheduled_run(root, identifier):
    directory = root / "runs" / identifier
    directory.mkdir(parents=True)
    return directory


def test_pruning_keeps_newest_runs_and_queued_recoveries(tmp_path):
    identifiers = [f"2026-11-{day:02d}-0900" for day in range(1, 9)]
    for identifier in identifiers:
        scheduled_run(tmp_path, identifier)
    scheduled_run(tmp_path, "manual-notes")
    write_document(
        tmp_path / "recovery-queue.json",
        {
            "runs": [
                {"run_id": identifiers[0], "status": "queued"},
                {"run_id": identifiers[1], "status": "published"},
            ]
        },
    )
    pruned = shorts_retention.prune_runs(tmp_path)
    remaining = sorted(path.name for path in (tmp_path / "runs").iterdir())
    assert pruned == [identifiers[2], identifiers[1]]
    assert remaining == sorted([identifiers[0], *identifiers[3:], "manual-notes"])


def test_pruning_without_runs_is_a_no_op(tmp_path):
    assert shorts_retention.prune_runs(tmp_path) == []


def test_runner_trims_published_run_and_prunes_old_runs(tmp_path, monkeypatch):
    for day in range(1, 7):
        scheduled_run(tmp_path, f"2026-10-{day:02d}-0900")
    current = scheduled_run(tmp_path, "2026-11-14-0900")
    write_document(current / "status.json", {"status": "started"})

    def publish(*arguments, **options):
        write_document(
            current / "episode.json",
            {
                "video": "final.mp4",
                "narration": {"file": "n.wav"},
                "beats": [],
                "review": {},
            },
        )
        for name in ("final.mp4", "n.wav", "bin/composition"):
            write_file(current, name, LARGE)
        write_document(current / "status.json", {"status": "published"})
        return Mock(wait=Mock(return_value=0))

    monkeypatch.setattr(shorts_runner, "publisher_readiness", lambda *arguments: None)
    monkeypatch.setattr(
        shorts_runner,
        "claim_slot",
        lambda *arguments: shorts_runner.SlotClaim(current, None),
    )
    monkeypatch.setattr(shorts_runner, "browser_pages", lambda *arguments: Mock())
    monkeypatch.setattr(shorts_runner, "agent_arguments", lambda *arguments: [])
    monkeypatch.setattr(shorts_runner.subprocess, "Popen", publish)
    result = shorts_runner.start_run(tmp_path, 9, {})
    assert result["status"] == "published"
    assert result["pruned_runs"] == ["2026-10-02-0900", "2026-10-01-0900"]
    assert len(list((tmp_path / "runs").iterdir())) == 5
    assert (current / "final.mp4").is_file()
    assert not (current / "bin").exists()
