import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from agent_api.catalog import describe, discover, providers
from agent_api.contract import MAXIMUM_REQUEST_BYTES, CapabilityError, OperationRequest
from agent_api.files import private_directory
from agent_api.service import CapabilityService


def build_parser():
    parser = argparse.ArgumentParser(
        description="Discover capabilities, inspect schemas and execute private durable agent jobs."
    )
    parser.add_argument(
        "--state-directory",
        type=Path,
        default=Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "agent-api",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "providers",
        help="Show provider documentation and credential availability without reading credentials.",
    )
    discover = commands.add_parser(
        "discover",
        help="Find capabilities without creating state or executing providers.",
    )
    discover.add_argument("query", nargs="?", default="")
    discover.add_argument("--provider")
    inspect = commands.add_parser(
        "inspect", help="Show one capability's input schema and payment requirements."
    )
    inspect.add_argument("capability")
    run = commands.add_parser(
        "run",
        help="Execute one capability; inspect failed jobs before selecting another UUID.",
    )
    run.add_argument("capability")
    inputs = run.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input")
    inputs.add_argument("--input-file", type=Path)
    run.add_argument("--operation-id")
    run.add_argument("--timeout-seconds", type=int, default=180)
    run.add_argument(
        "--allow-paid",
        action="store_true",
        help="Allow an account-billed operation; this does not reserve or cap its cost.",
    )
    operation = commands.add_parser(
        "operation",
        help="Inspect durable local state, retained artifacts and any provider submission ID.",
    )
    operation.add_argument("operation_id")
    serve = commands.add_parser(
        "serve",
        help="Serve HTTP/OpenAPI on a private Unix socket; runs only while this command is active.",
    )
    serve.add_argument("--socket", type=Path)
    worker = commands.add_parser("worker", help=argparse.SUPPRESS)
    worker.add_argument("directory", type=Path)
    return parser


def read_input(args):
    if args.input_file:
        with args.input_file.open("rb") as stream:
            data = stream.read(MAXIMUM_REQUEST_BYTES + 1)
    else:
        data = args.input.encode()
    if len(data) > MAXIMUM_REQUEST_BYTES:
        raise CapabilityError("request_too_large")
    try:
        return json.loads(data)
    except (ValueError, UnicodeError):
        raise CapabilityError("invalid_json") from None


def serve_api(args):
    import uvicorn

    from agent_api.transport import create_app

    state_directory = private_directory(args.state_directory)
    socket_path = args.socket or state_directory / "api.sock"
    private_directory(socket_path.absolute().parent)
    if socket_path.exists():
        raise CapabilityError("socket_exists")
    uvicorn.run(
        create_app(state_directory),
        uds=str(socket_path),
        limit_concurrency=8,
        timeout_keep_alive=5,
        access_log=False,
    )
    return 0


def execute_discovery(args):
    if args.command == "providers":
        return {"providers": providers()}
    if args.command == "discover":
        return {"capabilities": discover(args.query, args.provider)}
    if args.command == "inspect":
        return describe(args.capability)


def execute(args):
    if args.command in ("providers", "discover", "inspect"):
        return execute_discovery(args)
    service = CapabilityService(args.state_directory)
    if args.command == "operation":
        return service.store.inspect(args.operation_id)
    request = OperationRequest(
        args.capability, read_input(args), args.timeout_seconds, args.allow_paid
    )
    operation_id = args.operation_id or str(uuid.uuid4())
    print(json.dumps({"operation_id": operation_id}), file=sys.stderr, flush=True)
    return service.run(operation_id, request)


def execute_mode(args):
    if args.command == "worker":
        from agent_api.worker import execute_worker

        return execute_worker(args.directory)
    if args.command == "serve":
        return serve_api(args)
    print(json.dumps(execute(args), ensure_ascii=False, allow_nan=False, indent=2))
    return 0


def main(arguments=None):
    os.umask(0o077)
    args = build_parser().parse_args(arguments)
    try:
        return execute_mode(args)
    except CapabilityError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError):
        print(json.dumps({"error": "storage_or_input_failed"}), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
