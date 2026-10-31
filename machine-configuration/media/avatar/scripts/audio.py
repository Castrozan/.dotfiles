import contextlib
import fcntl
import json
import os
import subprocess
from pathlib import Path


CHANNELS = {"agent": "AvatarMic", "human": "AvatarHuman"}
MIX_SINK = "AvatarMix"
MEETING_SOURCE = "AvatarMicrophone"


def pulse(*arguments):
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


def pulse_items(kind):
    if kind == "modules":
        return parse_modules(pulse("list", "short", "modules"))
    return json.loads(pulse("--format=json", "list", kind))


def runtime_directory():
    return (
        Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "avatar"
    )


@contextlib.contextmanager
def exclusive_state():
    directory = runtime_directory()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / "audio.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield directory / "audio.json"


def read_state(path):
    return json.loads(path.read_text()) if path.exists() else {"modules": []}


def write_state(path, state):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state))
    temporary.chmod(0o600)
    temporary.replace(path)


def matches_module(entry, modules):
    return any(
        module["index"] == entry["index"]
        and module["name"] == entry["name"]
        and module["argument"] == entry["argument"]
        for module in modules
    )


def load_module(path, state, name, *arguments):
    identifier = int(pulse("load-module", name, *arguments))
    state["modules"].append(
        {"index": identifier, "name": name, "argument": " ".join(arguments)}
    )
    write_state(path, state)


def stop(path, state):
    modules = pulse_items("modules")
    for entry in reversed(state["modules"]):
        if matches_module(entry, modules):
            pulse("unload-module", str(entry["index"]))
    path.unlink(missing_ok=True)


def ensure_names_available():
    names = set(CHANNELS.values()) | {MIX_SINK, MEETING_SOURCE}
    existing = {
        item["name"] for kind in ("sinks", "sources") for item in pulse_items(kind)
    }
    if conflict := names & existing:
        raise ValueError(f"Refusing to adopt existing audio nodes: {sorted(conflict)}")


def validate_microphone(source_name):
    sources = pulse_items("sources")
    source = next((item for item in sources if item["name"] == source_name), None)
    if source is None:
        raise ValueError(f"Source does not exist: {source_name}")
    if source_name in {
        MEETING_SOURCE,
        *(f"{name}.monitor" for name in (*CHANNELS.values(), MIX_SINK)),
    }:
        raise ValueError("The avatar output cannot feed its own human input")
    return source_name


def load_sink(path, state, name, description):
    load_module(
        path,
        state,
        "module-null-sink",
        f"sink_name={name}",
        f"sink_properties=device.description={description}",
        "rate=48000",
        "channels=2",
    )


def load_loopback(path, state, source, sink, latency_msec=20):
    load_module(
        path,
        state,
        "module-loopback",
        f"source={source}",
        f"sink={sink}",
        f"latency_msec={latency_msec}",
        "source_dont_move=true",
        "sink_dont_move=true",
    )


def connect_microphone(path, state, source_name):
    validate_microphone(source_name)
    if state.get("microphone"):
        raise ValueError("A human input is already attached; stop before changing it")
    load_loopback(path, state, source_name, CHANNELS["human"])
    state["microphone"] = source_name
    write_state(path, state)


def start(path, state):
    modules = pulse_items("modules")
    if state.get("ready") and all(
        matches_module(entry, modules) for entry in state["modules"]
    ):
        return
    if state["modules"]:
        stop(path, state)
    ensure_names_available()
    state.clear()
    state.update({"modules": []})
    try:
        for channel, name in CHANNELS.items():
            load_sink(path, state, name, f"Avatar_{channel.title()}_Input")
            pulse("set-sink-mute", name, "1")
            pulse("set-sink-volume", name, "50%")
        load_sink(path, state, MIX_SINK, "Avatar_Meeting_Mix")
        for name in CHANNELS.values():
            load_loopback(
                path,
                state,
                f"{name}.monitor",
                MIX_SINK,
                200 if name == CHANNELS["agent"] else 20,
            )
        load_module(
            path,
            state,
            "module-remap-source",
            f"master={MIX_SINK}.monitor",
            f"source_name={MEETING_SOURCE}",
            "source_properties=device.description=Avatar_Meeting_Microphone",
        )
        state["ready"] = True
        write_state(path, state)
    except BaseException:
        stop(path, state)
        raise


def require_owned_graph(state):
    modules = pulse_items("modules")
    if not state.get("ready") or not all(
        matches_module(entry, modules) for entry in state["modules"]
    ):
        raise ValueError("Avatar audio is not running with its owned graph")


def set_channel(state, channel, operation, value):
    require_owned_graph(state)
    pulse(f"set-sink-{operation}", CHANNELS[channel], value)
