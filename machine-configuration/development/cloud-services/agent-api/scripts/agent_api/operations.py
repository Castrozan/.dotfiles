import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import asdict

from agent_api.contract import (
    CapabilityError,
    OperationRequest,
    canonical_json,
    validate_operation_id,
)
from agent_api.files import describe_artifacts, private_directory, verify_artifacts


class OperationStore:
    def __init__(self, state_directory):
        self.state_directory = private_directory(state_directory)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS operations ("
                "operation_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, "
                "request TEXT NOT NULL, status TEXT NOT NULL, expires_at REAL NOT NULL, "
                "receipt TEXT)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS operation_status ON operations(status)"
            )

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(
            self.state_directory / "operations.sqlite", timeout=10
        )
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def directory(self, operation_id):
        validate_operation_id(operation_id)
        return self.state_directory / operation_id

    def expire(self, connection):
        connection.execute(
            "UPDATE operations SET status = 'interrupted' "
            "WHERE status = 'running' AND expires_at < ?",
            (time.time(),),
        )

    def inspect(self, operation_id):
        validate_operation_id(operation_id)
        with self.connect() as connection:
            self.expire(connection)
            row = connection.execute(
                "SELECT status, request_sha256, request, receipt FROM operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
        if row is None:
            raise CapabilityError("operation_not_found")
        status, digest, request, receipt_json = row
        receipt = json.loads(receipt_json) if receipt_json else {}
        receipt.update(
            operation_id=operation_id,
            status=status,
            request_sha256=digest,
            request=json.loads(request),
        )
        submission = self.directory(operation_id) / "submission.json"
        if submission.exists():
            receipt["provider_submission"] = json.loads(submission.read_bytes())
        if status == "succeeded":
            verify_artifacts(self.directory(operation_id), receipt["artifacts"])
        return receipt

    def claim(self, operation_id, request: OperationRequest, input_fingerprints=None):
        validate_operation_id(operation_id)
        digest = hashlib.sha256(
            canonical_json(
                {"request": asdict(request), "input_files": input_fingerprints or {}}
            )
        ).hexdigest()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self.expire(connection)
            previous = connection.execute(
                "SELECT request_sha256, status FROM operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if previous is not None:
                self.validate_previous(previous, digest)
            else:
                self.reserve(connection, operation_id, request, digest)
        return self.inspect(operation_id) if previous is not None else None

    def validate_previous(self, previous, digest):
        if previous[0] != digest:
            raise CapabilityError("operation_conflict")
        if previous[1] != "succeeded":
            raise CapabilityError("operation_incomplete")

    def reserve(self, connection, operation_id, request, digest):
        active = connection.execute(
            "SELECT COUNT(*) FROM operations WHERE status = 'running'"
        ).fetchone()[0]
        if active >= 2:
            raise CapabilityError("capacity_exceeded")
        self.directory(operation_id).mkdir(mode=0o700)
        connection.execute(
            "INSERT INTO operations VALUES (?, ?, ?, 'running', ?, NULL)",
            (
                operation_id,
                digest,
                canonical_json(asdict(request)).decode(),
                time.time() + request.timeout_seconds + 10,
            ),
        )

    def finish(self, operation_id, status, result):
        receipt = {"result": result, "artifacts": []}
        if status == "succeeded":
            receipt["artifacts"] = describe_artifacts(self.directory(operation_id))
        with self.connect() as connection:
            connection.execute(
                "UPDATE operations SET status = ?, receipt = ? WHERE operation_id = ? AND status = 'running'",
                (status, canonical_json(receipt).decode(), operation_id),
            )
        return self.inspect(operation_id)
