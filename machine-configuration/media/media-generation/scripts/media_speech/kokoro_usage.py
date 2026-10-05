import time

from media_speech.usage import ProviderUsage, UsageCapabilities


class KokoroUsageReader:
    name = "kokoro"
    capabilities = UsageCapabilities("not_applicable", "local", ())

    def read_usage(self):
        return ProviderUsage(
            self.name,
            self.capabilities.status,
            self.capabilities.scope,
            int(time.time()),
        )
