import sys
import time


def log(message):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"{timestamp} arr-config-provisioner: {message}", file=sys.stdout, flush=True)
