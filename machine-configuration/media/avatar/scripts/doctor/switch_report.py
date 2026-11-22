import math
from datetime import datetime

from switch_moments import BOUNDARIES

STAGE_NAMES = (
    "silence window",
    "turn judgment and queue",
    "transcription",
    "wake pickup",
    "turn assembly",
    "decision API",
    "floor handoff",
    "prompt delivery",
    "agent wake-up",
    "reply composition",
    "speech dispatch",
    "speech queue",
    "synthesis",
    "playback start",
)
STAGES = (
    *zip(STAGE_NAMES, BOUNDARIES[:-1], BOUNDARIES[1:], strict=True),
    ("end to end", BOUNDARIES[0], BOUNDARIES[-1]),
)
PERCENTILES = (50, 95)
UNRECORDED = "-"
BOUNDARY_WIDTH = 23
STAGE_WIDTH = 25


def label(boundary):
    return boundary.replace("_", " ")


def took(moments, start, end):
    if moments.get(start) is None or moments.get(end) is None:
        return None
    return moments[end] - moments[start]


def seconds(duration):
    return UNRECORDED if duration is None else f"{duration:.3f} s"


def clock(at, zone):
    if at is None:
        return UNRECORDED
    return datetime.fromtimestamp(at, zone).strftime("%H:%M:%S.%f")[:-3]


def nearest_rank(values, percentile):
    ordered = sorted(values)
    return ordered[math.ceil(percentile / 100 * len(ordered)) - 1]


def recorded_span(moments):
    recorded = [boundary for boundary in BOUNDARIES if moments[boundary] is not None]
    if len(recorded) < 2:
        return "nothing measurable"
    first, last = recorded[0], recorded[-1]
    return f"{label(first)} -> {label(last)} {seconds(took(moments, first, last))}"


def delivery_of(switch):
    if switch.delivered is None:
        return "no prompt delivery recorded"
    return f"delivered as {switch.delivered} to {switch.pane}"


def switch_lines(switch, zone):
    switched = datetime.fromtimestamp(switch.switched_at, zone)
    lines = [
        f"Switch to {switch.servant} at {switched:%Y-%m-%d %H:%M:%S}, "
        f"sequence {switch.sequence}, {delivery_of(switch)}",
        f"  {'boundary':<{BOUNDARY_WIDTH}}{'time':<14}{'stage':<{STAGE_WIDTH}}took",
        f"  {label(BOUNDARIES[0]):<{BOUNDARY_WIDTH}}"
        f"{clock(switch.moments[BOUNDARIES[0]], zone)}",
    ]
    for name, start, end in STAGES[:-1]:
        duration = took(switch.moments, start, end)
        lines.append(
            f"  {label(end):<{BOUNDARY_WIDTH}}"
            f"{clock(switch.moments[end], zone):<14}"
            f"{name:<{STAGE_WIDTH}}{seconds(duration)}"
        )
    end_to_end = took(switch.moments, BOUNDARIES[0], BOUNDARIES[-1])
    lines.append(f"  end to end {seconds(end_to_end)}")
    lines.append(f"  recorded span {recorded_span(switch.moments)}")
    return lines


def summary_lines(switches):
    header = "".join(f"p{percentile:<11}" for percentile in PERCENTILES)
    lines = [
        f"Across {len(switches)} switches (nearest-rank percentiles)",
        f"  {'stage':<{STAGE_WIDTH}}{'measured':<10}{header}".rstrip(),
    ]
    for name, start, end in STAGES:
        durations = [
            duration
            for switch in switches
            if (duration := took(switch.moments, start, end)) is not None
        ]
        cells = "".join(
            f"{seconds(nearest_rank(durations, percentile) if durations else None):<12}"
            for percentile in PERCENTILES
        )
        lines.append(f"  {name:<{STAGE_WIDTH}}{len(durations):<10}{cells}".rstrip())
    return lines


def report(switches, zone=None):
    lines = []
    for switch in switches:
        lines.extend(switch_lines(switch, zone))
        lines.append("")
    return "\n".join([*lines, *summary_lines(switches)])
