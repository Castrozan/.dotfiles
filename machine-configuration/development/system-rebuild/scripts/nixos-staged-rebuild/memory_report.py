import argparse
import subprocess
import sys

from memory_components import measure_components
from memory_records import RebuildRun, publish_report
from staged_command import command_failure_status, run_command


def arguments():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="operation", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("records")
    publish.add_argument("directory")
    publish.add_argument("action")
    publish.add_argument("host")
    publish.add_argument("started_at")
    publish.add_argument("exit_status", type=int)
    execute = commands.add_parser("run")
    execute.add_argument("phase")
    execute.add_argument("command", nargs=argparse.REMAINDER)
    components = commands.add_parser("components")
    components.add_argument("public_reference")
    components.add_argument("configuration_attribute")
    components.add_argument("system")
    return parser.parse_args()


def execute_operation(options):
    if options.operation == "publish":
        publish_report(
            options.records,
            options.directory,
            RebuildRun(
                options.action, options.host, options.started_at, options.exit_status
            ),
        )
        return
    if options.operation == "run":
        run_command(options.phase, options.command)
        return
    measure_components(
        options.public_reference, options.configuration_attribute, options.system, ()
    )


def main():
    try:
        execute_operation(arguments())
        return 0
    except subprocess.CalledProcessError as error:
        return command_failure_status(error)
    except (OSError, ValueError) as error:
        print(f"error: rebuild memory metrics failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
