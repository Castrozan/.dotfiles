import math
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Protocol

from media_speech.contract import SpeechError


def validate_usage_label(value):
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 100
        or any(ord(character) < 32 for character in value)
    ):
        raise SpeechError("invalid_usage")


@dataclass(frozen=True)
class UsageCapabilities:
    status: str
    scope: str
    metrics: tuple[str, ...]

    def __post_init__(self):
        validate_usage_label(self.scope)
        if self.status not in {"available", "not_applicable", "unavailable"}:
            raise SpeechError("invalid_usage")
        if not isinstance(self.metrics, tuple):
            raise SpeechError("invalid_usage")
        for metric in self.metrics:
            validate_usage_label(metric)
        if len(set(self.metrics)) != len(self.metrics):
            raise SpeechError("invalid_usage")
        if (self.status == "available") != bool(self.metrics):
            raise SpeechError("invalid_usage")


@dataclass(frozen=True)
class UsageQuota:
    name: str
    unit: str
    used: int | float | None
    limit: int | float | None
    resets_at_unix: int | None = None
    remaining: int | float | None = field(init=False)

    def __post_init__(self):
        validate_usage_label(self.name)
        validate_usage_label(self.unit)
        for value in (self.used, self.limit):
            if value is not None and (
                type(value) not in (int, float)
                or value < 0
                or (type(value) is float and not math.isfinite(value))
            ):
                raise SpeechError("invalid_usage")
        if self.resets_at_unix is not None and (
            type(self.resets_at_unix) is not int or self.resets_at_unix < 0
        ):
            raise SpeechError("invalid_usage")
        remaining = (
            None
            if self.used is None or self.limit is None
            else max(0, self.limit - self.used)
        )
        object.__setattr__(self, "remaining", remaining)


@dataclass(frozen=True)
class UsageCharge:
    amount: str
    currency: str

    def __post_init__(self):
        try:
            if not isinstance(self.amount, str) or len(self.amount) > 100:
                raise ValueError
            amount = Decimal(self.amount)
            if not amount.is_finite() or amount < 0:
                raise ValueError
            if (
                not isinstance(self.currency, str)
                or len(self.currency) != 3
                or not self.currency.isascii()
                or not self.currency.isalpha()
                or self.currency != self.currency.upper()
            ):
                raise ValueError
        except (InvalidOperation, ValueError):
            raise SpeechError("invalid_usage") from None


@dataclass(frozen=True)
class ProviderUsage:
    provider: str
    status: str
    scope: str
    observed_at_unix: int
    quotas: tuple[UsageQuota, ...] = ()
    plan: str | None = None
    account_status: str | None = None
    overage_charge: UsageCharge | None = None
    overage_enabled: bool | None = None

    def __post_init__(self):
        validate_usage_label(self.provider)
        validate_usage_label(self.scope)
        for label in (self.plan, self.account_status):
            if label is not None:
                validate_usage_label(label)
        if self.status not in {"available", "not_applicable", "unavailable"}:
            raise SpeechError("invalid_usage")
        if type(self.observed_at_unix) is not int or self.observed_at_unix <= 0:
            raise SpeechError("invalid_usage")
        if not isinstance(self.quotas, tuple) or any(
            not isinstance(quota, UsageQuota) for quota in self.quotas
        ):
            raise SpeechError("invalid_usage")
        if len({quota.name for quota in self.quotas}) != len(self.quotas):
            raise SpeechError("invalid_usage")
        if (self.status == "available") != bool(self.quotas):
            raise SpeechError("invalid_usage")
        if self.overage_charge is not None and not isinstance(
            self.overage_charge, UsageCharge
        ):
            raise SpeechError("invalid_usage")
        if self.overage_enabled is not None and type(self.overage_enabled) is not bool:
            raise SpeechError("invalid_usage")


class ProviderUsageReader(Protocol):
    name: str
    capabilities: UsageCapabilities

    def read_usage(self) -> ProviderUsage: ...


class ProviderUsageService:
    def __init__(self, reader: ProviderUsageReader):
        self.reader = reader

    def capabilities(self):
        if not isinstance(self.reader.capabilities, UsageCapabilities):
            raise SpeechError("invalid_provider_response")
        return self.reader.capabilities

    def read_usage(self):
        capabilities = self.capabilities()
        snapshot = self.reader.read_usage()
        if (
            not isinstance(snapshot, ProviderUsage)
            or snapshot.provider != self.reader.name
            or snapshot.status != capabilities.status
            or snapshot.scope != capabilities.scope
            or any(quota.name not in capabilities.metrics for quota in snapshot.quotas)
        ):
            raise SpeechError("invalid_provider_response")
        return snapshot
