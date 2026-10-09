import http.server
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture(scope="module")
def transport_package():
    source = os.environ.get("CLAWDE_A2A_TRANSPORT_SOURCE")
    if source is None:
        pytest.skip(
            "CLAWDE_A2A_TRANSPORT_SOURCE is supplied by the packaged transport check"
        )
    package_name = "clawde_delivery_under_test"
    specification = importlib.util.spec_from_file_location(
        package_name,
        Path(source) / "a2a_server" / "__init__.py",
        submodule_search_locations=[str(Path(source) / "a2a_server")],
    )
    package = importlib.util.module_from_spec(specification)
    sys.modules[package_name] = package
    specification.loader.exec_module(package)
    return SimpleNamespace(
        resolution=importlib.import_module(
            f"{package_name}.backends.herdr_pane_resolution"
        ),
        coordinator=importlib.import_module(f"{package_name}.active_task_coordinator"),
        backend=importlib.import_module(f"{package_name}.backends.herdr_backend"),
        prompt_adapter=importlib.import_module(f"{package_name}.herdr_prompt_adapter"),
        observation=importlib.import_module(
            f"{package_name}.backends.base"
        ).BackendObservation,
        store=importlib.import_module(f"{package_name}.task_store").TaskStore,
        registry=importlib.import_module(
            f"{package_name}.fleet.registry"
        ).AttachedAgentRegistry,
        metadata=importlib.import_module(
            f"{package_name}.fleet.agent_metadata"
        ).FleetAgentMetadata,
        pane=importlib.import_module(
            f"{package_name}.fleet.discovery"
        ).DiscoveredAgentPane,
        router=importlib.import_module(
            f"{package_name}.fleet.request_router"
        ).FleetRequestRouter,
        http=importlib.import_module(f"{package_name}.fleet.http_handler"),
    )


@pytest.fixture
def owned_fleet(transport_package, monkeypatch):
    target = SimpleNamespace(
        status="working",
        harness="codex",
        draft="",
        paste_buffer="",
        commands=[],
        queued=[],
        submitted=[],
        fail_submission=False,
        ignore_submission=False,
    )

    def drive_owned_target(arguments):
        target.commands.append(arguments)
        if arguments[:2] == ["pane", "get"]:
            output = json.dumps(
                {
                    "result": {
                        "pane": {"agent": target.harness, "agent_status": target.status}
                    }
                }
            )
            return subprocess.CompletedProcess(arguments, 0, output, "")
        if arguments[:2] == ["pane", "read"]:
            if "visible" in arguments:
                prefix = {"codex": "›", "claude": "❯", "opencode": ">"}[target.harness]
                draft = target.draft or target.paste_buffer
                if not draft and target.harness == "codex":
                    draft = "\x1b[2mAsk Codex to do anything\x1b[0m"
                delivered = target.queued + target.submitted
                history = "\n".join(delivered)
                return subprocess.CompletedProcess(
                    arguments, 0, f"{history}\n\n{prefix} {draft}\n\nfooter", ""
                )
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:2] == ["pane", "send-text"]:
            target.paste_buffer += arguments[3]
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:2] == ["pane", "send-keys"]:
            if arguments[3] == "Enter":
                target.paste_buffer += "\n"
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:2] == ["agent", "send-keys"]:
            if target.fail_submission:
                return subprocess.CompletedProcess(arguments, 1, "", "agent_blocked")
            for key in arguments[3:]:
                if key == "Right":
                    target.draft += target.paste_buffer
                    target.paste_buffer = ""
                elif not target.ignore_submission and key in {"Enter", "Tab"}:
                    collection = (
                        target.queued
                        if key == "Tab" and target.status == "working"
                        else target.submitted
                    )
                    collection.append(target.draft)
                    target.draft = ""
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:2] == ["agent", "prompt"]:
            if target.fail_submission:
                return subprocess.CompletedProcess(arguments, 1, "", "agent_blocked")
            if target.harness == "codex":
                target.paste_buffer += arguments[3] + "\n"
            else:
                target.submitted.append(arguments[3])
            return subprocess.CompletedProcess(arguments, 0, "", "")
        pytest.fail(f"unexpected terminal input: {arguments}")

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", drive_owned_target
    )
    registry = transport_package.registry(transport_package.metadata({}), "")
    router = transport_package.router(registry)
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        transport_package.http.build_http_request_handler_class(router),
    )
    endpoint = f"http://127.0.0.1:{server.server_address[1]}"
    registry._daemon_base_url = endpoint
    pane = transport_package.pane(
        "owned-pane", "owned-tab", "codex", "working", "/owned"
    )
    registry.reconcile_against_the_live_fleet([pane], {"owned-tab": "owned-peer"})
    target.commands.clear()
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield SimpleNamespace(
            registry=registry,
            router=router,
            target=target,
            endpoint=endpoint,
            pane=pane,
        )
    finally:
        server.shutdown()
        worker.join(timeout=2)
        server.server_close()
        assert not worker.is_alive()
