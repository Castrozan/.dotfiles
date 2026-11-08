window.AmbientCanvasTokenFieldTimeline = (function buildTokenFieldTimeline() {
  const GENERATION_SECONDS = 40;
  const GENERATION_COUNT = 3;
  const DISSOLVE_BEGIN = 0.05;
  const DISSOLVE_SPREAD = 0.42;
  const WORD_FADE = 0.07;
  const NOISE_LINGER = 0.02;
  const NOISE_FADE = 0.07;
  const REFORM_BEGIN = 0.4;
  const REFORM_SPREAD = 0.41;
  const OUTGOING_WORD = 0;
  const OUTGOING_NOISE = 1;
  const INCOMING_NOISE = 2;
  const INCOMING_WORD = 3;

  function smootherStep(progress) {
    const clamped = Math.min(1, Math.max(0, progress));
    return clamped * clamped * clamped * (clamped * (clamped * 6 - 15) + 10);
  }

  function resolveGenerationMoment(elapsedSeconds) {
    const cycleSeconds = GENERATION_SECONDS * GENERATION_COUNT;
    const wrappedSeconds =
      ((elapsedSeconds % cycleSeconds) + cycleSeconds) % cycleSeconds;
    const generationIndex = Math.floor(wrappedSeconds / GENERATION_SECONDS);
    return {
      generationIndex,
      incomingGenerationIndex: (generationIndex + 1) % GENERATION_COUNT,
      phase: wrappedSeconds / GENERATION_SECONDS - generationIndex,
    };
  }

  function writeCellEnvelope(envelope, phase, outgoingOrder, incomingOrder) {
    const dissolveAt = DISSOLVE_BEGIN + outgoingOrder * DISSOLVE_SPREAD;
    const wordFadedOut = smootherStep((phase - dissolveAt) / WORD_FADE);
    const noiseThinned = smootherStep(
      (phase - dissolveAt - WORD_FADE - NOISE_LINGER) / NOISE_FADE,
    );
    const reformAt = REFORM_BEGIN + incomingOrder * REFORM_SPREAD;
    const noiseReturned = smootherStep((phase - reformAt) / NOISE_FADE);
    const wordReturned = smootherStep(
      (phase - reformAt - NOISE_FADE - NOISE_LINGER) / WORD_FADE,
    );
    envelope[OUTGOING_WORD] = 1 - wordFadedOut;
    envelope[OUTGOING_NOISE] = wordFadedOut * (1 - noiseThinned);
    envelope[INCOMING_NOISE] = noiseReturned * (1 - wordReturned);
    envelope[INCOMING_WORD] = wordReturned;
  }

  return {
    GENERATION_COUNT,
    cycleDurationSeconds: GENERATION_SECONDS * GENERATION_COUNT,
    OUTGOING_WORD,
    OUTGOING_NOISE,
    INCOMING_NOISE,
    INCOMING_WORD,
    resolveGenerationMoment,
    writeCellEnvelope,
  };
})();
