import json
import threading
import time

import pytest

from recording import recorded_loop_capture_pool as capture_pool
from recording.recorded_loop_capture_plan import RecordingWorker


@pytest.mark.parametrize(
    ("processor_count", "worker_count"), [(None, 1), (1, 1), (4, 2), (32, 4)]
)
def test_capture_pool_is_bounded_by_processor_count(
    monkeypatch, processor_count, worker_count
):
    monkeypatch.setattr(capture_pool.os, "cpu_count", lambda: processor_count)
    assert capture_pool.resolve_recording_worker_count() == worker_count


def test_workers_overlap_and_share_one_deadline(monkeypatch):
    barrier = threading.Barrier(2)
    observed_workers = []
    manifest_bytes = json.dumps(
        {"segments": [{"fingerprint": "current", "durationSeconds": 1}]}
    ).encode()

    def drive_browser(*arguments):
        worker, deadline = arguments[-3:-1]
        barrier.wait(timeout=2)
        observed_workers.append((worker, deadline))
        return manifest_bytes

    monkeypatch.setattr(capture_pool, "resolve_recording_worker_count", lambda: 2)
    monkeypatch.setattr(capture_pool, "drive_record_browser", drive_browser)
    before = time.monotonic()
    assert capture_pool.capture_recorded_playlist(*([None] * 4)) == manifest_bytes
    assert {worker for worker, deadline in observed_workers} == {
        RecordingWorker(0, 2),
        RecordingWorker(1, 2),
    }
    deadlines = {deadline for worker, deadline in observed_workers}
    assert len(deadlines) == 1
    assert before + 1800 <= deadlines.pop() <= time.monotonic() + 1800


@pytest.mark.parametrize(
    "other_manifest", [None, b"{}", b"invalid", b'{"segments": []}']
)
def test_an_incomplete_worker_prevents_publication(monkeypatch, other_manifest):
    complete_manifest = (
        b'{"segments": [{"fingerprint": "current", "durationSeconds": 1}]}'
    )
    monkeypatch.setattr(capture_pool, "resolve_recording_worker_count", lambda: 2)
    monkeypatch.setattr(
        capture_pool,
        "drive_record_browser",
        lambda *arguments: (
            complete_manifest if arguments[-3].index == 0 else other_manifest
        ),
    )
    assert capture_pool.capture_recorded_playlist(*([None] * 4)) is None


def test_conflicting_worker_plans_prevent_publication(monkeypatch):
    monkeypatch.setattr(capture_pool, "resolve_recording_worker_count", lambda: 2)
    monkeypatch.setattr(
        capture_pool,
        "drive_record_browser",
        lambda *arguments: json.dumps(
            {
                "segments": [
                    {"fingerprint": str(arguments[-3].index), "durationSeconds": 1}
                ]
            }
        ).encode(),
    )
    assert capture_pool.capture_recorded_playlist(*([None] * 4)) is None


def test_worker_failure_cancels_its_siblings(monkeypatch):
    barrier = threading.Barrier(2)
    cancelled_workers = []

    def drive_browser(*arguments):
        worker, deadline, cancellation_event = arguments[-3:]
        barrier.wait(timeout=2)
        if worker.index == 0:
            raise OSError("browser failed")
        assert cancellation_event.wait(timeout=2)
        cancelled_workers.append(worker.index)

    monkeypatch.setattr(capture_pool, "resolve_recording_worker_count", lambda: 2)
    monkeypatch.setattr(capture_pool, "drive_record_browser", drive_browser)
    assert capture_pool.capture_recorded_playlist(*([None] * 4)) is None
    assert cancelled_workers == [1]
