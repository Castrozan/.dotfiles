const LONGEST_VOICE_DELAY_SECONDS = 2;

function plausibleDelaySeconds(seconds) {
  return (
    Number.isFinite(seconds) &&
    seconds >= 0 &&
    seconds <= LONGEST_VOICE_DELAY_SECONDS
  );
}

class DelayedVoiceLevels {
  constructor(deliver, schedule = setTimeout, now = Date.now) {
    this.deliver = deliver;
    this.schedule = schedule;
    this.now = now;
    this.delaySeconds = 0;
    this.lastDueTime = 0;
  }

  followVoiceDelay(seconds) {
    if (!plausibleDelaySeconds(seconds)) return;
    this.delaySeconds = seconds;
  }

  forgetVoiceDelay() {
    this.delaySeconds = 0;
  }

  send(payload) {
    const now = this.now();
    const dueTime = Math.max(now + this.delaySeconds * 1000, this.lastDueTime);
    this.lastDueTime = dueTime;
    if (dueTime <= now) {
      this.deliver(payload);
      return;
    }
    this.schedule(() => this.deliver(payload), dueTime - now);
  }
}

module.exports = { DelayedVoiceLevels };
