from __future__ import annotations

import os
import select
import sys
import time

MILLISECONDS_PER_SECOND = 1000


def seconds_left_before(deadline):
    if deadline is None:
        return None
    return max(deadline - time.monotonic(), 0.0)


def _process_exit_through_pidfd(process_id, timeout_seconds):
    try:
        process_descriptor = os.pidfd_open(process_id)
    except ProcessLookupError:
        return True
    try:
        exit_poller = select.poll()
        exit_poller.register(process_descriptor, select.POLLIN)
        timeout_milliseconds = (
            None
            if timeout_seconds is None
            else timeout_seconds * MILLISECONDS_PER_SECOND
        )
        return bool(exit_poller.poll(timeout_milliseconds))
    finally:
        os.close(process_descriptor)


def _process_exit_through_kqueue(process_id, timeout_seconds):
    exit_queue = select.kqueue()
    exit_event = select.kevent(
        process_id,
        filter=select.KQ_FILTER_PROC,
        flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
        fflags=select.KQ_NOTE_EXIT,
    )
    try:
        return bool(exit_queue.control([exit_event], 1, timeout_seconds))
    except ProcessLookupError:
        return True
    finally:
        exit_queue.close()


def process_exits_within(process_id, timeout_seconds):
    if sys.platform == "darwin":
        return _process_exit_through_kqueue(process_id, timeout_seconds)
    return _process_exit_through_pidfd(process_id, timeout_seconds)


def every_process_exits_within(process_ids, timeout_seconds):
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    return all(
        process_exits_within(process_id, seconds_left_before(deadline))
        for process_id in process_ids
    )
