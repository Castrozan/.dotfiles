import os
import time
from pathlib import Path

from continuous_integration_status import continuous_integration_status_for_revision
from cycle_commands import CommandRunner
from cycle_configuration import UPSTREAM_BRANCH, UPSTREAM_REFERENCE, CycleConfiguration
from cycle_facts import CycleFacts
from cycle_inbox import unread_local_messages
from cycle_jobs import active_job_scopes, rebuild_running
from cycle_records import (
    current_timestamp,
    read_record,
    read_text,
    revision_record_path,
    write_record,
)
from cycle_repository import Repository

TERMINAL_CONTINUOUS_INTEGRATION_STATES = ("passing", "failing")
LIVE_SYSTEM = Path("/run/current-system")


def settled_validation(record: dict | None, scopes: tuple[str, ...]) -> dict | None:
    if record and record.get("status") == "running" and not scopes:
        return {**record, "status": "transient"}
    return record


def settled_activation(
    record: dict | None, scopes: tuple[str, ...], live_toplevel: str
) -> dict | None:
    if record and record.get("status") == "running" and not scopes:
        status = "activated" if live_toplevel == record.get("toplevel") else "failed"
        return {**record, "status": status, "finished": current_timestamp()}
    return record


def continuous_integration_for(
    configuration: CycleConfiguration, runner: CommandRunner, revision: str
) -> dict:
    path = revision_record_path(
        configuration.continuous_integration_directory, revision
    )
    cached = read_record(path)
    if cached and cached.get("state") in TERMINAL_CONTINUOUS_INTEGRATION_STATES:
        return cached
    status = continuous_integration_status_for_revision(
        configuration.repository, revision, runner.run_capturing
    )
    if (
        not configuration.dry_run
        and status.get("state") in TERMINAL_CONTINUOUS_INTEGRATION_STATES
    ):
        write_record(path, status)
    return status


def head_activation(
    configuration: CycleConfiguration,
    head: str,
    scopes: tuple[str, ...],
    live_toplevel: str,
):
    path = revision_record_path(configuration.activations_directory, head)
    recorded = read_record(path)
    settled = settled_activation(recorded, scopes, live_toplevel)
    if settled is not recorded and not configuration.dry_run:
        write_record(path, settled)
    return settled


def synchronization_pending_seconds(
    configuration: CycleConfiguration, behind: int, now: float
) -> float:
    marker = configuration.synchronization_pending_file
    if not behind:
        if not configuration.dry_run:
            marker.unlink(missing_ok=True)
        return 0
    since = read_text(marker)
    if not since and not configuration.dry_run:
        marker.write_text(f"{now}\n")
    return now - float(since) if since else 0


def entrypoint_settled(entrypoint: Repository) -> bool:
    return (
        entrypoint.current_branch() == UPSTREAM_BRANCH
        and not entrypoint.operation_in_progress()
        and entrypoint.is_clean()
    )


def observe(
    configuration: CycleConfiguration, runner: CommandRunner, now: float | None = None
) -> CycleFacts:
    now = time.time() if now is None else now
    repository = Repository(configuration.repository, runner)
    scopes = active_job_scopes(runner, configuration.state_directory)
    entrypoint = Repository(configuration.entrypoint, runner)
    repository.fetch()
    entrypoint.fetch()
    head = repository.revision("HEAD")
    entrypoint_head = entrypoint.revision("HEAD")
    entrypoint_behind, entrypoint_ahead = entrypoint.divergence()
    upstream = repository.revision(UPSTREAM_REFERENCE)
    behind, ahead = repository.divergence()
    dirty_paths = repository.tracked_dirty_paths()
    newest_activity = max(
        repository.commit_time(head),
        repository.commit_time(upstream),
        repository.newest_modification_time(dirty_paths),
        entrypoint.commit_time(entrypoint_head),
    )
    last_green = read_text(configuration.last_green_file) or None
    validation = settled_validation(
        read_record(revision_record_path(configuration.validations_directory, head)),
        scopes,
    )
    live_toplevel = os.path.realpath(LIVE_SYSTEM)
    green = (validation or {}).get("status") == "green"
    synchronized_green = green and behind == 0
    return CycleFacts(
        branch=repository.current_branch(),
        operation_in_progress=repository.operation_in_progress(),
        active_job_scopes=scopes,
        head=head,
        upstream=upstream,
        behind=behind,
        ahead=ahead,
        dirty_paths=tuple(dirty_paths),
        newest_activity_age_seconds=now - newest_activity,
        oldest_unvalidated_age_seconds=0
        if last_green == head
        else now - repository.oldest_commit_time_since(last_green, head),
        head_validation=validation,
        recorded_rebase_conflict=read_record(configuration.rebase_conflict_file),
        unpublished_submodule_pins=tuple(repository.unpublished_submodule_pins(head))
        if synchronized_green and ahead
        else (),
        continuous_integration=continuous_integration_for(
            configuration, runner, upstream
        )
        if synchronized_green and not ahead
        else None,
        live_toplevel=live_toplevel,
        head_activation=head_activation(configuration, head, scopes, live_toplevel),
        operator_idle=configuration.idle_marker.exists(),
        rebuild_running=rebuild_running(),
        entrypoint_head=entrypoint_head,
        entrypoint_settled=entrypoint_settled(entrypoint),
        entrypoint_behind=entrypoint_behind,
        entrypoint_ahead=entrypoint_ahead,
        unread_local_messages=unread_local_messages(
            configuration.inbox_directory, configuration.peers_file
        ),
        synchronization_pending_seconds=synchronization_pending_seconds(
            configuration, behind, now
        ),
    )
