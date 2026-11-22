from control_server_node_runner import evaluate_node_json, requires_node
from reply_playback_harness import REPLY_PLAYBACK_HARNESS


@requires_node
def test_a_barge_in_silences_every_sink_and_acknowledges_the_turn_as_interrupted():
    result = evaluate_node_json(
        REPLY_PLAYBACK_HARNESS
        + """
        const result = (async () => {
          const spoken = speak("Reply now.");
          await settle();
          const sinks = players.map((player) => player.sink);
          bargeIn();
          await spoken;
          return {
            sinks,
            signals: players.map((player) => player.signals),
            agentMessages: agentMessages.map(({ type, status, source }) => ({
              type, status, source: source ?? null,
            })),
            rendererMessages,
          };
        })();
        """
    )
    assert result == {
        "sinks": ["AvatarLipSync", "default"],
        "signals": [["SIGTERM"], ["SIGTERM"]],
        "agentMessages": [
            {"type": "stopSpeakingAck", "status": "stopped", "source": None},
            {"type": "speakAck", "status": "interrupted", "source": "elevenlabs"},
        ],
        "rendererMessages": ["start:Reply", "speechEnded"],
    }


@requires_node
def test_the_reply_after_a_barge_in_starts_without_waiting_for_the_interrupted_one():
    result = evaluate_node_json(
        REPLY_PLAYBACK_HARNESS
        + """
        const result = (async () => {
          const first = speak("First reply.", "first");
          await settle();
          bargeIn();
          const second = speak("Second reply.", "second");
          await settle();
          const startedAfterBargeIn = roomPlayers().map((player) => player.audio);
          await finishRoomPlayback();
          await Promise.all([first, second]);
          return {
            startedAfterBargeIn,
            acknowledgements: agentMessages
              .filter((message) => message.type === "speakAck")
              .map((message) => [message.id, message.status]),
          };
        })();
        """
    )
    assert result == {
        "startedAfterBargeIn": ["/First.wav", "/Second.wav"],
        "acknowledgements": [["first", "interrupted"], ["second", "finished"]],
    }
