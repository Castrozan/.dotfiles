import json
import os
import shutil
import sys
from pathlib import Path

from staged_native_library_fixture import write_native_library_fixture

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/nixos-staged-rebuild"
SOURCE_PATH = "/nix/store/00000000000000000000000000000000-public-source"
PRIVATE_PATH = "/nix/store/11111111111111111111111111111111-private-source"
SYSTEM_PATH = "/nix/store/22222222222222222222222222222222-nixos-system-fixture"


def write_nix_client_fixture(directory):
    native = directory / "fake-nix"
    native.write_text(
        f"""#!{sys.executable}
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

arguments = sys.argv[1:]
directory = Path(os.environ["TEST_PHASE_DIRECTORY"])
with (directory / "commands").open("a") as events:
    events.write(json.dumps({{"command": Path(sys.argv[0]).name, "arguments": arguments, "pid": os.getpid(), "gc": [os.environ.get("GC_INITIAL_HEAP_SIZE"), os.environ.get("GC_FREE_SPACE_DIVISOR")]}}) + "\\n")
if "archive" in arguments:
    reference = arguments[-1]
    if "dotfiles" in reference:
        print(json.dumps({{"path": {SOURCE_PATH!r}, "inputs": {{"nested": {{"path": "/nix/store/33333333333333333333333333333333-nested-source", "inputs": {{}}}}}}}}))
    else:
        if os.environ.get("TEST_REQUIRE_PUBLIC_ROOT") == "1" and not (directory / "prefetch-public/sources").is_symlink():
            raise SystemExit("public sources were unrooted during private prefetch")
        print(json.dumps({{"path": {PRIVATE_PATH!r}, "inputs": {{"dotfiles": {{"path": {SOURCE_PATH!r}, "inputs": {{}}}}}}}}))
elif "eval" in arguments:
    (directory / "eval-pid").write_text(str(os.getpid()))
    if os.environ.get("TEST_REWRITE_REQUEST"):
        request_path = Path(os.environ["TEST_REWRITE_REQUEST"])
        request = json.loads(request_path.read_text())
        request["arguments"][0] = "switch"
        request_path.write_text(json.dumps(request))
    if os.environ.get("TEST_EVAL_HOLD") == "1":
        worker = "import os, signal, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); directory=Path(os.environ['TEST_PHASE_DIRECTORY']); (directory/'descendant-started').touch(); " + "\\nwhile not (directory/'release-descendant').exists(): time.sleep(0.01)"
        subprocess.run([sys.executable, "-c", worker], close_fds=True)
    if os.environ.get("TEST_EVAL_FAILURE"):
        raise SystemExit(int(os.environ["TEST_EVAL_FAILURE"]))
    print("/nix/store/44444444444444444444444444444444-system.drv")
elif "--realise" in arguments:
    root = Path(arguments[arguments.index("--add-root") + 1])
    if arguments[arguments.index("--realise") + 1] != "/nix/store/44444444444444444444444444444444-system.drv":
        sources = arguments[arguments.index("--realise") + 1:arguments.index("--add-root")]
        for index, source in enumerate(sources):
            source_root = root if index == 0 else root.with_name(root.name + "-" + str(index + 1))
            source_root.symlink_to(source)
            print(source)
        raise SystemExit(0)
    evaluated_process = int((directory / "eval-pid").read_text())
    try:
        os.kill(evaluated_process, 0)
    except ProcessLookupError:
        pass
    else:
        raise SystemExit("evaluation client still owns its heap during realization")
    if os.environ.get("TEST_REALISE_FAILURE"):
        raise SystemExit(int(os.environ["TEST_REALISE_FAILURE"]))
    root = Path(arguments[arguments.index("--add-root") + 1])
    root.symlink_to({SYSTEM_PATH!r})
    print({SYSTEM_PATH!r})
else:
    raise SystemExit("unexpected Nix operation")
"""
    )
    native.chmod(0o755)
    for name in ("nix", "nix-store"):
        (directory / name).symlink_to(native)


def build_staged_environment(managed_environment, directory):
    write_nix_client_fixture(directory)
    library = write_native_library_fixture(directory)
    return {
        **managed_environment,
        "BASH_ENV": "/dev/null",
        "PATH": f"{directory}:{os.environ['PATH']}",
        "PYTHONPATH": str(library),
        "PYTHONNOUSERSITE": "true",
        "REBUILD_COMMAND_TIME": shutil.which("time"),
        "NIXOS_STAGED_REBUILD_PYTHON": sys.executable,
        "NIXOS_STAGED_REBUILD_SCRIPTS": str(SCRIPTS),
        "TEST_PHASE_DIRECTORY": str(directory),
        "TEST_NATIVE_LOG": str(directory / "native-events"),
    }


def write_prepared_request(directory, action="switch", extra_arguments=()):
    request = directory / "request.json"
    request.write_text(
        json.dumps(
            {
                "arguments": [
                    action,
                    "--flake",
                    f"path:{PRIVATE_PATH}#chise",
                    "--override-input",
                    "dotfiles",
                    f"path:{SOURCE_PATH}",
                    *extra_arguments,
                ],
                "sources": [PRIVATE_PATH, SOURCE_PATH],
            }
        )
    )
    return request


def read_events(directory, name="commands"):
    path = directory / name
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )
