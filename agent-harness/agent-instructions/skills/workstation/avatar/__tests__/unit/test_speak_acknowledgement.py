from control_server_node_runner import evaluate_node_json, requires_node


@requires_node
def test_the_acknowledgement_names_the_voice_source_that_spoke():
    result = evaluate_node_json(
        """
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const sent = [];
        const context = {
          avatarState: { beginSpeaking: () => {}, finishSpeaking: () => {} },
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "kokoro" }) },
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform()).finished;
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
