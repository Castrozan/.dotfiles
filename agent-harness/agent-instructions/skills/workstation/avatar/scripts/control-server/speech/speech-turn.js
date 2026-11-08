const TURN_PHASES = Object.freeze({
  QUEUED: "queued",
  SYNTHESIZING: "synthesizing",
  PLAYING: "playing",
  ENDED: "ended",
});

const TURN_EVENTS = Object.freeze({
  BEGIN: "begin",
  SYNTHESIZED: "synthesized",
  FINISH: "finish",
  INTERRUPT: "interrupt",
  FAIL: "fail",
});

const ILLEGAL = "illegal";
const UNCHANGED = "unchanged";

const TURN_TRANSITIONS = {
  [TURN_PHASES.QUEUED]: {
    [TURN_EVENTS.BEGIN]: { phase: TURN_PHASES.SYNTHESIZING, status: null },
    [TURN_EVENTS.SYNTHESIZED]: ILLEGAL,
    [TURN_EVENTS.FINISH]: ILLEGAL,
    [TURN_EVENTS.INTERRUPT]: { phase: TURN_PHASES.ENDED, status: "cancelled" },
    [TURN_EVENTS.FAIL]: { phase: TURN_PHASES.ENDED, status: "failed" },
  },
  [TURN_PHASES.SYNTHESIZING]: {
    [TURN_EVENTS.BEGIN]: ILLEGAL,
    [TURN_EVENTS.SYNTHESIZED]: { phase: TURN_PHASES.PLAYING, status: null },
    [TURN_EVENTS.FINISH]: ILLEGAL,
    [TURN_EVENTS.INTERRUPT]: {
      phase: TURN_PHASES.ENDED,
      status: "interrupted",
    },
    [TURN_EVENTS.FAIL]: { phase: TURN_PHASES.ENDED, status: "failed" },
  },
  [TURN_PHASES.PLAYING]: {
    [TURN_EVENTS.BEGIN]: ILLEGAL,
    [TURN_EVENTS.SYNTHESIZED]: ILLEGAL,
    [TURN_EVENTS.FINISH]: { phase: TURN_PHASES.ENDED, status: "finished" },
    [TURN_EVENTS.INTERRUPT]: {
      phase: TURN_PHASES.ENDED,
      status: "interrupted",
    },
    [TURN_EVENTS.FAIL]: { phase: TURN_PHASES.ENDED, status: "failed" },
  },
  [TURN_PHASES.ENDED]: {
    [TURN_EVENTS.BEGIN]: UNCHANGED,
    [TURN_EVENTS.SYNTHESIZED]: UNCHANGED,
    [TURN_EVENTS.FINISH]: UNCHANGED,
    [TURN_EVENTS.INTERRUPT]: UNCHANGED,
    [TURN_EVENTS.FAIL]: UNCHANGED,
  },
};

function nextTurnState(turn, event) {
  const transition = TURN_TRANSITIONS[turn.phase][event];
  if (transition === ILLEGAL) {
    throw new Error(`Speech turn cannot take "${event}" while ${turn.phase}`);
  }
  if (transition === UNCHANGED) {
    return { phase: turn.phase, status: turn.status };
  }
  return { ...transition };
}

module.exports = { TURN_PHASES, TURN_EVENTS, TURN_TRANSITIONS, nextTurnState };
