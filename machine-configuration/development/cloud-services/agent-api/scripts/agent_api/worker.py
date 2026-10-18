import json
import os

from agent_api.catalog import validate_request
from agent_api.contract import (
    MAXIMUM_RESULT_BYTES,
    CapabilityError,
    OperationRequest,
    canonical_json,
)
from agent_api.files import write_json
from agent_api.providers.factory import create_provider
from agent_api.service import fingerprint_inputs


def generate_result(directory):
    envelope = json.loads((directory / "request.json").read_bytes())
    request = OperationRequest(**envelope["request"])
    if fingerprint_inputs(request) != envelope["input_fingerprints"]:
        raise CapabilityError("input_changed")
    capability = validate_request(request)
    provider = create_provider(capability["provider"])
    provider.preflight(request)
    output = provider.execute(request, directory, envelope["operation_id"])
    result = {"status": "succeeded", "output": output}
    if len(canonical_json(result)) > MAXIMUM_RESULT_BYTES:
        raise CapabilityError("response_too_large")
    return result


def execute_worker(directory):
    os.umask(0o077)
    try:
        result = generate_result(directory)
    except CapabilityError as error:
        result = {"status": "failed", "error": str(error)}
    except KeyboardInterrupt:
        result = {"status": "failed", "error": "execution_interrupted"}
    except Exception:
        result = {"status": "failed", "error": "execution_failed"}
    write_json(directory / "result.json", result)
    return 0 if result["status"] == "succeeded" else 1
