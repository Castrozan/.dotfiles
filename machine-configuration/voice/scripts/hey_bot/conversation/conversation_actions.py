from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnnounceAction:
    message: str


@dataclass(frozen=True)
class LogTranscriptionAction:
    text: str


@dataclass(frozen=True)
class NotifyAction:
    body: str


@dataclass(frozen=True)
class DispatchCommandAction:
    command_text: str


@dataclass(frozen=True)
class SpeakAction:
    text: str


@dataclass(frozen=True)
class SaveWaitContextAction:
    command_text: str


@dataclass(frozen=True)
class ClearWaitContextAction:
    pass


@dataclass(frozen=True)
class RaiseFollowupSignalAction:
    pass


ConversationAction = (
    AnnounceAction
    | LogTranscriptionAction
    | NotifyAction
    | DispatchCommandAction
    | SpeakAction
    | SaveWaitContextAction
    | ClearWaitContextAction
    | RaiseFollowupSignalAction
)
