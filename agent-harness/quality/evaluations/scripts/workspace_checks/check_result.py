from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
