import argparse
import dataclasses
import json
import sys
from pathlib import Path

import openai_decisions_api
from decision_choice import Consultation, Decision, DecisionRequest, Option, decide

HIGH_CONFIDENCE = 0.9


def parsed_request(document: dict) -> DecisionRequest:
    options = tuple(
        Option(option["id"], option["description"]) for option in document["options"]
    )
    if not options:
        raise SystemExit("a decision needs at least one legal option")
    request = DecisionRequest(
        decision=document["decision"],
        instructions=document["instructions"],
        context=document["context"],
        evidence=document["evidence"],
        options=options,
        safest=document["safest"],
        floor=float(document["floor"]),
        reason=document["reason"],
        guarded=bool(document["guarded"]),
        summary=document["summary"],
    )
    if len(options) > 1 and request.safest not in request.identifiers:
        raise SystemExit("the safest option must be legal whenever the model chooses")
    return request


def confidence_label(decision: Decision) -> str:
    if decision.source == "fallback":
        return "low"
    return "high" if decision.confidence >= HIGH_CONFIDENCE else "medium"


def metric(kind: str, name: str, unit: str, subject: str, value: float) -> dict:
    return {
        "kind": kind,
        "name": f"workflow.decision.{name}",
        "unit": unit,
        "subject": subject,
        "value": value,
    }


def metrics(request: DecisionRequest, consultation: Consultation) -> list[dict]:
    fell_back = 1 if consultation.decision.source == "fallback" else 0
    subject = request.decision
    return [
        metric("count", "model_calls", "calls", subject, consultation.model_calls),
        metric("count", "fallbacks", "decisions", subject, fell_back),
        metric("count", "input_tokens", "tokens", subject, consultation.input_tokens),
        metric("score", "latency", "ms", subject, consultation.latency_milliseconds),
    ]


def rendered(request: DecisionRequest, consultation: Consultation) -> dict:
    decision = consultation.decision
    return {
        "choice": decision.choice,
        "confidence": decision.confidence,
        "source": decision.source,
        "options": list(request.identifiers),
        "needs_human": decision.choice == request.safest
        or decision.source == "fallback",
        "recommendation": {
            "option": decision.choice,
            "why": decision.why,
            "confidence": confidence_label(decision),
        },
        "summary": request.summary,
        "metrics": metrics(request, consultation),
    }


def append_record(
    record: Path, request: DecisionRequest, consultation: Consultation
) -> None:
    record.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "decision": request.decision,
        **dataclasses.asdict(consultation.decision),
        "options": list(request.identifiers),
        "model_calls": consultation.model_calls,
        "latency_ms": consultation.latency_milliseconds,
    }
    with record.open("a") as appended:
        appended.write(json.dumps(entry) + "\n")


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="workflow-decision",
        description=(
            "Choose one legal option of a workflow decision read from stdin, asking "
            "the Decisions API only when several are legal and falling back to the "
            "safest option on any miss."
        ),
    )
    parser.add_argument("--record", type=Path, help="JSON Lines file to append to")
    return parser.parse_args(command_line_arguments)


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    request = parsed_request(json.load(sys.stdin))
    consultation = decide(request, openai_decisions_api.reply)
    if arguments.record:
        append_record(arguments.record, request, consultation)
    print(json.dumps(rendered(request, consultation)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
