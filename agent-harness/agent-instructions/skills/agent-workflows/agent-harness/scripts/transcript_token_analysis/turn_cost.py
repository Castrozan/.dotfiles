import dataclasses

CACHE_READ_WEIGHT = 0.1
CACHE_WRITE_FIVE_MINUTE_WEIGHT = 1.25
CACHE_WRITE_ONE_HOUR_WEIGHT = 2.0
OUTPUT_WEIGHT = 5.0


@dataclasses.dataclass(frozen=True)
class Turn:
    fresh_input: int
    cache_read: int
    cache_write_one_hour: int
    cache_write_five_minute: int
    output: int

    @property
    def context(self):
        return (
            self.fresh_input
            + self.cache_read
            + self.cache_write_one_hour
            + self.cache_write_five_minute
        )

    @property
    def weighted_cost(self):
        return (
            self.fresh_input
            + CACHE_READ_WEIGHT * self.cache_read
            + CACHE_WRITE_ONE_HOUR_WEIGHT * self.cache_write_one_hour
            + CACHE_WRITE_FIVE_MINUTE_WEIGHT * self.cache_write_five_minute
            + OUTPUT_WEIGHT * self.output
        )


def turn_from_usage(usage):
    one_hour = (usage.get("cache_creation") or {}).get("ephemeral_1h_input_tokens", 0)
    written = usage.get("cache_creation_input_tokens", 0)
    return Turn(
        fresh_input=usage.get("input_tokens", 0),
        cache_read=usage.get("cache_read_input_tokens", 0),
        cache_write_one_hour=one_hour,
        cache_write_five_minute=written - one_hour,
        output=usage.get("output_tokens", 0),
    )
