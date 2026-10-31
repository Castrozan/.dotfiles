import json
import subprocess


def run(*arguments):
    completed = subprocess.run(
        ["pactl", *arguments], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def parse_modules(output):
    modules = []
    for line in output.splitlines():
        fields = line.split("\t", 3)
        if len(fields) >= 3 and fields[0].isdigit():
            modules.append(
                {"index": int(fields[0]), "name": fields[1], "argument": fields[2]}
            )
    return modules


def items(kind):
    if kind == "modules":
        return parse_modules(run("list", "short", "modules"))
    return json.loads(run("--format=json", "list", kind))


def active_playbacks(sink_name):
    sinks = [line.split("\t") for line in run("list", "short", "sinks").splitlines()]
    identifier = next(
        (fields[0] for fields in sinks if len(fields) > 1 and fields[1] == sink_name),
        None,
    )
    if identifier is None:
        return []
    inputs = [
        line.split("\t") for line in run("list", "short", "sink-inputs").splitlines()
    ]
    return [
        fields[0] for fields in inputs if len(fields) > 1 and fields[1] == identifier
    ]
