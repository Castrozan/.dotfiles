from cycle_commands import CommandRunner
from cycle_configuration import CycleConfiguration
from cycle_facts import CycleDecision, CycleFacts
from cycle_jobs import launch_activation, launch_validation
from cycle_records import (
    current_timestamp,
    remove_record,
    revision_log_path,
    revision_record_path,
    write_record,
)
from cycle_repository import Repository


def fast_forward(repository: Repository, with_submodules: bool = True) -> str:
    merged = repository.merge_fast_forward()
    if not merged.succeeded:
        return f"fast-forward refused: {merged.explanation}"
    if with_submodules:
        repository.update_submodules()
    return "fast-forwarded"


def rebase(
    configuration: CycleConfiguration, repository: Repository, facts: CycleFacts
) -> str:
    outcome = repository.rebase_onto_upstream()
    if outcome == "conflict":
        write_record(
            configuration.rebase_conflict_file,
            {
                "head": facts.head,
                "upstream": facts.upstream,
                "observed": current_timestamp(),
            },
        )
    if outcome == "rebased":
        remove_record(configuration.rebase_conflict_file)
        repository.update_submodules()
    return outcome


def validate(
    configuration: CycleConfiguration,
    runner: CommandRunner,
    facts: CycleFacts,
    attempt: int,
    cycle_command: list[str],
) -> str:
    write_record(
        revision_record_path(configuration.validations_directory, facts.head),
        {
            "revision": facts.head,
            "status": "running",
            "attempt": attempt,
            "started": current_timestamp(),
            "log": str(
                revision_log_path(configuration.validations_directory, facts.head)
            ),
        },
    )
    launch_validation(configuration, runner, facts.head, attempt, cycle_command)
    return f"validation attempt {attempt} launched"


def push(repository: Repository, revision: str) -> str:
    pushed = repository.push(revision)
    return "pushed" if pushed.succeeded else f"push refused: {pushed.explanation}"


def activate(
    configuration: CycleConfiguration, runner: CommandRunner, facts: CycleFacts
) -> str:
    write_record(
        revision_record_path(configuration.activations_directory, facts.head),
        {
            "revision": facts.head,
            "status": "running",
            "toplevel": (facts.head_validation or {}).get("toplevel", ""),
            "started": current_timestamp(),
            "log": str(
                revision_log_path(configuration.activations_directory, facts.head)
            ),
        },
    )
    launch_activation(configuration, runner, facts.head)
    return "activation launched"


def execute(
    decision: CycleDecision,
    facts: CycleFacts,
    configuration: CycleConfiguration,
    runner: CommandRunner,
    cycle_command: list[str],
) -> str:
    repository = Repository(configuration.repository, runner)
    entrypoint = Repository(configuration.entrypoint, runner)
    if decision.action == "fast-forward":
        return fast_forward(repository)
    if decision.action == "fast-forward-entrypoint":
        return fast_forward(entrypoint, with_submodules=False)
    if decision.action == "rebase":
        return rebase(configuration, repository, facts)
    if decision.action == "validate":
        return validate(configuration, runner, facts, decision.attempt, cycle_command)
    if decision.action == "push":
        return push(repository, facts.head)
    if decision.action == "push-entrypoint":
        return push(entrypoint, facts.entrypoint_head)
    if decision.action == "activate":
        return activate(configuration, runner, facts)
    return ""
