import json
import time

import httpx

from agent_api.contract import (
    MAXIMUM_RESULT_BYTES,
    CapabilityError,
    canonical_json,
    validate_url,
)


class NetworkClient:
    def __init__(self, timeout_seconds, client=None):
        self.deadline = time.monotonic() + timeout_seconds
        self.client = client or httpx.Client(follow_redirects=False, trust_env=False)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.close()

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise CapabilityError("deadline_exceeded")
        return min(30, remaining)

    def request(
        self, method, url, data=None, headers=None, maximum_bytes=MAXIMUM_RESULT_BYTES
    ):
        validate_url(url)
        try:
            with self.client.stream(
                method, url, json=data, headers=headers, timeout=self.remaining()
            ) as response:
                if response.status_code not in (200, 201, 202):
                    category = {
                        401: "authentication_failed",
                        403: "permission_denied",
                        429: "rate_limited",
                    }
                    raise CapabilityError(
                        category.get(response.status_code, "provider_failed")
                    )
                content = bytearray()
                for chunk in response.iter_bytes():
                    self.remaining()
                    content.extend(chunk)
                    if len(content) > maximum_bytes:
                        raise CapabilityError("response_too_large")
                return bytes(content)
        except (httpx.HTTPError, OSError):
            raise CapabilityError("network_failed") from None

    def json(self, method, url, data=None, headers=None):
        try:
            result = json.loads(self.request(method, url, data, headers))
            if not isinstance(result, dict):
                raise ValueError
            canonical_json(result)
            return result
        except (ValueError, UnicodeError):
            raise CapabilityError("invalid_provider_response") from None

    def close(self):
        self.client.close()
