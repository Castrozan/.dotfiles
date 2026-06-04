from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolCallEvent:
    tool_name: str
    tool_input: dict
    timestamp: float


@dataclass
class SessionTrace:
    tool_calls: list[ToolCallEvent] = field(default_factory=list)
    assistant_messages: list[str] = field(default_factory=list)
    full_output: str = ""
    duration_seconds: float = 0
    exit_code: int = 0


@dataclass
class AssertionResult:
    name: str
    passed: bool
    detail: str


@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    assertion_results: list[AssertionResult]
    trace: SessionTrace
    workspace_directory: Path | None
    duration_seconds: float
    experience_score: int = 0
    error: str | None = None
