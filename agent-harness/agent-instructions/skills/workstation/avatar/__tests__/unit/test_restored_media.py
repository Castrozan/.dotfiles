from control_server_node_runner import evaluate_node_json, requires_node


@requires_node
def test_audio_meter_uses_actual_waveform_energy():
    result = evaluate_node_json(
        """
        const { measureLevel } = require("./audio-playback/microphone-level-meter");
        const samples = Buffer.alloc(16);
        [0.5, -0.5, 0.5, -0.5].forEach((value, index) => samples.writeFloatLE(value, index * 4));
        const result = { active: measureLevel(samples), silent: measureLevel(Buffer.alloc(16)), empty: measureLevel(Buffer.alloc(0)) };
        """
    )
    assert result == {"active": 0.5, "silent": 0, "empty": 0}


@requires_node
def test_multiple_agents_can_connect_and_receive_renderer_result():
    result = evaluate_node_json(
        """
        const { ConnectedClientRegistry } = require("./avatar-session/connected-client-registry");
        const registry = new ConnectedClientRegistry();
        const first = { closed: false, sent: [], close() { this.closed = true; }, sendJson(value) { this.sent.push(value); } };
        const second = { ...first, sent: [] };
        registry.registerAgent(first);
        registry.registerAgent(second);
        registry.sendToAgents({ type: "videoModeChanged", mode: "avatar" });
        registry.forget(first);
        const result = { firstClosed: first.closed, firstMessages: first.sent.length, secondMessages: second.sent.length, secondActive: registry.isAgent(second) };
        """
    )
    assert result == {
        "firstClosed": False,
        "firstMessages": 1,
        "secondMessages": 1,
        "secondActive": True,
    }


@requires_node
def test_video_mode_rejects_invalid_request_and_absent_renderer():
    result = evaluate_node_json(
        """
        const { handleSetVideoModeCommand } = require("./agent-commands/set-video-mode-command-handler");
        const sent = [];
        const connection = { isOpen: () => true, sendJson: (value) => sent.push(value) };
        const context = { clientRegistry: { sendToRenderer: () => false } };
        handleSetVideoModeCommand({ mode: "unknown" }, connection, context);
        handleSetVideoModeCommand({ mode: "avatar" }, connection, context);
        const result = sent;
        """
    )
    assert len(result) == 2
    assert result[0]["type"] == result[1]["type"] == "error"
    assert "No renderer" in result[1]["error"]


@requires_node
def test_video_mode_preserves_request_identity():
    result = evaluate_node_json(
        """
        const { handleSetVideoModeCommand } = require("./agent-commands/set-video-mode-command-handler");
        const sent = [];
        const forwarded = [];
        handleSetVideoModeCommand({ mode: "avatar", id: "request-1" }, { sendJson: value => sent.push(value) }, { clientRegistry: { sendToRenderer: value => { forwarded.push(value); return true; } } });
        const result = { forwarded, sent };
        """
    )
    assert result["forwarded"][0]["id"] == result["sent"][0]["id"] == "request-1"
