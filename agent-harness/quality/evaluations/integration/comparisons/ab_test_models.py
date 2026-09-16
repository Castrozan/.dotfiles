from dataclasses import dataclass, field


@dataclass
class ToolCallEvent:
    tool_name: str
    tool_input: dict


@dataclass
class SessionTrace:
    tool_calls: list[ToolCallEvent] = field(default_factory=list)
    assistant_messages: list[str] = field(default_factory=list)
    duration_seconds: float = 0
    exit_code: int = 0


@dataclass
class InstructionFollowingMetrics:
    read_before_edit: bool = False
    used_glob_not_find: bool = False
    no_comments_in_written_code: bool = False
    used_descriptive_names: bool = False
    used_specific_git_staging: bool = False
    read_to_edit_ratio: float = 0.0
    total_tool_calls: int = 0
    score: int = 0


@dataclass
class AbTestResult:
    configuration_name: str
    scenario_name: str
    metrics: InstructionFollowingMetrics
    trace: SessionTrace
    duration_seconds: float
