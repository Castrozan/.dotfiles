import argparse
import json
import sys
from pathlib import Path

from agent_api_job.errors import JobError
from agent_api_job.jobs import cancel_job, job_logs, job_status, start_job
from agent_api_job.model import Limits, StartRequest, validate_job_id, validate_tree_key
from agent_api_job.runners import select_runner
from agent_api_job.storage import state_root
from agent_api_job.supervisor import supervise
from agent_api_job.transfer import send_path
from agent_api_job.trees import DEFAULT_MAXIMUM_BYTES, receive_tree


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run, inspect and cancel jobs on this machine and store copied working trees."
    )
    verbs = parser.add_subparsers(dest="verb", required=True)
    start = verbs.add_parser("start", help="Start a job; the command follows --.")
    start.add_argument("job")
    location = start.add_mutually_exclusive_group()
    location.add_argument("--directory")
    location.add_argument("--tree")
    for limit in ("memory-megabytes", "cpu-percent", "runtime-seconds"):
        start.add_argument(f"--{limit}", type=int, required=True)
    status = verbs.add_parser("status", help="Report a job's state and outcome.")
    status.add_argument("job")
    logs = verbs.add_parser("logs", help="Return the tail of a job's output.")
    logs.add_argument("job")
    logs.add_argument("--lines", type=int, required=True)
    cancel = verbs.add_parser("cancel", help="Stop a job and forget its outcome.")
    cancel.add_argument("job")
    receive = verbs.add_parser(
        "receive", help="Store a tar stream from stdin as a tree."
    )
    receive.add_argument("key")
    receive.add_argument("--maximum-bytes", type=int, default=DEFAULT_MAXIMUM_BYTES)
    send = verbs.add_parser(
        "send", help="Write a path of a job's directory as a tar stream."
    )
    send.add_argument("job")
    send.add_argument("path")
    supervise_verb = verbs.add_parser("supervise", help=argparse.SUPPRESS)
    supervise_verb.add_argument("job_directory", type=Path)
    supervise_verb.add_argument("working_directory", type=Path)
    supervise_verb.add_argument("runtime_seconds", type=int)
    return parser


def working_directory(root, args):
    if args.tree is not None:
        path = root / "trees" / validate_tree_key(args.tree, "directory_unavailable")
    elif args.directory is not None:
        path = Path(args.directory)
    else:
        path = Path.home()
    if not path.is_absolute() or not path.is_dir():
        raise JobError("directory_unavailable")
    return path


def execute_start(root, args):
    validate_job_id(args.job)
    limits = Limits(args.memory_megabytes, args.cpu_percent, args.runtime_seconds)
    request = StartRequest(
        args.job, working_directory(root, args), limits, args.command_line
    )
    return start_job(root, request, select_runner())


def execute_supervise(root, args):
    supervise(
        args.job_directory,
        args.working_directory,
        args.runtime_seconds,
        args.command_line,
    )


HANDLERS = {
    "start": execute_start,
    "status": lambda root, args: job_status(root, args.job),
    "logs": lambda root, args: job_logs(root, args.job, args.lines),
    "cancel": lambda root, args: cancel_job(root, args.job),
    "receive": lambda root, args: receive_tree(
        root, args.key, sys.stdin.buffer, args.maximum_bytes
    ),
    "send": lambda root, args: send_path(root, args.job, args.path, sys.stdout.buffer),
    "supervise": execute_supervise,
}


def split_command(arguments):
    if "--" not in arguments:
        return arguments, []
    separator = arguments.index("--")
    return arguments[:separator], arguments[separator + 1 :]


def parse_arguments(arguments):
    head, command = split_command(arguments)
    parser = build_parser()
    args = parser.parse_args(head)
    if args.verb in ("start", "supervise") and not command:
        parser.error("the command to run must follow --")
    args.command_line = command
    return args


def main(arguments=None):
    args = parse_arguments(list(sys.argv[1:] if arguments is None else arguments))
    try:
        output = HANDLERS[args.verb](state_root(), args)
    except JobError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print(json.dumps({"error": "storage_failed"}), file=sys.stderr)
        return 1
    if output is not None:
        print(json.dumps(output))
    return 0
