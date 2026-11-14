const FRAME_SECONDS = 0.02;
const CUSHION_SECONDS = 0.12;
const MAXIMUM_SECONDS = 0.6;
const QUEUE_REPORT_SECONDS = 0.1;
const FULL_SCALE = 32767;

function isSilent(chunk) {
  return chunk.every((sample) => sample === 0);
}

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
    this.cushionSamples = Math.round(sampleRate * CUSHION_SECONDS);
    this.ring = new Float32Array(Math.round(sampleRate * MAXIMUM_SECONDS));
    this.readIndex = 0;
    this.queued = 0;
    this.buffering = true;
    this.reportSamples = Math.round(sampleRate * QUEUE_REPORT_SECONDS);
    this.samplesSinceReport = 0;
    this.port.onmessage = (event) => this.enqueue(new Int16Array(event.data));
  }

  enqueue(chunk) {
    if (this.queued > this.cushionSamples && isSilent(chunk)) return;
    for (const sample of chunk) this.write(sample / FULL_SCALE);
  }

  write(sample) {
    const capacity = this.ring.length;
    this.ring[(this.readIndex + this.queued) % capacity] = sample;
    if (this.queued < capacity) this.queued += 1;
    else this.readIndex = (this.readIndex + 1) % capacity;
  }

  read() {
    const sample = this.ring[this.readIndex];
    this.readIndex = (this.readIndex + 1) % this.ring.length;
    this.queued -= 1;
    return sample;
  }

  reportQueue(rendered) {
    this.samplesSinceReport += rendered;
    if (this.samplesSinceReport < this.reportSamples) return;
    this.samplesSinceReport = 0;
    this.port.postMessage({ queuedSeconds: this.queued / sampleRate });
  }

  process(_inputs, outputs) {
    const output = outputs[0][0];
    this.reportQueue(output.length);
    if (this.buffering && this.queued < this.cushionSamples) return true;
    const playable = Math.min(output.length, this.queued);
    for (let index = 0; index < playable; index += 1)
      output[index] = this.read();
    this.buffering = playable < output.length;
    return true;
  }
}

registerProcessor("microphone-frames", MicrophoneFrames);
registerProcessor("voice-playback", VoicePlayback);
