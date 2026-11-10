import time
from pathlib import Path

from stale_entry_removal import CleanupPolicy, CleanupResult, StaleEntryRemover

TIMESTAMP_ORDERING_PAUSE_SECONDS = 0.01
AGENIX_TOP_LEVEL_NAMES = frozenset({"agenix", "agenix.d"})


def policy_treating_existing_entries_as_stale(
    temporary_directory: Path,
) -> CleanupPolicy:
    time.sleep(TIMESTAMP_ORDERING_PAUSE_SECONDS)
    stale_before_timestamp = time.time()
    time.sleep(TIMESTAMP_ORDERING_PAUSE_SECONDS)
    return CleanupPolicy(
        temporary_directory, stale_before_timestamp, AGENIX_TOP_LEVEL_NAMES
    )


def remove_everything_written_before_now(temporary_directory: Path) -> CleanupResult:
    policy = policy_treating_existing_entries_as_stale(temporary_directory)
    return StaleEntryRemover(policy).remove_stale_top_level_entries()
