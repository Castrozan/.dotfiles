import os
import signal
import sys

descriptor = int(sys.argv[1])
try:
    os.write(descriptor, f"{os.getpid()}\n".encode())
except BrokenPipeError:
    raise SystemExit(1) from None
finally:
    os.close(descriptor)
for name in ("SIGPIPE", "SIGXFZ", "SIGXFSZ"):
    number = getattr(signal, name, None)
    if number is not None:
        signal.signal(number, signal.SIG_DFL)
previous = {int(number) for number in sys.argv[2].split(",") if number}
signal.pthread_sigmask(signal.SIG_SETMASK, previous)
try:
    os.execvp(sys.argv[3], sys.argv[3:])
except OSError as error:
    print(f"opencli-run: {error}", file=sys.stderr)
    raise SystemExit(1) from None
