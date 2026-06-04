from dataclasses import dataclass


@dataclass
class CoachedSessionResult:
    scenario_name: str
    initial_nps: int
    coached_nps: int
    improvement: int
    initial_tool_sequence: list[str]
    coached_tool_sequence: list[str]
    coach_findings: str
    duration_seconds: float
    error: str | None = None
