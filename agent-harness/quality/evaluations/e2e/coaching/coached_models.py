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


def failed_coached_session(
    scenario_name: str, duration_seconds: float, error: str
) -> CoachedSessionResult:
    return CoachedSessionResult(
        scenario_name=scenario_name,
        initial_nps=0,
        coached_nps=0,
        improvement=0,
        initial_tool_sequence=[],
        coached_tool_sequence=[],
        coach_findings="",
        duration_seconds=duration_seconds,
        error=error,
    )
