from dataclasses import dataclass

from cycle_configuration import QUIET_SECONDS, STARVATION_SECONDS


@dataclass(frozen=True)
class CycleFacts:
    branch: str
    operation_in_progress: bool
    active_job_scopes: tuple[str, ...]
    head: str
    upstream: str
    behind: int
    ahead: int
    dirty_paths: tuple[str, ...]
    newest_activity_age_seconds: float
    oldest_unvalidated_age_seconds: float
    head_validation: dict | None
    recorded_rebase_conflict: dict | None = None
    unpublished_submodule_pins: tuple[str, ...] = ()
    continuous_integration: dict | None = None
    live_toplevel: str = ""
    head_activation: dict | None = None
    operator_idle: bool = False
    rebuild_running: bool = False
    entrypoint_head: str = ""
    entrypoint_settled: bool = False
    entrypoint_behind: int = 0
    entrypoint_ahead: int = 0
    unread_local_messages: tuple[str, ...] = ()
    synchronization_pending_seconds: float = 0

    @property
    def tracked_dirty(self) -> bool:
        return bool(self.dirty_paths)

    @property
    def synchronization_stalled(self) -> bool:
        return self.synchronization_pending_seconds >= STARVATION_SECONDS

    @property
    def work_in_progress(self) -> bool:
        return self.newest_activity_age_seconds < QUIET_SECONDS

    @property
    def starving(self) -> bool:
        return self.oldest_unvalidated_age_seconds >= STARVATION_SECONDS


@dataclass(frozen=True)
class CycleDecision:
    action: str
    reason: str
    attention: dict | None = None
    attempt: int = 0


def wait(reason: str) -> CycleDecision:
    return CycleDecision("wait", reason)


def attention(kind: str, reason: str, **details) -> CycleDecision:
    return CycleDecision("attention", reason, {"kind": kind, **details})
