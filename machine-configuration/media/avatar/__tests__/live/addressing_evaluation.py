import argparse
import dataclasses
import importlib
import json
import os
import pathlib
import statistics
import sys
import time
from types import SimpleNamespace

AVATAR = pathlib.Path(__file__).resolve().parents[2]
CASES = pathlib.Path(__file__).with_name("addressing-cases.json")
PRODUCTION_DIRECTORIES = ("addressing", "wake", "listening", "conversation", "echo")
ORDINARY_WORDS = AVATAR / "__tests__" / "unit" / "wake" / "ordinary-words.txt"
LIVE_SERVANTS = ("Ishtar", "Astolfo", "Anastasia", "Shuten-dōji", "Medea")
NO_SWITCH = ("keep", "nobody")
SWEPT_FLOORS = (0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.98)


@dataclasses.dataclass(frozen=True)
class Outcome:
    case: dict
    result: str
    decision: dict | None

    @property
    def expected(self):
        return self.case["expected"]

    @property
    def false_switch(self):
        return self.result not in NO_SWITCH and self.result != self.expected

    @property
    def missed(self):
        return self.expected not in NO_SWITCH and self.result in NO_SWITCH

    @property
    def correct(self):
        return not self.false_switch and not self.missed


def production():
    for directory in PRODUCTION_DIRECTORIES:
        sys.path.insert(0, str(AVATAR / "scripts" / directory))
    os.environ.setdefault("AVATAR_ORDINARY_WORDS", str(ORDINARY_WORDS))
    names = (
        "voice_addressing",
        "decisions_api",
        "wake_phrase",
        "conversation_addressee",
    )
    return SimpleNamespace(**{name: importlib.import_module(name) for name in names})


def holder_of(case, sessions, modules):
    held = next(
        (session for session in sessions if session.servant == case["holder"]), None
    )
    if held is None:
        return None
    return modules.conversation_addressee.Addressee(held.pane, held.servant, 0)


def addressed(case, modules, reports):
    sessions = [
        modules.wake_phrase.LiveSession(servant, f"pane-{index}")
        for index, servant in enumerate(LIVE_SERVANTS)
    ]
    holder = holder_of(case, sessions, modules)
    boundaries = SimpleNamespace(
        decide=modules.decisions_api.answers,
        report=reports.append,
        now=time.monotonic,
        addressee=lambda: holder,
        open_seat=lambda: None,
    )
    addressing = modules.voice_addressing.VoiceAddressing(
        boundaries, lambda: sessions, lambda: sessions
    )
    turn = modules.voice_addressing.Turn
    addressing.recent_turns.extend(turn(None, text) for text in case["context"])
    if holder is None:
        return addressing.wake_match(case["utterance"])
    entry = {"sequence": 1, "text": case["utterance"], "source": "human"}
    return addressing.conversation_match(entry)


def evaluated(case, modules):
    reports = []
    match = addressed(case, modules, reports)
    records = [json.loads(line) for line in reports if line.startswith("{")]
    decision = records[0] if records else None
    if match is None:
        return Outcome(case, "nobody" if case["holder"] is None else "keep", decision)
    return Outcome(case, match.session.servant.split("-")[0], decision)


def shown(outcome):
    decision = outcome.decision or {}
    verdict = decision.get("fallback") or decision.get("choice", "no candidate heard")
    mark = (
        "FALSE SWITCH" if outcome.false_switch else "MISSED" if outcome.missed else "ok"
    )
    cells = [
        outcome.case["id"],
        outcome.case["language"],
        outcome.case["kind"],
        outcome.expected,
        outcome.result,
        str(verdict),
        str(decision.get("confidence", "-")),
        str(decision.get("latency_ms", "-")),
        mark,
    ]
    return "| " + " | ".join(cells) + " |"


def switched_at(outcome, floor):
    decision = outcome.decision or {}
    choice, confidence = decision.get("choice"), decision.get("confidence")
    named = choice in decision.get("candidates", ())
    return choice if named and (confidence or 0) >= floor else "keep"


def sweep(outcomes):
    print("\n| floor | false switches | missed addresses |\n| --- | --- | --- |")
    for floor in SWEPT_FLOORS:
        results = [
            dataclasses.replace(outcome, result=switched_at(outcome, floor))
            for outcome in outcomes
        ]
        false_switches = sum(outcome.false_switch for outcome in results)
        missed = sum(outcome.missed for outcome in results)
        print(f"| {floor} | {false_switches} | {missed} |")


def summary(outcomes):
    latencies = [
        outcome.decision["latency_ms"] for outcome in outcomes if outcome.decision
    ]
    percentiles = (
        statistics.quantiles(latencies, n=20) if len(latencies) > 1 else [0] * 19
    )
    print(
        f"\ncases {len(outcomes)}, correct {sum(o.correct for o in outcomes)}, "
        f"accuracy {sum(o.correct for o in outcomes) / len(outcomes):.1%}, "
        f"false switches {sum(o.false_switch for o in outcomes)}, "
        f"missed addresses {sum(o.missed for o in outcomes)}, "
        f"API calls {len(latencies)}, "
        f"latency p50 {statistics.median(latencies or [0]):.0f} ms, "
        f"p95 {percentiles[18]:.0f} ms"
    )


def main():
    parser = argparse.ArgumentParser(prog="addressing-evaluation")
    parser.add_argument("--holdout", action="store_true")
    arguments = parser.parse_args()
    modules = production()
    cases = [
        case
        for case in json.loads(CASES.read_text())
        if case["holdout"] is arguments.holdout
    ]
    print(
        "| case | language | kind | expected | result | choice | confidence | ms "
        "| outcome |"
    )
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    outcomes = []
    for case in cases:
        outcome = evaluated(case, modules)
        outcomes.append(outcome)
        print(shown(outcome), flush=True)
    summary(outcomes)
    sweep(outcomes)


if __name__ == "__main__":
    main()
