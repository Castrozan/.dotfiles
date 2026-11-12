const FRAME_SECONDS = 0.02;
const START_SECONDS = 0.12;
const MAXIMUM_SECONDS = 0.6;
const FULL_SCALE = 32767;

class MicrophoneFrames extends AudioWorkletProcessor {
  constructor() {
    super();
    this.frame = new Int16Array(Math.round(sampleRate * FRAME_SECONDS));
    this.filled = 0;
  }

  process(inputs) {
    const channel = inputs[0][0];
    if (!channel) return true;
    for (const sample of channel) {
      this.frame[this.filled] = Math.max(-1, Math.min(1, sample)) * FULL_SCALE;
      this.filled += 1;
      if (this.filled === this.frame.length) {
        this.port.postMessage(this.frame.slice().buffer);
        this.filled = 0;
      }
    }
    return true;
  }
}

class VoicePlayback extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunks = [];
    this.position = 0;
    this.queued = 0;
    this.buffering = true;
    this.startSamples = sampleRate * START_SECONDS;
    this.maximumSamples = sampleRate * MAXIMUM_SECONDS;
    this.port.onmessage = (event) => this.enqueue(new Int16Array(event.data));
  }

  enqueue(chunk) {
    const ahead = this.queued > this.startSamples;
    if (ahead && chunk.every((sample) => sample === 0)) return;
    this.chunks.push(chunk);
    this.queued += chunk.length;
    while (this.queued > this.maximumSamples) this.dropOldestChunk();
  }

  dropOldestChunk() {
    this.queued -= this.chunks.shift().length - this.position;
    this.position = 0;
  }

  process(inputs, outputs) {
    const output = outputs[0][0];
    if (this.buffering && this.queued < this.startSamples) return true;
    this.buffering = false;
    for (let index = 0; index < output.length; index += 1) {
      if (!this.chunks.length) {
        this.buffering = true;
        break;
      }
      output[index] = this.chunks[0][this.position] / FULL_SCALE;
      this.position += 1;
      this.queued -= 1;
      if (this.position === this.chunks[0].length) {
        this.chunks.shift();
        this.position = 0;
      }
    }
    return true;
  }
}

registerProcessor("microphone-frames", MicrophoneFrames);
registerProcessor("voice-playback", VoicePlayback);
