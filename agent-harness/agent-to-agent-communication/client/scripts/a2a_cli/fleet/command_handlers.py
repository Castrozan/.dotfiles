"""Command handlers independent from argument declarations."""

import json
import sqlite3
import sys

from . import operations
from .job_intents import DispatchIntent
from .registry import Registry
from .session_records import Observation


def confirm(registry, args):
    registry.confirm_host(args.host, args.transport, args.evidence)


def status(registry, args):
    live = operations.refresh(registry, args.refresh) if args.refresh else []
    return registry.status(live_hosts=live)


def read_document(path):
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("metadata import exceeds 2 MiB")
    return json.loads(path.read_text())


def ingest(registry, args):
    doc = read_document(args.file)
    observation = Observation(
        doc["a2a"], doc["herdr"], doc["observed_at"], doc["evidence"]
    )
    registry.ingest(args.host, observation)


def event(registry, args):
    registry.event(args.host, read_document(args.file), args.evidence)


def assign(registry, args):
    registry.assign(args.host, args.pane, args.session, args.owner, args.task)


def dispatch(registry, args):
    intent = DispatchIntent(
        args.request_id,
        args.host,
        args.pane,
        args.session,
        args.owner,
        args.task,
        args.prompt,
    )
    return operations.dispatch(registry, intent)


def result(registry, args):
    return operations.result(registry, args.request_id)


def verify(registry, args):
    return registry.verify(args.request_id, args.evidence)


def reconcile(registry, args):
    return registry.reconcile(
        args.request_id, args.evidence, args.remote_task_id, args.outcome
    )


HANDLERS = {
    "confirm-host": confirm,
    "status": status,
    "ingest": ingest,
    "event": event,
    "assign": assign,
    "dispatch": dispatch,
    "result": result,
    "verify": verify,
    "reconcile": reconcile,
}


def execute(args):
    registry = Registry(args.db)
    try:
        answer = HANDLERS[args.fleet_command](registry, args)
        if answer is not None:
            print(json.dumps(answer, indent=2))
        return 0
    finally:
        registry.close()


def command_fleet(arguments):
    try:
        return execute(arguments)
    except (
        ValueError,
        OSError,
        sqlite3.Error,
        KeyError,
        TypeError,
        AttributeError,
    ) as error:
        print(f"a2a fleet: {error}", file=sys.stderr)
        return 1
