from control_server_node_runner import evaluate_node_json, requires_node

EXPECTED_TURN_TRANSITIONS = {
    "queued": {
        "begin": {"phase": "synthesizing", "status": None},
        "synthesized": "illegal",
        "finish": "illegal",
        "interrupt": {"phase": "ended", "status": "cancelled"},
        "fail": {"phase": "ended", "status": "failed"},
    },
    "synthesizing": {
        "begin": "illegal",
        "synthesized": {"phase": "playing", "status": None},
        "finish": "illegal",
        "interrupt": {"phase": "ended", "status": "interrupted"},
        "fail": {"phase": "ended", "status": "failed"},
    },
    "playing": {
        "begin": "illegal",
        "synthesized": "illegal",
        "finish": {"phase": "ended", "status": "finished"},
        "interrupt": {"phase": "ended", "status": "interrupted"},
        "fail": {"phase": "ended", "status": "failed"},
    },
    "ended": {
        "begin": "unchanged",
        "synthesized": "unchanged",
        "finish": "unchanged",
        "interrupt": "unchanged",
        "fail": "unchanged",
    },
}


@requires_node
def test_turn_table_covers_every_phase_and_event_and_pins_each_cell():
    result = evaluate_node_json(
        """
        const {
          TURN_PHASES,
          TURN_EVENTS,
          TURN_TRANSITIONS,
        } = require("./speech/speech-turn");
        const result = {
          phases: Object.values(TURN_PHASES),
          events: Object.values(TURN_EVENTS),
          table: TURN_TRANSITIONS,
        };
        """
    )
    assert sorted(result["table"]) == sorted(result["phases"])
    for phase in result["phases"]:
        assert sorted(result["table"][phase]) == sorted(result["events"])
    assert result["table"] == EXPECTED_TURN_TRANSITIONS


@requires_node
def test_current_phase_is_idle_then_synthesizing_then_playing_then_idle_again():
    result = evaluate_node_json(
        """
        const { SpeechFloor } = require("./speech/speech-floor");
        const settle = () => new Promise((resolve) => setTimeout(resolve, 5));
        const channel = { async open() { return async () => {}; } };
        const floor = new SpeechFloor(channel);
        const observed = [floor.currentPhase()];
        let finishPlayback;
        const playbackFinished = new Promise((resolve) => { finishPlayback = resolve; });
        const result = (async () => {
          const spoken = floor.enqueue(false, async () => {
            observed.push(floor.currentPhase());
            return { finished: playbackFinished, stop() {} };
          });
          await settle();
          observed.push(floor.currentPhase());
          finishPlayback();
          const { status } = await spoken;
          observed.push(floor.currentPhase());
          return { status, observed };
        })();
        """
    )
    assert result == {
        "status": "finished",
        "observed": ["idle", "synthesizing", "playing", "idle"],
    }
