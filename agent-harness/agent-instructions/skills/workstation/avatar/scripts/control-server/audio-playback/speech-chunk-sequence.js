const NO_MORE_SPEECH = Symbol("no more speech");
const SILENT_PLAYBACK = Object.freeze({
  finished: Promise.resolve(),
  stop: () => {},
});

function prefetched(synthesis) {
  synthesis.catch(() => {});
  return synthesis;
}

class SpeechChunkSequence {
  constructor(chunkCount, { synthesizeChunk, playChunk }) {
    this.chunkCount = chunkCount;
    this.synthesizeChunk = synthesizeChunk;
    this.playChunk = playChunk;
    this.playback = SILENT_PLAYBACK;
    this.stopped = new Promise((resolve) => {
      this.signalStop = () => resolve(NO_MORE_SPEECH);
    });
  }

  stop() {
    this.signalStop();
    this.playback.stop();
  }

  async playFrom(firstSpeech) {
    let speech = firstSpeech;
    for (let index = 0; speech !== NO_MORE_SPEECH; index += 1) {
      speech = await this.playThenAwaitNext(speech, index);
    }
  }

  async playThenAwaitNext(speech, index) {
    this.playback = this.playChunk(speech, index);
    const next =
      index + 1 < this.chunkCount
        ? prefetched(this.synthesizeChunk(index + 1))
        : null;
    await this.playback.finished;
    if (!next) return NO_MORE_SPEECH;
    return Promise.race([this.stopped, next]);
  }
}

async function playSpeechChunks(chunkCount, steps) {
  const firstSpeech = await steps.synthesizeChunk(0);
  if (!steps.holdsFloor()) return SILENT_PLAYBACK;
  const sequence = new SpeechChunkSequence(chunkCount, steps);
  return {
    finished: sequence.playFrom(firstSpeech),
    stop: () => sequence.stop(),
  };
}

module.exports = { playSpeechChunks };
