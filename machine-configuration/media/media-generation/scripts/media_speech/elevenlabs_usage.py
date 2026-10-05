import time
from contextlib import ExitStack

from media_speech.contract import SpeechError
from media_speech.usage import ProviderUsage, UsageCapabilities, UsageCharge, UsageQuota


class ElevenLabsUsageReader:
    name = "elevenlabs"
    capabilities = UsageCapabilities("available", "account", ("credits", "voice_slots"))

    def __init__(self, api_key: str | None, client=None):
        self.api_key = api_key
        self.client = client

    def read_usage(self):
        from elevenlabs.client import ElevenLabs
        from elevenlabs.core.api_error import ApiError
        from httpx import Client, RequestError
        from pydantic import ValidationError

        if not self.api_key:
            raise SpeechError("missing_credentials")
        try:
            with ExitStack() as resources:
                client = self.client
                if client is None:
                    transport = resources.enter_context(Client(timeout=30))
                    client = ElevenLabs(
                        api_key=self.api_key, timeout=30, httpx_client=transport
                    )
                response = client.user.subscription.get(
                    request_options={"max_retries": 0}
                )
            extension = getattr(response, "max_credit_limit_extension", None)
            if extension is not None and not (
                extension == "unlimited" or (type(extension) is int and extension >= 0)
            ):
                raise SpeechError("invalid_usage")
            overage = getattr(response, "current_overage", None)
            charge = (
                None
                if overage is None
                else UsageCharge(overage["amount"], overage["currency"].upper())
            )
            return ProviderUsage(
                self.name,
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
