export function startFrameClock(
  framesPerSecond,
  drawFrame,
  clock = globalThis,
) {
  const frameInterval = 1000 / framesPerSecond;
  let deadline = clock.performance.now();
  const tick = () => {
    try {
      drawFrame();
    } finally {
      const now = clock.performance.now();
      deadline = Math.max(deadline + frameInterval, now);
      clock.setTimeout(tick, deadline - now);
    }
  };
  tick();
}
