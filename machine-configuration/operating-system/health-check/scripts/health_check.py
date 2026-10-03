from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from health_probes import probe_execution

DEFAULT_PROBE_TIMEOUT_SECONDS = "10"
UNKNOWN_ARGUMENT_EXIT_CODE = 2
CATEGORY_COLUMN_WIDTH = 6
COLOUR_AND_SYMBOL_PER_STATUS = {
    "pass": ("32", "✓"),
    "skip": ("90", "-"),
    "fail": ("31", "✗"),
}


@dataclass(frozen=True)
class Invocation:
    json_mode: bool
    summary_mode: bool
    category_filter: str


def usage_text(probe_timeout_seconds: str) -> str:
    return (
        "Usage: health-check [--json|--summary] [--category=<cat[,cat...]>]\n"
        "\n"
        "Categories: bin, app, config, daemon, secret, auth, nix, misc\n"
        "Statuses: pass, fail, skip. A probe skips when its applicability command\n"
        "reports the thing is not meant to be running right now, so a component that\n"
        "is dormant by design never counts as a failure.\n"
        f"Every probe is bounded at {probe_timeout_seconds}s, "
        "and exceeding that counts as a failure.\n"
        "Exit code: 0 when no applicable probe fails, 1 when any fails.\n"
    )


def parse_arguments(arguments: list[str], probe_timeout_seconds: str) -> Invocation:
    json_mode = False
    summary_mode = False
    category_filter = ""
    pending_arguments = list(arguments)
    while pending_arguments:
        argument = pending_arguments.pop(0)
        if argument == "--json":
            json_mode = True
        elif argument == "--summary":
            summary_mode = True
        elif argument == "--category":
            if not pending_arguments:
                print("missing value for --category", file=sys.stderr)
                raise SystemExit(1)
            category_filter = pending_arguments.pop(0)
        elif argument.startswith("--category="):
            category_filter = argument.removeprefix("--category=")
        elif argument in ("-h", "--help"):
            sys.stdout.write(usage_text(probe_timeout_seconds))
            raise SystemExit(0)
        else:
            print(f"unknown arg: {argument}", file=sys.stderr)
            raise SystemExit(UNKNOWN_ARGUMENT_EXIT_CODE)
    return Invocation(json_mode, summary_mode, category_filter)


def probe_is_selected(category: str, category_filter: str) -> bool:
    if not category_filter:
        return True
    return f",{category}," in f",{category_filter},"


def json_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def json_record(outcome: probe_execution.ProbeOutcome) -> str:
    fields = [
        f'"category":"{json_escape(outcome.category)}"',
        f'"name":"{json_escape(outcome.name)}"',
        f'"status":"{outcome.status}"',
    ]
    if outcome.reason:
        fields.append(f'"reason":"{json_escape(outcome.reason)}"')
    return "{" + ",".join(fields) + "}"


def human_readable_line(outcome: probe_execution.ProbeOutcome) -> str:
    colour, symbol = COLOUR_AND_SYMBOL_PER_STATUS[outcome.status]
    detail = f" ({outcome.reason})" if outcome.reason else ""
    category = outcome.category.ljust(CATEGORY_COLUMN_WIDTH)
    return f"  \033[{colour}m{symbol}\033[0m [{category}] {outcome.name}{detail}"


def totals_text(pass_count: int, fail_count: int, skip_count: int) -> str:
    total = pass_count + fail_count
    if skip_count > 0:
        return (
            f"\n{pass_count}/{total} passed ({fail_count} failed, {skip_count} skipped)"
        )
    return f"\n{pass_count}/{total} passed ({fail_count} failed)"


def main() -> int:
    probe_definitions_path, *arguments = sys.argv[1:]
    probe_timeout_seconds = (
        os.environ.get("HEALTH_CHECK_PROBE_TIMEOUT_SECONDS")
        or DEFAULT_PROBE_TIMEOUT_SECONDS
    )
    invocation = parse_arguments(arguments, probe_timeout_seconds)
    probes = json.loads(Path(probe_definitions_path).read_text())

    counts = {"pass": 0, "fail": 0, "skip": 0}
    json_records = []
    for probe in probes:
        _record_probe_result(
            probe,
            invocation,
            probe_timeout_seconds,
            counts,
            json_records,
        )

    _print_probe_summary(invocation, counts, json_records)

    return 1 if counts["fail"] > 0 else 0


def _record_probe_result(probe, invocation, timeout, counts, json_records) -> None:
    if not probe_is_selected(probe["category"], invocation.category_filter):
        return
    outcome = probe_execution.evaluate_probe(probe, timeout)
    counts[outcome.status] += 1
    if invocation.json_mode:
        json_records.append(json_record(outcome))
    elif not invocation.summary_mode:
        print(human_readable_line(outcome))


def _print_probe_summary(invocation, counts, json_records) -> None:
    if invocation.json_mode:
        print(f"[{','.join(json_records)}]")
    elif invocation.summary_mode:
        print(
            f"health-check: {counts['pass']} pass, "
            f"{counts['fail']} fail, {counts['skip']} skip"
        )
    else:
        print(totals_text(counts["pass"], counts["fail"], counts["skip"]))


if __name__ == "__main__":
    sys.exit(main())
