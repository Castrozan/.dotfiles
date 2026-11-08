import audio_ownership
import pulse_audio
import audio_state


CHANNELS = {"agent": "AvatarMic", "human": "AvatarHuman"}
MIX_SINK = "AvatarMix"
LIP_SYNC_SINK = "AvatarLipSync"
MEETING_SOURCE = "AvatarMicrophone"


def load_pulse_module(name, *arguments):
    identifier = int(pulse_audio.run("load-module", name, *arguments))
    return {"index": identifier, "name": name, "argument": " ".join(arguments)}


def load_module(path, state, name, *arguments):
    state["modules"].append(load_pulse_module(name, *arguments))
    audio_state.write_state(path, state)


def owned_sink_names(state, modules):
    return [
        name
        for name in CHANNELS.values()
        if any(sink_matches(entry, name, modules) for entry in state["modules"])
    ]


def sink_matches(entry, name, modules):
    return (
        entry["name"] == "module-null-sink"
        and entry["argument"].startswith(f"sink_name={name} ")
        and audio_state.matches_module(entry, modules)
    )


def mute_owned_inputs(state, modules):
    owned = owned_sink_names(state, modules)
    for name in owned:
        pulse_audio.run("set-sink-mute", name, "1")
    return owned


def unload_owned_modules(state, modules):
    for entry in reversed(state["modules"]):
        if audio_state.matches_module(entry, modules):
            pulse_audio.run("unload-module", str(entry["index"]))


def tear_down(path, state):
    if not state["modules"]:
        path.unlink(missing_ok=True)
        return
    modules = pulse_audio.items("modules")
    owned = mute_owned_inputs(state, modules)
    if CHANNELS["agent"] in owned and pulse_audio.active_playbacks(CHANNELS["agent"]):
        raise ValueError(
            "Stop or reroute agent playback before removing AvatarMic; inputs remain muted"
        )
    if audio_ownership.microphone_is_live(state, modules):
        pulse_audio.run("unload-module", str(state["microphone"]["index"]))
    unload_owned_modules(state, modules)
    path.unlink(missing_ok=True)
    state.clear()
    state["modules"] = []


def ensure_names_available():
    names = set(CHANNELS.values()) | {MIX_SINK, LIP_SYNC_SINK, MEETING_SOURCE}
    existing = {
        item["name"]
        for kind in ("sinks", "sources")
        for item in pulse_audio.items(kind)
    }
    if conflict := names & existing:
        raise ValueError(f"Refusing to adopt existing audio nodes: {sorted(conflict)}")


def validate_microphone(source_name):
    sources = pulse_audio.items("sources")
    source = next((item for item in sources if item["name"] == source_name), None)
    if source is None:
        raise ValueError(f"Source does not exist: {source_name}")
    if source_name in {
        MEETING_SOURCE,
        *(f"{name}.monitor" for name in (*CHANNELS.values(), MIX_SINK, LIP_SYNC_SINK)),
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


def loopback_arguments(source, sink, latency_msec=20):
    return (
        f"source={source}",
        f"sink={sink}",
        f"latency_msec={latency_msec}",
        "source_dont_move=true",
        "sink_dont_move=true",
    )


def load_loopback(path, state, source, sink, latency_msec=20):
    load_module(
        path, state, "module-loopback", *loopback_arguments(source, sink, latency_msec)
    )


def attach_source(path, state, source_name):
    validate_microphone(source_name)
    loopback = load_pulse_module(
        "module-loopback", *loopback_arguments(source_name, CHANNELS["human"])
    )
    state["microphone"] = {"source": source_name, **loopback}
    audio_state.write_state(path, state)


def attach_default_and_unmute(path, state):
    attach_source(path, state, pulse_audio.run("get-default-source"))
    unmute_inputs()


def unmute_inputs():
    for channel in CHANNELS:
        set_channel(channel, "mute", "0")


def create_mix(path, state):
    for channel, name in CHANNELS.items():
        load_sink(path, state, name, f"Avatar_{channel.title()}_Input")
        pulse_audio.run("set-sink-mute", name, "1")
        pulse_audio.run("set-sink-volume", name, "100%")
    load_sink(path, state, MIX_SINK, "Avatar_Meeting_Mix")
    load_sink(path, state, LIP_SYNC_SINK, "Avatar_Lip_Sync")
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


def build(path, state):
    ensure_names_available()
    state.clear()
    state.update({"modules": []})
    try:
        create_mix(path, state)
        state["ready"] = True
        audio_state.write_state(path, state)
    except BaseException:
        tear_down(path, state)
        raise


def rebuild(path, state):
    tear_down(path, state)
    build(path, state)


def set_channel(channel, operation, value):
    pulse_audio.run(f"set-sink-{operation}", CHANNELS[channel], value)
