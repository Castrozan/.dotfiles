export const CAMERA_PHASES = Object.freeze({
  OFF: "off",
  OPENING: "opening",
  LIVE: "live",
  SYNTHETIC: "synthetic",
});

const CAMERA_TRANSITIONS = {
  open: (_phase, event) => ({
    name: CAMERA_PHASES.OPENING,
    generation: event.generation,
  }),
  synthetic: (_phase, event) => ({
    name: CAMERA_PHASES.SYNTHETIC,
    canvas: event.canvas,
  }),
  release: () => ({ name: CAMERA_PHASES.OFF }),
  ready: readyCameraPhase,
};

function readyCameraPhase(phase, event) {
  if (
    phase.name !== CAMERA_PHASES.OPENING ||
    phase.generation !== event.generation
  )
    return phase;
  return {
    name: CAMERA_PHASES.LIVE,
    generation: event.generation,
    stream: event.stream,
  };
}

export const ACTIVE_PHASES = [CAMERA_PHASES.LIVE, CAMERA_PHASES.SYNTHETIC];

export function nextCameraPhase(phase, event) {
  const transition = CAMERA_TRANSITIONS[event.type];
  return transition ? transition(phase, event) : phase;
}
