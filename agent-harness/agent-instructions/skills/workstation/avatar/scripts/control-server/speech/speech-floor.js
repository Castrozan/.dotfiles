const { TURN_EVENTS, TURN_PHASES, nextTurnState } = require("./speech-turn");

const IDLE_PHASE = "idle";

function createTurn(usesAgentChannel, performSpeech) {
  return {
    phase: TURN_PHASES.QUEUED,
    status: null,
    usesAgentChannel,
    performSpeech,
    playback: null,
  };
}

function isAudibleTurn(turn) {
  return (
    turn.phase === TURN_PHASES.SYNTHESIZING ||
    turn.phase === TURN_PHASES.PLAYING
  );
}

class SpeechFloor {
  constructor(agentChannel) {
    this.agentChannel = agentChannel;
    this.lastTurn = Promise.resolve();
    this.unfinishedTurns = new Set();
  }

  enqueue(usesAgentChannel, performSpeech) {
    const turn = createTurn(usesAgentChannel, performSpeech);
    this.unfinishedTurns.add(turn);
    const outcome = this.lastTurn.then(() => this.takeTurn(turn));
    this.lastTurn = outcome.catch(() => {});
    return outcome;
  }

  async takeTurn(turn) {
    try {
      if (turn.phase === TURN_PHASES.ENDED) return { status: turn.status };
      return await this.runTurn(turn);
    } catch (error) {
      this.applyTurnEvent(turn, TURN_EVENTS.FAIL);
      throw error;
    } finally {
      this.unfinishedTurns.delete(turn);
    }
  }

  async runTurn(turn) {
    this.applyTurnEvent(turn, TURN_EVENTS.BEGIN);
    const release = turn.usesAgentChannel
      ? await this.agentChannel.open()
      : null;
    try {
      await this.synthesizeAndPlay(turn);
      return { status: turn.status };
    } finally {
      turn.playback = null;
      if (release) await release();
    }
  }

  async synthesizeAndPlay(turn) {
    turn.playback = await turn.performSpeech(
      () => turn.phase !== TURN_PHASES.ENDED,
    );
    this.applyTurnEvent(turn, TURN_EVENTS.SYNTHESIZED);
    if (turn.phase === TURN_PHASES.ENDED) turn.playback.stop();
    await turn.playback.finished;
    this.applyTurnEvent(turn, TURN_EVENTS.FINISH);
  }

  interrupt() {
    for (const turn of this.unfinishedTurns) {
      this.applyTurnEvent(turn, TURN_EVENTS.INTERRUPT);
      if (turn.playback) turn.playback.stop();
    }
  }

  currentPhase() {
    const audibleTurn = [...this.unfinishedTurns].find(isAudibleTurn);
    return audibleTurn ? audibleTurn.phase : IDLE_PHASE;
  }

  applyTurnEvent(turn, event) {
    Object.assign(turn, nextTurnState(turn, event));
  }
}

module.exports = { SpeechFloor };
