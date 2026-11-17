import signal
import subprocess
import sys
import wave

import mac_seat_client

PLAYER = "/usr/bin/afplay"
PLAYBACK_TIMEOUT_SECONDS = 310


def samples_of(recording):
    with wave.open(recording, "rb") as audio:
        return audio.readframes(audio.getnframes())


def play_through_the_speakers(recording):
    subprocess.run([PLAYER, recording], check=True, timeout=PLAYBACK_TIMEOUT_SECONDS)


def play(recording):
    if mac_seat_client.attached():
        mac_seat_client.play(samples_of(recording))
        return
    play_through_the_speakers(recording)


def hush_and_leave(signal_number, frame):
    mac_seat_client.hush()
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, hush_and_leave)
    play(sys.argv[1])


if __name__ == "__main__":
    main()
