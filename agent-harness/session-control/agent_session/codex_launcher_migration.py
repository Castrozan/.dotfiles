import hashlib
import time

from agent_session import codex_migration_inputs, codex_migration_readiness
from agent_session.codex_migration_contract import require, resume_arguments
from agent_session.codex_migration_journal import MigrationJournal
from agent_session.codex_migration_processes import process_birth


def wait_for_owned_exit(plan, journal):
    deadline = time.monotonic() + 30.0
    while True:
        remaining = []
        for process in plan["old_processes"]:
            observed = process_birth(process["pid"])
            if (
                observed
                and observed["start_ticks"] == process["start_ticks"]
                and observed["state"] != "Z"
            ):
                remaining.append({**process, "observed": observed})
        journal.result["remaining_old_processes"] = remaining
        if not remaining:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError("owned process births remain after30s")
        time.sleep(min(0.2, deadline - time.monotonic()))


def migrate(plan, commands, directory):
    journal = MigrationJournal(directory, plan)
    result = journal.result
    started = time.monotonic()
    try:
        journal.phase("validate-declared-inputs")
        codex_migration_inputs.validate_plan(plan)
        codex_migration_inputs.validate_configuration(plan)
        codex_migration_inputs.validate_rollout(plan)
        package = codex_migration_inputs.validate_package(plan)
        result["package"] = package
        journal.phase("await-old-processes")
        wait_for_owned_exit(plan, journal)
        journal.phase("inspect-idle-shell")
        information = commands.herdr(
            "cleared process-info",
            ["pane", "process-info", "--pane", plan["pane_identifier"]],
        )["process_info"]
        require(
            information["pane_id"] == plan["pane_identifier"]
            and information["foreground_process_group_id"] == information["shell_pid"],
            "pane is not its cleared shell",
        )
        baseline = hashlib.sha256(
            codex_migration_readiness.read_pane_frame(
                commands, plan["pane_identifier"]
            ).encode()
        ).hexdigest()
        codex_migration_inputs.validate_configuration(plan)
        journal.phase("launch-exact-thread")
        result["launch_attempted"] = True
        journal.save()
        arguments = [
            "herdr",
            "pane",
            "run",
            plan["pane_identifier"],
            "env",
            "CODEX_LAUNCHER_BINARY=" + plan["upstream_binary"],
            "AGENT_INTERACTIVE_PREFERENCES_PATH=" + plan["preferences"],
            plan["launcher"],
            *resume_arguments(plan),
        ]
        commands.run("native pane run", arguments, 30.0)
        journal.phase("await-replacement")
        result["replacement"] = codex_migration_readiness.await_replacement(
            plan, commands, package, baseline
        )
        journal.phase("submit-continuation")
        result["continuation_attempted"] = True
        journal.save()
        result["continuation"] = commands.send(
            plan["pane_identifier"], plan["continuation"]
        )
        result["status"] = "continuation-submitted"
    except Exception as error:
        result.update(status="failed", error=type(error).__name__ + ": " + str(error))
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        journal.save()
    return result
