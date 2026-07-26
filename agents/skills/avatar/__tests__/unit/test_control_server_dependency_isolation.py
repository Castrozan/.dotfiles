import re

from control_server_node_runner import (
    ISOLATED_DEPENDENCY_PACKAGES,
    adapter_javascript_files,
    domain_javascript_files,
    requires_node,
    run_node_expression,
)


def require_calls_in(source):
    return set(re.findall(r"""require\(\s*["']([^"']+)["']\s*\)""", source))


def third_party_requires_in(source):
    return {
        name
        for name in require_calls_in(source)
        if name in ISOLATED_DEPENDENCY_PACKAGES
    }


def test_domain_modules_never_require_an_isolated_dependency_directly():
    offenders = {
        path.name: sorted(third_party_requires_in(path.read_text()))
        for path in domain_javascript_files()
        if third_party_requires_in(path.read_text())
    }
    assert offenders == {}


def test_every_isolated_dependency_has_exactly_one_adapter_importing_it():
    importers_by_package = {name: [] for name in ISOLATED_DEPENDENCY_PACKAGES}
    for path in adapter_javascript_files():
        for name in third_party_requires_in(path.read_text()):
            importers_by_package[name].append(path.name)

    assert sorted(importers_by_package["express"]) == [
        "express-audio-file-http-server.js"
    ]
    assert sorted(importers_by_package["ws"]) == [
        "websocket-message-socket-client.js",
        "websocket-message-socket-server.js",
    ]


def test_every_port_declares_an_unimplemented_guard():
    port_files = [
        path for path in adapter_javascript_files() if path.name.endswith("-port.js")
    ]
    assert port_files
    for path in port_files:
        assert "must be implemented by an adapter" in path.read_text()


@requires_node
def test_domain_modules_load_without_any_installed_dependency():
    run_node_expression(
        """
        require("./avatar-session/client-connection-router");
        require("./avatar-session/avatar-state-store");
        require("./avatar-session/connected-client-registry");
        require("./agent-commands/agent-command-router");
        require("./speech/speech-timing-parser");
        require("./speech/text-to-speech-generator");
        require("./audio-playback/pulse-audio-sink-player");
        require("./chrome-devtools/chrome-devtools-session");
        require("./chrome-devtools/chrome-devtools-target-locator");
        require("./virtual-camera/screencast-frame-pipeline");
        """
    )


@requires_node
def test_calling_an_unimplemented_port_method_throws():
    run_node_expression(
        """
        const {
          MessageSocketServerPort,
        } = require("./dependencies/message-socket-server/message-socket-server-port");
        let threw = false;
        try {
          new MessageSocketServerPort().onConnection(() => {});
        } catch (error) {
          threw = error.message.includes("must be implemented by an adapter");
        }
        if (!threw) {
          process.exit(1);
        }
        """
    )
