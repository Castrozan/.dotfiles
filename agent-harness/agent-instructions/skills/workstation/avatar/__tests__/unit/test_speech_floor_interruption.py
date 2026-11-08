from control_server_node_runner import evaluate_node_json, requires_node

INTERRUPTION_HARNESS = """
const { SpeechFloor } = require("./speech/speech-floor");
const settle = () => new Promise((resolve) => setTimeout(resolve, 5));
const channel = { async open() { return async () => {}; } };
"""


@requires_node
def test_an_interrupt_during_synthesis_marks_the_turn_interrupted_before_playback():
    result = evaluate_node_json(
        INTERRUPTION_HARNESS
        + """
        const floor = new SpeechFloor(channel);
        const events = [];
        let finishSynthesis;
        const synthesized = new Promise((resolve) => { finishSynthesis = resolve; });
        const result = (async () => {
          const spoken = floor.enqueue(false, async (holdsFloor) => {
            events.push("synthesize");
            await synthesized;
            events.push(`holdsFloor:${holdsFloor()}`);
            return { finished: Promise.resolve(), stop: () => events.push("stop") };
          });
          await settle();
          floor.interrupt();
          finishSynthesis();
          const { status } = await spoken;
          return { status, events };
        })();
        """
    )
    assert result == {
        "status": "interrupted",
        "events": ["synthesize", "holdsFloor:false", "stop"],
    }


@requires_node
def test_an_interrupted_synthesis_never_starts_a_player_or_announces_speech():
    result = evaluate_node_json(
        INTERRUPTION_HARNESS
        + """
        const childProcess = require("child_process");
        const spawned = [];
        childProcess.spawn = (_, playerArguments) => {
          spawned.push(playerArguments);
          return {
            stderr: { on: () => {} },
            on: (event, resolve) => event === "close" && resolve(),
            kill: () => {},
          };
        };
        const { AvatarStateStore } = require("./avatar-session/avatar-state-store");
        const { ConnectedClientRegistry } = require("./avatar-session/connected-client-registry");
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const floor = new SpeechFloor(channel);
        const rendererMessages = [];
        const registry = new ConnectedClientRegistry();
        registry.registerRenderer({
          sendJson: (payload) => { rendererMessages.push(payload); return true; },
        });
        const agentMessages = [];
        let finishSynthesis;
        const synthesized = new Promise((resolve) => { finishSynthesis = resolve; });
        const context = {
          avatarState: new AvatarStateStore(),
          clientRegistry: registry,
          speakerSinkName: "default",
          speechFloor: floor,
          textToSpeechGenerator: {
            generate: async () => {
              await synthesized;
              return { audioPath: "/a.wav", source: "local" };
            },
          },
        };
        const result = (async () => {
          const spoken = handleSpeakCommand(
            { text: "oi", output: "speakers", id: "turn" },
            { sendJson: (message) => agentMessages.push(message) },
            context,
          );
          await settle();
          floor.interrupt();
          finishSynthesis();
          await spoken;
          return {
            spawned,
            rendererMessageTypes: rendererMessages.map((message) => message.type),
            agentMessages,
          };
        })();
        """
    )
    assert result == {
        "spawned": [],
        "rendererMessageTypes": ["speechEnded"],
        "agentMessages": [
            {
                "type": "speakAck",
                "id": "turn",
                "output": "speakers",
                "status": "interrupted",
                "source": "local",
            }
        ],
    }
