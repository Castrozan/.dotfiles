import time
from dataclasses import asdict

from agent_api.catalog import describe, validate_input, validate_request
from agent_api.contract import MAXIMUM_RESULT_BYTES, CapabilityError, canonical_json
from agent_api.files import file_digest, input_file, write_json
from agent_api.operations import OperationStore
from agent_api.providers.factory import create_provider
from agent_api.runtime import WorkerExecutor


def fingerprint_inputs(request):
    return {
        name: file_digest(input_file(request.input[name]))
        for name in ("path", "model_path")
        if name in request.input
    }


class CapabilityService:
    def __init__(self, state_directory, executor=None):
        self.store = OperationStore(state_directory)
        self.executor = executor or WorkerExecutor()

    def run(self, operation_id, request):
        validate_input(request)
        fingerprints = fingerprint_inputs(request)
        try:
            self.store.inspect(operation_id)
        except CapabilityError as error:
            if str(error) != "operation_not_found":
                raise
        else:
            return self.store.claim(operation_id, request, fingerprints)
        entry = validate_request(request)
        create_provider(entry["provider"]).preflight(request)
        replay = self.store.claim(operation_id, request, fingerprints)
        if replay is not None:
            return replay
        directory = self.store.directory(operation_id)
        started = time.monotonic()
        try:
            write_json(
                directory / "request.json",
                {
                    "operation_id": operation_id,
                    "request": asdict(request),
                    "input_fingerprints": fingerprints,
                },
            )
            result = self.executor.execute(directory, request.timeout_seconds)
            if len(canonical_json(result)) > MAXIMUM_RESULT_BYTES - 1024:
                raise CapabilityError("response_too_large")
            if fingerprint_inputs(request) != fingerprints:
                raise CapabilityError("input_changed")
            return self.store.finish(
                operation_id,
                "succeeded",
                {
                    "output": result,
                    "elapsed_seconds": time.monotonic() - started,
                    "charge_usd": None
                    if describe(request.capability)["payment"] != "none"
                    else 0,
                },
            )
        except BaseException as error:
            category = (
                str(error)
                if isinstance(error, CapabilityError)
                else "execution_interrupted"
            )
            self.store.finish(
                operation_id, "failed", {"error": category, "charge_usd": None}
            )
            raise
