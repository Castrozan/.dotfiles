import time
from contextlib import ExitStack

from media_speech.contract import SpeechError
from media_speech.usage import ProviderUsage, UsageCapabilities, UsageCharge, UsageQuota


def fetch_subscription(api_key, injected_client):
    from elevenlabs.client import ElevenLabs
    from httpx import Client

    with ExitStack() as resources:
        client = injected_client
        if client is None:
            transport = resources.enter_context(Client(timeout=30))
            client = ElevenLabs(api_key=api_key, timeout=30, httpx_client=transport)
        return client.user.subscription.get(request_options={"max_retries": 0})


def read_credit_limit_extension(response):
    extension = getattr(response, "max_credit_limit_extension", None)
    if extension is not None and not (
        extension == "unlimited" or (type(extension) is int and extension >= 0)
    ):
        raise SpeechError("invalid_usage")
    return extension


def build_overage_charge(response):
    overage = getattr(response, "current_overage", None)
    if overage is None:
        return None
    return UsageCharge(overage.amount, overage.currency.upper())


def build_provider_usage(name, response):
    extension = read_credit_limit_extension(response)
    charge = build_overage_charge(response)
    return ProviderUsage(
        name,
        "available",
        "account",
        int(time.time()),
        (
            UsageQuota(
                "credits",
                "credits",
                response.character_count,
                response.character_limit,
                response.next_character_count_reset_unix,
            ),
            UsageQuota(
                "voice_slots",
                "voices",
                response.voice_slots_used,
                response.voice_limit,
            ),
        ),
        plan=response.tier,
        account_status=response.status,
        overage_charge=charge,
        overage_enabled=None if extension is None else extension != 0,
    )


class ElevenLabsUsageReader:
    name = "elevenlabs"
    capabilities = UsageCapabilities("available", "account", ("credits", "voice_slots"))

    def __init__(self, api_key: str | None, client=None):
        self.api_key = api_key
        self.client = client

    def read_usage(self):
        from elevenlabs.core.api_error import ApiError
        from httpx import RequestError
        from pydantic import ValidationError

        if not self.api_key:
            raise SpeechError("missing_credentials")
        try:
            response = fetch_subscription(self.api_key, self.client)
            return build_provider_usage(self.name, response)
        except ApiError as error:
            categories = {
                401: "authentication_failed",
                403: "permission_denied",
                429: "rate_limited",
            }
            raise SpeechError(
                categories.get(error.status_code, "provider_failed")
            ) from None
        except RequestError:
            raise SpeechError("provider_unavailable") from None
        except (
            ValidationError,
            ValueError,
            AttributeError,
            TypeError,
            KeyError,
            SpeechError,
        ):
            raise SpeechError("invalid_provider_response") from None
