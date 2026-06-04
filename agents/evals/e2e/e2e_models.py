from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TerminalToolCallEvent:
    tool_name: str
    tool_arguments_text: str
    position_in_output: int


@dataclass
class TerminalSessionTrace:
    raw_terminal_output: str = ""
    detected_tool_calls: list[TerminalToolCallEvent] = field(default_factory=list)
    detected_bash_commands: list[str] = field(default_factory=list)
    detected_assistant_text_blocks: list[str] = field(default_factory=list)
    duration_seconds: float = 0
    timed_out: bool = False


@dataclass
class E2eAssertionResult:
    name: str
    passed: bool
    detail: str


@dataclass
class E2eScenarioResult:
    scenario_name: str
    passed: bool
    assertion_results: list[E2eAssertionResult]
    trace: TerminalSessionTrace
    workspace_directory: Path | None
    duration_seconds: float
    experience_score: int = 0
    error: str | None = None
