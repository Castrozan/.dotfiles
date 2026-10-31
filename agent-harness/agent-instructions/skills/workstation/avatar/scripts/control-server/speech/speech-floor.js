class SpeechFloor {
  constructor(agentChannel) {
    this.agentChannel = agentChannel;
    this.lastTurn = Promise.resolve();
    this.interruptions = 0;
    this.playback = null;
  }

  enqueue(usesAgentChannel, performSpeech) {
    const interruptionsAtArrival = this.interruptions;
    const turn = this.lastTurn.then(() =>
      interruptionsAtArrival === this.interruptions
        ? this.takeTurn(usesAgentChannel, performSpeech, interruptionsAtArrival)
        : { status: "cancelled" },
    );
    this.lastTurn = turn.catch(() => {});
    return turn;
  }

  async takeTurn(usesAgentChannel, performSpeech, interruptionsAtArrival) {
    const release = usesAgentChannel ? await this.agentChannel.open() : null;
    try {
      this.playback = await performSpeech();
      if (interruptionsAtArrival !== this.interruptions) this.playback.stop();
      await this.playback.finished;
      return {
        status:
          interruptionsAtArrival === this.interruptions
            ? "finished"
            : "interrupted",
      };
    } finally {
      this.playback = null;
      if (release) await release();
    }
  }

  interrupt() {
    this.interruptions += 1;
    if (this.playback) this.playback.stop();
  }
}

module.exports = { SpeechFloor };
