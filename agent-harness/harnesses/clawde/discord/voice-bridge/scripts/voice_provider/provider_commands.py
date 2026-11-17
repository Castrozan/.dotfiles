import contextlib
import json
import signal
import sys
import wave

from voice_control import (
    connected_control_socket,
    request_running_bridge,
    send_request,
)
from voice_provider.clip_wire import BYTES_PER_MONO_SAMPLE, MAXIMUM_CLIP_BYTES
from voice_provider.pcm_conversion import STEREO_CHANNELS, mono_pcm_from_interleaved

CONNECT_TIMEOUT_SECONDS = 5
HUSH_TIMEOUT_SECONDS = 5
PLAYBACK_MARGIN_SECONDS = 120
STREAM_CHUNK_BYTES = 65536
TERMINATED_EXIT_STATUS = 128 + signal.SIGTERM


def report_error(code):
    print(json.dumps({"error": code}), file=sys.stderr)
    return 1


def relay_to_standard_output(connection):
    while chunk := connection.recv(STREAM_CHUNK_BYTES):
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
    return report_error("bridge_closed_the_connection")


def capture(_arguments):
    try:
        with connected_control_socket(timeout_seconds=CONNECT_TIMEOUT_SECONDS) as link:
            link.settimeout(None)
            send_request(link, command="capture")
            return relay_to_standard_output(link)
    except (FileNotFoundError, ConnectionRefusedError):
        return report_error("bridge_not_running")
    except BrokenPipeError:
        return 0
    except OSError as error:
        return report_error(f"capture_failed_{type(error).__name__}")


def validated_channels(clip):
    channels = clip.getnchannels()
    if clip.getsampwidth() != BYTES_PER_MONO_SAMPLE or channels > STEREO_CHANNELS:
        raise ValueError("wav_must_be_16_bit_pcm_mono_or_stereo")
    if clip.getnframes() * channels * BYTES_PER_MONO_SAMPLE > MAXIMUM_CLIP_BYTES:
        raise ValueError("wav_too_long")
    return channels


def mono_clip_from_wav(path):
    try:
        with wave.open(path, "rb") as clip:
            channels = validated_channels(clip)
            pcm = clip.readframes(clip.getnframes())
            sample_rate = clip.getframerate()
    except (wave.Error, EOFError, OSError) as error:
        raise ValueError("wav_unreadable") from error
    if not pcm:
        raise ValueError("wav_has_no_audio")
    return mono_pcm_from_interleaved(pcm, channels), sample_rate


def hush_and_exit(_signal_number, _frame):
    with contextlib.suppress(OSError, ValueError):
        request_running_bridge(command="hush", timeout_seconds=HUSH_TIMEOUT_SECONDS)
    raise SystemExit(TERMINATED_EXIT_STATUS)


def upload_clip(pcm, sample_rate):
    playback_seconds = len(pcm) / BYTES_PER_MONO_SAMPLE / sample_rate
    with connected_control_socket(timeout_seconds=CONNECT_TIMEOUT_SECONDS) as link:
        link.settimeout(playback_seconds + PLAYBACK_MARGIN_SECONDS)
        send_request(link, command="play", sample_rate=sample_rate, byte_count=len(pcm))
        link.sendall(pcm)
        with link.makefile(encoding="utf-8") as replies:
            reply = replies.readline()
    if not reply:
        return {"error": "bridge_closed_the_connection"}
    return json.loads(reply)


def play(arguments):
    try:
        pcm, sample_rate = mono_clip_from_wav(arguments.wav)
    except ValueError as error:
        return {"error": str(error)}
    signal.signal(signal.SIGTERM, hush_and_exit)
    try:
        return upload_clip(pcm, sample_rate)
    except (FileNotFoundError, ConnectionRefusedError):
        return {"error": "bridge_not_running"}


def hush(_arguments):
    return request_running_bridge(command="hush", timeout_seconds=HUSH_TIMEOUT_SECONDS)
