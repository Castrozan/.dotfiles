import math
import string
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


def validate_usage_status(status):
    if status not in {"available", "not_applicable", "unavailable"}:
        raise SpeechError("invalid_usage")


def validate_usage_metrics(metrics):
    if not isinstance(metrics, tuple):
        raise SpeechError("invalid_usage")
    for metric in metrics:
        validate_usage_label(metric)
    if len(set(metrics)) != len(metrics):
        raise SpeechError("invalid_usage")


def is_usage_amount(amount):
    if type(amount) is float:
        return math.isfinite(amount) and amount >= 0
    return type(amount) is int and amount >= 0


def validate_usage_amount(amount):
    if amount is not None and not is_usage_amount(amount):
        raise SpeechError("invalid_usage")


def validate_resets_at_unix(resets_at_unix):
    if resets_at_unix is not None and (
        type(resets_at_unix) is not int or resets_at_unix < 0
    ):
        raise SpeechError("invalid_usage")


def validate_observed_at_unix(observed_at_unix):
    if type(observed_at_unix) is not int or observed_at_unix <= 0:
        raise SpeechError("invalid_usage")


def validate_quotas(quotas):
    if not isinstance(quotas, tuple) or any(
        not isinstance(quota, UsageQuota) for quota in quotas
    ):
        raise SpeechError("invalid_usage")
    if len({quota.name for quota in quotas}) != len(quotas):
        raise SpeechError("invalid_usage")


def validate_overage(overage_charge, overage_enabled):
    if overage_charge is not None and not isinstance(overage_charge, UsageCharge):
        raise SpeechError("invalid_usage")
    if overage_enabled is not None and type(overage_enabled) is not bool:
        raise SpeechError("invalid_usage")


def is_usage_charge_amount(amount):
    if not isinstance(amount, str) or len(amount) > 100:
        return False
    decimal_amount = Decimal(amount)
    return decimal_amount.is_finite() and decimal_amount >= 0


def is_currency_code(currency):
    return (
        isinstance(currency, str)
        and len(currency) == 3
        and all(character in string.ascii_uppercase for character in currency)
    )


@dataclass(frozen=True)
class UsageCapabilities:
    status: str
    scope: str
    metrics: tuple[str, ...]

    def __post_init__(self):
        validate_usage_label(self.scope)
        validate_usage_status(self.status)
        validate_usage_metrics(self.metrics)
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
        validate_usage_amount(self.used)
        validate_usage_amount(self.limit)
        validate_resets_at_unix(self.resets_at_unix)
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
            if not is_usage_charge_amount(self.amount) or not is_currency_code(
                self.currency
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
        validate_usage_status(self.status)
        validate_observed_at_unix(self.observed_at_unix)
        validate_quotas(self.quotas)
        if (self.status == "available") != bool(self.quotas):
            raise SpeechError("invalid_usage")
        validate_overage(self.overage_charge, self.overage_enabled)


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
