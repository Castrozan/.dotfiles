import json
import io
import runpy
import sys
from contextlib import redirect_stdout

from opencode_payload import dispatcher_payload, native_output


class HookOutputBuffer(io.StringIO):
    def __init__(self):
        super().__init__()
        self.byte_count = 0

    def write(self, text):
        self.byte_count += len(text.encode("utf-8"))
        if self.byte_count > 1024 * 1024:
            raise ValueError("Hook dispatcher output exceeded 1 MiB")
        return super().write(text)


def main():
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("OpenCode hook payload must be an object")
    captured = HookOutputBuffer()
    sys.stdin = io.StringIO(json.dumps(dispatcher_payload(payload)))
    sys.argv = sys.argv[1:]
    with redirect_stdout(captured):
        try:
            runpy.run_path(sys.argv[0], run_name="__main__")
        except SystemExit as result:
            if result.code not in (None, 0):
                raise
    if captured.getvalue().strip():
        output = json.loads(captured.getvalue())
        if not isinstance(output, dict):
            raise ValueError("OpenCode hook decision must be an object")
        print(json.dumps(native_output(output, payload.get("tool_name"))))


if __name__ == "__main__":
    main()
