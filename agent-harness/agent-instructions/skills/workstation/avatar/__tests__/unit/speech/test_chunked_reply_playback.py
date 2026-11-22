from control_server_node_runner import evaluate_node_json, requires_node
from reply_playback_harness import REPLY_PLAYBACK_HARNESS

LONG_REPLY = (
    REPLY_PLAYBACK_HARNESS
    + """
const sentence = (word) => `${word} ${"and then some more words ".repeat(6)}end. `;
const reply = ["One", "Two", "Three"].map(sentence).join("");
const acknowledgement = () => agentMessages.find((message) => message.type !== "stopSpeakingAck");
"""
)


@requires_node
def test_a_long_reply_starts_after_its_first_sentence_and_synthesizes_one_ahead():
    result = evaluate_node_json(
        LONG_REPLY
        + """
        const result = (async () => {
          const steps = [];
          const spoken = speak(reply);
          for (let step = 0; step < 3; step += 1) {
            await settle();
            steps.push({
              playing: roomPlayers().map((player) => player.audio),
              synthesized: [...synthesized],
              at: Date.now(),
            });
            await finishRoomPlayback();
          }
          await spoken;
          return { steps, rendererMessages, acknowledgement: acknowledgement() };
        })();
        """
    )
    first_chunk_heard_by = [step.pop("at") for step in result["steps"]][0]
    timing = result["acknowledgement"].pop("timing")
    assert list(timing) == ["received", "synthesisStarted", "synthesized", "playing"]
    assert list(timing.values()) == sorted(timing.values())
    assert timing["playing"] <= first_chunk_heard_by
    assert result["steps"] == [
        {"playing": ["/One.wav"], "synthesized": ["One", "Two"]},
        {"playing": ["/One.wav", "/Two.wav"], "synthesized": ["One", "Two", "Three"]},
        {
            "playing": ["/One.wav", "/Two.wav", "/Three.wav"],
            "synthesized": ["One", "Two", "Three"],
        },
    ]
    assert result["rendererMessages"] == [
        "start:One",
        "start:Two",
        "start:Three",
        "speechEnded",
    ]
    assert result["acknowledgement"] == {
        "type": "speakAck",
        "id": "turn",
        "output": "speakers",
        "status": "finished",
        "source": "elevenlabs",
    }


@requires_node
def test_a_barge_in_mid_reply_silences_it_and_never_plays_the_prefetched_rest():
    result = evaluate_node_json(
        LONG_REPLY
        + """
        const result = (async () => {
          const spoken = speak(reply);
          await settle();
          bargeIn();
          await spoken;
          await settle();
          return {
            played: roomPlayers().map((player) => [player.audio, player.signals]),
            status: acknowledgement().status,
            rendererMessages,
          };
        })();
        """
    )
    assert result == {
        "played": [["/One.wav", ["SIGTERM"]]],
        "status": "interrupted",
        "rendererMessages": ["start:One", "speechEnded"],
    }


@requires_node
def test_a_barge_in_while_the_next_sentence_synthesizes_ends_the_turn_at_once():
    result = evaluate_node_json(
        LONG_REPLY
        + """
        const cloud = synthesize;
        synthesize = (text) => firstWord(text) === "Two" ? new Promise(() => {}) : cloud(text);
        const result = (async () => {
          const spoken = speak(reply, "long");
          await finishRoomPlayback();
          bargeIn();
          await spoken;
          const next = speak("After that.", "after");
          await finishRoomPlayback();
          await next;
          return {
            played: roomPlayers().map((player) => player.audio),
            acknowledgements: agentMessages
              .filter((message) => message.type === "speakAck")
              .map((message) => [message.id, message.status]),
          };
        })();
        """
    )
    assert result == {
        "played": ["/One.wav", "/After.wav"],
        "acknowledgements": [["long", "interrupted"], ["after", "finished"]],
    }


@requires_node
def test_a_sentence_that_cannot_be_voiced_stops_the_reply_and_reports_the_failure():
    result = evaluate_node_json(
        LONG_REPLY
        + """
        const cloud = synthesize;
        synthesize = async (text) => {
          if (firstWord(text) === "Two") throw new Error("no voice speaks it");
          return cloud(text);
        };
        const result = (async () => {
          const spoken = speak(reply);
          await finishRoomPlayback();
          await spoken;
          return {
            played: roomPlayers().map((player) => player.audio),
            reply: acknowledgement().error,
            rendererMessages,
          };
        })();
        """
    )
    assert result == {
        "played": ["/One.wav"],
        "reply": "Speech failed: no voice speaks it",
        "rendererMessages": ["start:One", "speechEnded"],
    }


@requires_node
def test_the_acknowledgement_names_every_source_that_voiced_the_reply():
    result = evaluate_node_json(
        LONG_REPLY
        + """
        const cloud = synthesize;
        synthesize = async (text) =>
          firstWord(text) === "Two"
            ? { audioPath: "/Two.wav", source: "kokoro" }
            : cloud(text);
        const result = (async () => {
          const spoken = speak(reply);
          for (let step = 0; step < 3; step += 1) await finishRoomPlayback();
          await spoken;
          return acknowledgement().source;
        })();
        """
    )
    assert result == "elevenlabs+kokoro"
