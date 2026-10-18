import json
import uuid
from dataclasses import asdict, dataclass
from typing import Protocol
from urllib.parse import urlsplit

MAXIMUM_REQUEST_BYTES = 64 * 1024
MAXIMUM_RESULT_BYTES = 4 * 1024 * 1024
MAXIMUM_ARTIFACT_BYTES = 512 * 1024 * 1024


class CapabilityError(Exception):
    pass


def canonical_json(value):
    try:
        return json.dumps(value, sort_keys=True, allow_nan=False).encode()
    except (ValueError, TypeError):
        raise CapabilityError("invalid_json") from None


def validate_operation_id(operation_id):
    try:
        if str(uuid.UUID(operation_id)) != operation_id:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise CapabilityError("invalid_operation_id") from None


def validate_url(url):
    try:
        parsed = urlsplit(url)
        validate_url_authority(parsed)
    except (ValueError, TypeError):
        raise CapabilityError("invalid_url") from None
    if len(url) > 4096 or any(ord(character) <= 32 for character in url):
        raise CapabilityError("invalid_url")
    return url


def validate_url_authority(parsed):
    valid = (
        parsed.scheme in ("http", "https"),
        bool(parsed.hostname),
        parsed.username is None,
        parsed.password is None,
    )
    if not all(valid):
        raise ValueError
    if parsed.port == 0:
        raise ValueError


def validate_request_controls(capability, timeout_seconds):
    if not isinstance(capability, str):
        raise CapabilityError("invalid_capability")
    if not 1 <= len(capability) <= 100:
        raise CapabilityError("invalid_capability")
    if type(timeout_seconds) is not int:
        raise CapabilityError("invalid_deadline")
    if not 1 <= timeout_seconds <= 600:
        raise CapabilityError("invalid_deadline")


@dataclass(frozen=True)
class OperationRequest:
    capability: str
    input: dict
    timeout_seconds: int = 180
    allow_paid: bool = False

    def __post_init__(self):
        validate_request_controls(self.capability, self.timeout_seconds)
        if not isinstance(self.input, dict):
            raise CapabilityError("invalid_input")
        if type(self.allow_paid) is not bool:
            raise CapabilityError("invalid_payment_permission")
        if len(canonical_json(asdict(self))) > MAXIMUM_REQUEST_BYTES:
            raise CapabilityError("request_too_large")


class CapabilityProvider(Protocol):
    def preflight(self, request: OperationRequest) -> None: ...

    def execute(
        self, request: OperationRequest, directory, operation_id: str
    ) -> dict: ...
