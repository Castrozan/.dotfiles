#!/usr/bin/env python3
"""
Hey Cleber — Always-on voice assistant for Clawdbot.

Uses Silero VAD + Whisper tiny for keyword detection, then records speech,
transcribes with Whisper small, sends to Clawdbot gateway, and plays back
the response via TTS + mpv over PipeWire.

Architecture:
  Phase 1 (always running): VAD detects speech → buffer → Whisper tiny →
           check for "cleber" keyword → if found, activate
  Phase 2 (on activation): Beep → record until silence → Whisper small →
           Clawdbot gateway → TTS → play → return to Phase 1

Usage:
    python3 hey-cleber.py [--debug] [--device N] [--keywords word1,word2]
"""

import argparse
import io
import json
import logging
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import onnxruntime
import requests
import sounddevice as sd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GATEWAY_URL = os.environ.get("CLAWDBOT_GATEWAY_URL", "http://localhost:18789")
GATEWAY_TOKEN = os.environ.get(
    "CLAWDBOT_GATEWAY_TOKEN",
    "REDACTED_TOKEN",
)

SAMPLE_RATE = 16000  # 16 kHz mono
CHANNELS = 1
BLOCK_SIZE = 512  # Silero VAD expects 512 samples at 16 kHz (32ms)

WHISPER_BIN = os.environ.get("WHISPER_BIN", "/run/current-system/sw/bin/whisper")
MPV_BIN = os.environ.get("MPV_BIN", "/run/current-system/sw/bin/mpv")

# Silence detection for post-keyword recording (Phase 2)
SILENCE_THRESHOLD_RMS = 300
SILENCE_DURATION_SEC = 2.0
MAX_RECORDING_SEC = 30
MIN_RECORDING_SEC = 0.5

# VAD + keyword detection settings (Phase 1)
VAD_THRESHOLD = 0.4          # Silero VAD speech probability threshold
MAX_KEYWORD_BUFFER_SEC = 5   # Max speech buffer for keyword detection
KEYWORD_SILENCE_SEC = 0.8    # Silence after speech to trigger keyword check
MIN_KEYWORD_SPEECH_SEC = 0.3 # Minimum speech to bother checking

# Default keywords and phonetic variants
DEFAULT_KEYWORDS = [
    "cleber", "kleber", "clever", "cleaver", "clebert", "cleber's",
    "kleiber", "klebber", "cleyber", "klever",
]

# Ensure PipeWire access
os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")

log = logging.getLogger("hey-cleber")


# ---------------------------------------------------------------------------
# Silero VAD (ONNX)
# ---------------------------------------------------------------------------

class SileroVAD:
    """Silero VAD using ONNX runtime (no torch needed)."""

    def __init__(self, model_path: str, threshold: float = VAD_THRESHOLD):
        self.threshold = threshold
        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = onnxruntime.InferenceSession(model_path, sess_options=opts)
        self.reset()

    def reset(self):
        """Reset internal state."""
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
        self._sr = np.array(SAMPLE_RATE, dtype=np.int64)

    def __call__(self, audio_chunk: np.ndarray) -> float:
        """Run VAD on a chunk of audio (int16 or float32). Returns speech probability."""
        if audio_chunk.dtype == np.int16:
            audio = audio_chunk.astype(np.float32) / 32767.0
        else:
            audio = audio_chunk.astype(np.float32)

        # Silero expects (batch, samples)
        audio = audio.reshape(1, -1)

        ort_inputs = {
            "input": audio,
            "h": self._h,
            "c": self._c,
            "sr": self._sr,
        }
        out, h_new, c_new = self.session.run(None, ort_inputs)
        self._h = h_new
        self._c = c_new

        return float(out[0][0])

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        return self(audio_chunk) >= self.threshold


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def rms(block: np.ndarray) -> float:
    """Root mean square of an audio block."""
    return float(np.sqrt(np.mean(block.astype(np.float64) ** 2)))


def generate_beep(freq=880, duration=0.15, sample_rate=SAMPLE_RATE, volume=0.3):
    """Generate a short beep as int16 numpy array."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave_data = (volume * 32767 * np.sin(2 * np.pi * freq * t)).astype(np.int16)
    return wave_data


def play_beep():
    """Play a short beep to indicate keyword detected."""
    try:
        beep = generate_beep()
        sd.play(beep, samplerate=SAMPLE_RATE, blocksize=4096)
        sd.wait()
    except Exception as e:
        log.warning("Could not play beep: %s", e)


def play_audio_file(path: str, interrupt_event: threading.Event | None = None):
    """Play an audio file via mpv over PipeWire."""
    env = os.environ.copy()
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    try:
        subprocess.run(
            ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"],
            env=env, capture_output=True, timeout=5,
        )
        subprocess.run(
            ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "1.0"],
            env=env, capture_output=True, timeout=5,
        )
        proc = subprocess.Popen(
            [MPV_BIN, "--no-video", "--ao=pipewire", path],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        while proc.poll() is None:
            if interrupt_event is not None and interrupt_event.is_set():
                log.info("⚡ Playback interrupted — killing mpv")
                proc.kill()
                proc.wait(timeout=5)
                return True
            time.sleep(0.05)
        return False
    except Exception as e:
        log.error("Audio playback failed: %s", e)
        return False


def save_wav(audio_data: np.ndarray, path: str):
    """Save int16 numpy array as WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())


# ---------------------------------------------------------------------------
# Recording (post-keyword, Phase 2)
# ---------------------------------------------------------------------------

def record_until_silence(
    audio_queue: queue.Queue,
    silence_thresh: float = SILENCE_THRESHOLD_RMS,
    silence_dur: float = SILENCE_DURATION_SEC,
    max_dur: float = MAX_RECORDING_SEC,
    min_dur: float = MIN_RECORDING_SEC,
) -> np.ndarray | None:
    """Record from the audio queue until silence is detected."""
    frames = []
    silence_start = None
    recording_start = time.monotonic()
    got_speech = False

    while True:
        try:
            block = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        frames.append(block)
        elapsed = time.monotonic() - recording_start
        block_rms = rms(block)

        if block_rms > silence_thresh:
            got_speech = True
            silence_start = None
        else:
            if got_speech and silence_start is None:
                silence_start = time.monotonic()

        if elapsed >= max_dur:
            log.info("Max recording duration reached (%.0fs)", max_dur)
            break

        if got_speech and silence_start is not None:
            if time.monotonic() - silence_start >= silence_dur:
                log.info("Silence detected after %.1fs of recording", elapsed)
                break

    if not frames:
        return None

    audio = np.concatenate(frames)
    duration = len(audio) / SAMPLE_RATE

    if duration < min_dur or not got_speech:
        log.info("Recording too short or no speech (%.2fs)", duration)
        return None

    return audio


# ---------------------------------------------------------------------------
# Whisper transcription
# ---------------------------------------------------------------------------

def transcribe_tiny(whisper_model, audio: np.ndarray) -> str:
    """Transcribe audio using the in-process faster-whisper tiny model."""
    audio_f32 = audio.astype(np.float32) / 32767.0
    try:
        segments, info = whisper_model.transcribe(
            audio_f32,
            beam_size=1,
            best_of=1,
            language=None,  # auto-detect for keyword (could be EN or PT)
            vad_filter=False,  # we already did VAD
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text
    except Exception as e:
        log.error("Whisper tiny transcription failed: %s", e)
        return ""


def transcribe_full(audio: np.ndarray, whisper_model=None) -> str:
    """Transcribe audio using faster-whisper small model (in-process) for high quality."""
    if whisper_model is not None:
        try:
            audio_float = audio.astype(np.float32) / 32768.0
            segments, info = whisper_model.transcribe(
                audio_float, beam_size=5, language="en",
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            return text
        except Exception as e:
            log.error("faster-whisper small transcription failed: %s", e)
            return ""
    # Fallback to CLI if no model passed
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
        save_wav(audio, wav_path)
    try:
        result = subprocess.run(
            [WHISPER_BIN, wav_path, "--model", "small", "--language", "en",
             "--output_format", "txt", "--output_dir", tempfile.gettempdir()],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            log.error("Whisper CLI failed (rc=%d): %s", result.returncode, result.stderr[:500])
        txt_path = wav_path.rsplit(".", 1)[0] + ".txt"
        if os.path.exists(txt_path):
            text = open(txt_path).read().strip()
            os.unlink(txt_path)
            return text
        else:
            log.warning("Whisper txt output not found, using stdout")
            return result.stdout.strip()
    except subprocess.TimeoutExpired:
        log.error("Whisper timed out")
        return ""
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)


# ---------------------------------------------------------------------------
# Keyword matching
# ---------------------------------------------------------------------------

def check_keyword(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in the transcription (case-insensitive)."""
    text_lower = text.lower().strip()
    if not text_lower:
        return False
    for kw in keywords:
        if kw.lower() in text_lower:
            log.debug("Keyword match: '%s' found in '%s'", kw, text_lower)
            return True
    return False


# ---------------------------------------------------------------------------
# Clawdbot Gateway
# ---------------------------------------------------------------------------

def send_to_clawdbot(message: str) -> str:
    """Send a message to Clawdbot via the OpenAI-compatible endpoint."""
    url = f"{GATEWAY_URL}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GATEWAY_TOKEN}",
        "x-clawdbot-agent-id": "main",
    }
    payload = {
        "model": "clawdbot:main",
        "user": "voice-cleber",
        "messages": [
            {
                "role": "user",
                "content": (
                    "[Voice input from microphone — respond concisely for TTS playback. "
                    "Match the user's language (English or Portuguese).]\n\n"
                    + message
                ),
            },
        ],
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.error("Gateway request failed: %s", e)
        return "Sorry, I couldn't process that request."


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

def tts_and_play(text: str, audio_q: queue.Queue | None = None,
                 speaking_flag: threading.Event | None = None) -> bool:
    """Convert text to speech and play it."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_path = f.name

        result = subprocess.run(
            [
                sys.executable, "-m", "edge_tts",
                "--text", text,
                "--voice", "en-US-GuyNeural",
                "--write-media", mp3_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            log.info("Playing TTS response via edge-tts")

            if speaking_flag is not None:
                speaking_flag.set()
                log.info("🔇 Mic muted during TTS playback")

            try:
                play_audio_file(mp3_path)
            finally:
                if speaking_flag is not None:
                    time.sleep(0.5)
                    speaking_flag.clear()
                    if audio_q is not None:
                        while not audio_q.empty():
                            try:
                                audio_q.get_nowait()
                            except queue.Empty:
                                break
                    log.info("🔊 Mic re-enabled")

            return False
    except Exception as e:
        log.warning("edge-tts failed: %s, trying fallback", e)
    finally:
        if 'mp3_path' in locals() and os.path.exists(mp3_path):
            os.unlink(mp3_path)

    try:
        subprocess.run(
            ["espeak-ng", "-s", "150", text],
            capture_output=True,
            timeout=30,
            env={**os.environ, "XDG_RUNTIME_DIR": "/run/user/1000"},
        )
    except Exception:
        log.warning("No TTS backend available. Response text: %s", text)

    return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def find_silero_vad_model() -> str:
    """Find the Silero VAD ONNX model bundled with openwakeword."""
    # Check openwakeword package first
    try:
        import openwakeword
        pkg_dir = os.path.dirname(openwakeword.__file__)
        path = os.path.join(pkg_dir, "resources", "models", "silero_vad.onnx")
        if os.path.exists(path):
            return path
    except ImportError:
        pass

    # Fallback: search in venv
    venv = Path(sys.prefix)
    for p in venv.rglob("silero_vad.onnx"):
        return str(p)

    raise FileNotFoundError("silero_vad.onnx not found. Install openwakeword or provide the model.")


def main():
    parser = argparse.ArgumentParser(description="Hey Cleber voice assistant")
    parser.add_argument("--list-devices", action="store_true",
                        help="List audio devices and exit")
    parser.add_argument("--device", type=int, default=None,
                        help="Input device index")
    parser.add_argument("--silence-threshold", type=float, default=SILENCE_THRESHOLD_RMS,
                        help="RMS silence threshold for command recording")
    parser.add_argument("--keywords", type=str, default=None,
                        help="Comma-separated list of activation keywords (default: cleber variants)")
    parser.add_argument("--vad-threshold", type=float, default=VAD_THRESHOLD,
                        help="Silero VAD speech probability threshold (default: %.1f)" % VAD_THRESHOLD)
    parser.add_argument("--debug", action="store_true")
    # Legacy args (ignored, kept for backward compat with service file)
    parser.add_argument("--wake-word", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--threshold", type=float, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.list_devices:
        print(sd.query_devices())
        return

    # Parse keywords
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = DEFAULT_KEYWORDS
    log.info("Activation keywords: %s", keywords)

    # Initialize Silero VAD
    vad_model_path = find_silero_vad_model()
    log.info("Loading Silero VAD from: %s", vad_model_path)
    vad = SileroVAD(vad_model_path, threshold=args.vad_threshold)

    # Initialize faster-whisper models
    log.info("Loading Whisper tiny model for keyword detection...")
    from faster_whisper import WhisperModel
    whisper_tiny = WhisperModel("tiny", device="cpu", compute_type="int8")
    log.info("Whisper tiny model loaded.")

    log.info("Loading Whisper small model for command transcription...")
    whisper_small = WhisperModel("small", device="cpu", compute_type="int8")
    log.info("Whisper small model loaded.")

    log.info("Starting audio stream (sample_rate=%d, block_size=%d)", SAMPLE_RATE, BLOCK_SIZE)

    # Shared state
    audio_q: queue.Queue = queue.Queue()
    is_speaking = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if status:
            log.debug("Audio status: %s", status)
        if is_speaking.is_set():
            return
        block = (indata[:, 0] * 32767).astype(np.int16)
        audio_q.put(block)

    device_kwargs = {}
    if args.device is not None:
        device_kwargs["device"] = args.device

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        blocksize=BLOCK_SIZE,
        dtype="float32",
        callback=audio_callback,
        **device_kwargs,
    )

    log.info("=== Hey Cleber is listening! Say 'Cleber' to activate. ===")

    with stream:
        while True:
            # ---------------------------------------------------------------
            # Phase 1: VAD + keyword detection
            # ---------------------------------------------------------------
            speech_buffer: list[np.ndarray] = []
            in_speech = False
            silence_after_speech_start = None
            speech_start_time = None
            buffer_duration = 0.0

            while True:
                try:
                    block = audio_q.get(timeout=1.0)
                except queue.Empty:
                    continue

                is_speech = vad.is_speech(block)
                block_dur = len(block) / SAMPLE_RATE

                if is_speech:
                    if not in_speech:
                        in_speech = True
                        speech_start_time = time.monotonic()
                        log.debug("VAD: speech started")
                    silence_after_speech_start = None
                    speech_buffer.append(block)
                    buffer_duration += block_dur

                    # Cap buffer length
                    if buffer_duration > MAX_KEYWORD_BUFFER_SEC:
                        log.debug("Keyword buffer full (%.1fs), checking...", buffer_duration)
                        break
                else:
                    if in_speech:
                        # Still buffer silence frames (they're part of the utterance tail)
                        speech_buffer.append(block)
                        buffer_duration += block_dur

                        if silence_after_speech_start is None:
                            silence_after_speech_start = time.monotonic()
                        elif time.monotonic() - silence_after_speech_start >= KEYWORD_SILENCE_SEC:
                            log.debug("VAD: speech ended (%.1fs buffered)", buffer_duration)
                            break

            # Check if we have enough speech
            if buffer_duration < MIN_KEYWORD_SPEECH_SEC:
                log.debug("Speech too short (%.2fs), ignoring", buffer_duration)
                vad.reset()
                continue

            # Transcribe with Whisper tiny
            audio_chunk = np.concatenate(speech_buffer)
            log.debug("Transcribing %.1fs of speech with Whisper tiny...", buffer_duration)
            text = transcribe_tiny(whisper_tiny, audio_chunk)
            log.debug("Whisper tiny heard: '%s'", text)

            # Check for keyword
            if not check_keyword(text, keywords):
                log.debug("No keyword found, continuing to listen")
                vad.reset()
                continue

            log.info("🎤 Keyword detected in: '%s'", text)
            vad.reset()

            # ---------------------------------------------------------------
            # Phase 2: Record command, transcribe, send to Clawdbot
            # ---------------------------------------------------------------

            # Play beep (mute mic to avoid capturing beep)
            is_speaking.set()
            play_beep()
            is_speaking.clear()

            # Drain queue (discard stale audio)
            while not audio_q.empty():
                try:
                    audio_q.get_nowait()
                except queue.Empty:
                    break

            # Record until silence
            log.info("Recording command...")
            audio = record_until_silence(
                audio_q,
                silence_thresh=args.silence_threshold,
            )

            if audio is None or len(audio) == 0:
                log.info("No speech captured, returning to listening")
                continue

            duration = len(audio) / SAMPLE_RATE
            log.info("Recorded %.1fs of audio, transcribing with Whisper small...", duration)

            # Transcribe with Whisper small (full quality, in-process)
            text = transcribe_full(audio, whisper_model=whisper_small)
            if not text:
                log.info("Empty transcription, returning to listening")
                continue

            log.info("Transcribed: '%s'", text)

            # Send to Clawdbot
            log.info("Sending to Clawdbot...")
            response = send_to_clawdbot(text)
            log.info("Response: '%s'", response[:200])

            # TTS and play
            tts_and_play(response, audio_q=audio_q, speaking_flag=is_speaking)

            log.info("=== Ready for next keyword ===")


if __name__ == "__main__":
    main()
