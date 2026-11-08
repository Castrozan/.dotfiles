from control_server_node_runner import evaluate_node_json, requires_node


@requires_node
def test_the_acknowledgement_names_the_voice_source_that_spoke():
    result = evaluate_node_json(
        """
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const sent = [];
        const context = {
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "kokoro" }) },
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform(() => true)).finished;
              return { status: "finished" };
            },
          },
        };
        const connection = { sendJson: (message) => sent.push(message) };
        const result = handleSpeakCommand({ text: "oi", output: "none", id: "turn" }, connection, context)
          .then(() => sent);
        """
    )
    assert result == [
        {
            "type": "speakAck",
            "id": "turn",
            "output": "none",
            "status": "finished",
            "source": "kokoro",
        }
    ]


@requires_node
def test_every_output_drives_the_lip_sync_sink_so_the_mouth_moves():
    result = evaluate_node_json(
        """
        const childProcess = require("child_process");
        const played = [];
        childProcess.spawn = (_, playerArguments) => {
          played.push(playerArguments[playerArguments.indexOf("--device") + 1]);
          return {
            stderr: { on: () => {} },
            on: (event, resolve) => event === "close" && resolve(),
            kill: () => {},
          };
        };
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const context = {
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "local" }) },
          speakerSinkName: "default",
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform(() => true)).finished;
              return { status: "finished" };
            },
          },
        };
        const result = handleSpeakCommand(
          { text: "oi", output: "speakers", id: "turn" },
          { sendJson: () => {} },
          context,
        ).then(() => played);
        """
    )
    assert result == ["AvatarLipSync", "default"]
