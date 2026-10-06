import importlib.util
import io
import json
import os
import runpy
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


fixture_specification = importlib.util.spec_from_file_location(
    "native_hook_fixtures",
    Path(__file__).resolve().parents[1] / "native_hook_fixtures.py",
)
hook_fixtures = importlib.util.module_from_spec(fixture_specification)
fixture_specification.loader.exec_module(hook_fixtures)


def test_dispatch_record_remains_valid_while_a_new_payload_is_published(
    tmp_path, monkeypatch, capsys
):
    launcher = hook_fixtures.write_hook_dispatcher_launcher(tmp_path)
    record = tmp_path / "dispatch.json"
    existing_payload = {"dispatcher": "earlier", "payload": {"session_id": "owned"}}
    record.write_text(json.dumps([existing_payload]))
    monkeypatch.setenv("OPENCODE_HOOK_RECORD", str(record))
    monkeypatch.setenv(
        "OPENCODE_HOOK_RESPONSES", json.dumps({"stop-dispatcher.py": "accepted"})
    )
    monkeypatch.setattr(sys, "argv", [str(launcher), "stop-dispatcher.py"])
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"stop_hook_active":true}'))
    observed_payloads = []

    def observe_write(path, contents, *arguments, **options):
        with path.open("w") as writer:
            observed_payloads.append(json.loads(record.read_text()))
            writer.write(contents)
        return len(contents)

    monkeypatch.setattr(Path, "write_text", observe_write)

    runpy.run_path(str(launcher), run_name="__main__")

    assert observed_payloads == [[existing_payload]]
    assert json.loads(record.read_text()) == [
        existing_payload,
        {"dispatcher": "stop-dispatcher.py", "payload": {"stop_hook_active": True}},
    ]
    assert capsys.readouterr().out == "accepted\n"


def test_concurrent_native_dispatchers_preserve_every_payload(tmp_path):
    launcher = hook_fixtures.write_hook_dispatcher_launcher(tmp_path)
    record = tmp_path / "dispatch.json"
    environment = os.environ | {
        "OPENCODE_HOOK_RECORD": str(record),
        "OPENCODE_HOOK_RESPONSES": "{}",
    }

    def dispatch(sequence):
        subprocess.run(
            [sys.executable, str(launcher), "stop-dispatcher.py"],
            input=json.dumps({"sequence": sequence}),
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

    with ThreadPoolExecutor(max_workers=4) as dispatchers:
        list(dispatchers.map(dispatch, range(12)))

    payloads = json.loads(record.read_text())
    assert sorted(item["payload"]["sequence"] for item in payloads) == list(range(12))
