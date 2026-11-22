import dataclasses
import math
import time
from collections.abc import Callable

ASK_ERRORS = (OSError, ValueError, TimeoutError)

Ask = Callable[[list[dict], list[dict]], object]


@dataclasses.dataclass(frozen=True)
class Option:
    identifier: str
    description: str


@dataclasses.dataclass(frozen=True)
class DecisionRequest:
    decision: str
    instructions: str
    context: str
    evidence: str
    options: tuple[Option, ...]
    safest: str
    floor: float
    reason: str
    guarded: bool
    summary: str

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(option.identifier for option in self.options)


@dataclasses.dataclass(frozen=True)
class Decision:
    choice: str
    confidence: float
    source: str
    why: str


@dataclasses.dataclass(frozen=True)
class Consultation:
    decision: Decision
    model_calls: int
    latency_milliseconds: int
    input_tokens: int


def input_messages(request: DecisionRequest) -> list[dict]:
    return [
        {"role": "developer", "content": request.context},
        {"role": "user", "content": request.evidence},
    ]


def questions(request: DecisionRequest) -> list[dict]:
    choices = [
        {"value": option.identifier, "description": option.description}
        for option in request.options
    ]
    return [
        {
            "type": "choice",
            "name": request.decision,
            "instructions": request.instructions,
            "choices": choices,
        }
    ]


def named_answer(replied: object, name: str) -> dict:
    answers = replied.get("answers") if isinstance(replied, dict) else None
    if not isinstance(answers, list):
        return {}
    return next(
        (
            answer
            for answer in answers
            if isinstance(answer, dict) and answer.get("name") == name
        ),
        {},
    )


def confidence_of(answer: dict) -> float | None:
    confidence = answer.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        return None
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        return None
    return float(confidence)


def reported_input_tokens(replied: object) -> object:
    usage = replied.get("usage") if isinstance(replied, dict) else None
    return usage.get("input_tokens") if isinstance(usage, dict) else None


def input_tokens(replied: object) -> int:
    tokens = reported_input_tokens(replied)
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
        return 0
    return tokens


def fallback(request: DecisionRequest, miss: str) -> Decision:
    return Decision(
        request.safest, 0.0, "fallback", f"{miss}; falling back to {request.safest}"
    )


def settled(request: DecisionRequest) -> Decision:
    source = "guard" if request.guarded else "only-option"
    return Decision(request.options[0].identifier, 1.0, source, request.reason)


def legal_choice(answer: dict, identifiers: tuple[str, ...]) -> str | None:
    choice = answer.get("choice") if answer.get("type") == "choice" else None
    return choice if isinstance(choice, str) and choice in identifiers else None


def validated(request: DecisionRequest, replied: object) -> Decision:
    answer = named_answer(replied, request.decision)
    choice = legal_choice(answer, request.identifiers)
    confidence = confidence_of(answer)
    if choice is None:
        return fallback(request, "the Decisions API named no legal option")
    if confidence is None or confidence < request.floor:
        return fallback(
            request, "the Decisions API answered below the confidence floor"
        )
    return Decision(
        choice,
        confidence,
        "model",
        f"{request.reason}; the Decisions API chose {choice}",
    )


def elapsed_milliseconds(started: float) -> int:
    return round((time.monotonic() - started) * 1000)


def decide(request: DecisionRequest, ask: Ask) -> Consultation:
    if len(request.options) == 1:
        return Consultation(settled(request), 0, 0, 0)
    started = time.monotonic()
    try:
        replied = ask(input_messages(request), questions(request))
    except ASK_ERRORS as error:
        miss = f"the Decisions API failed with {type(error).__name__}"
        return Consultation(
            fallback(request, miss), 1, elapsed_milliseconds(started), 0
        )
    return Consultation(
        validated(request, replied),
        1,
        elapsed_milliseconds(started),
        input_tokens(replied),
    )
