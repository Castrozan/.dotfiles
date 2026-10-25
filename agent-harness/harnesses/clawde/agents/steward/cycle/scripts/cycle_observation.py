import os
from pathlib import Path

from continuous_integration_status import continuous_integration_status_for_revision
from cycle_commands import CommandRunner
from cycle_configuration import UPSTREAM_REFERENCE, CycleConfiguration
from cycle_entrypoint import observe_entrypoint
from cycle_facts import CycleFacts
from cycle_jobs import active_jobs, rebuild_running
from cycle_operator import operator_idle, unread_local_messages
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


def forget_synchronization_pending(configuration: CycleConfiguration) -> None:
    if not configuration.dry_run:
        configuration.synchronization_pending_file.unlink(missing_ok=True)


def remember_synchronization_pending(
    configuration: CycleConfiguration, now: float
) -> str:
    if not configuration.dry_run:
        configuration.synchronization_pending_file.write_text(f"{now}\n")
    return str(now)


def synchronization_pending_seconds(
    configuration: CycleConfiguration, behind: int, now: float
) -> float:
    if not behind:
        forget_synchronization_pending(configuration)
        return 0
    since = read_text(
        configuration.synchronization_pending_file
    ) or remember_synchronization_pending(configuration, now)
    return now - float(since)


def oldest_unvalidated_age_seconds(
    repository: Repository, last_green: str, head: str, now: float
) -> float:
    if last_green == head:
        return 0
    return now - repository.oldest_commit_time_since(last_green, head)


def publication_facts(
    configuration: CycleConfiguration,
    runner: CommandRunner,
    repository: Repository,
    validation: dict | None,
    revisions: tuple[str, str, int, int],
) -> dict:
    head, upstream, behind, ahead = revisions
    if (validation or {}).get("status") != "green" or behind:
        return {}
    if ahead:
        pins = repository.unpublished_submodule_pins(head)
        return {"unpublished_submodule_pins": tuple(pins)}
    return {
        "continuous_integration": continuous_integration_for(
            configuration, runner, upstream
        )
    }


def observe(
    configuration: CycleConfiguration, runner: CommandRunner, now: float
) -> CycleFacts:
    repository = Repository(configuration.repository, runner)
    scopes = active_jobs(configuration, runner)
    repository.fetch()
    entrypoint = observe_entrypoint(configuration, runner)
    head = repository.revision("HEAD")
    upstream = repository.revision(UPSTREAM_REFERENCE)
    behind, ahead = repository.divergence()
    dirty_paths = repository.tracked_dirty_paths()
    newest_activity = max(
        repository.commit_time(head),
        repository.commit_time(upstream),
        repository.newest_modification_time(dirty_paths),
        entrypoint.commit_time,
    )
    last_green = read_text(configuration.last_green_file)
    validation = settled_validation(
        read_record(revision_record_path(configuration.validations_directory, head)),
        scopes,
    )
    live_toplevel = os.path.realpath(LIVE_SYSTEM)
    return CycleFacts(
        branch=repository.current_branch(),
        operation_in_progress=repository.operation_in_progress(),
        active_job_scopes=scopes,
        head=head,
        upstream=upstream,
        behind=behind,
        ahead=ahead,
        tracked_dirty=bool(dirty_paths),
        newest_activity_age_seconds=now - newest_activity,
        oldest_unvalidated_age_seconds=oldest_unvalidated_age_seconds(
            repository, last_green, head, now
        ),
        head_validation=validation,
        recorded_rebase_conflict=read_record(configuration.rebase_conflict_file),
        live_toplevel=live_toplevel,
        head_activation=head_activation(configuration, head, scopes, live_toplevel),
        operator_idle=operator_idle(configuration, runner),
        rebuild_running=rebuild_running(runner, configuration.state_directory),
        **entrypoint.as_facts(),
        unread_local_messages=unread_local_messages(
            configuration.inbox_directory, configuration.peers_file
        ),
        synchronization_pending_seconds=synchronization_pending_seconds(
            configuration, behind, now
        ),
        **publication_facts(
            configuration,
            runner,
            repository,
            validation,
            (head, upstream, behind, ahead),
        ),
    )
