const {
  playAudioFileToSink,
} = require("../audio-playback/pulse-audio-sink-player");
const {
  sendResponse,
  sendError,
} = require("../messaging/client-response-sender");

const MIC_SINK_NAME = "AvatarMic";

function resolveRequestedSinks(output, speakerSinkName) {
  const sinks = [];
  if (output === "mic" || output === "both") {
    sinks.push(MIC_SINK_NAME);
  }
  if (output === "speakers" || output === "both") {
    sinks.push(speakerSinkName);
  }
  return sinks;
}

function forwardSpeechToRenderer(
  clientRegistry,
  { id, timing, emotion, text },
) {
  clientRegistry.sendToRenderer({
    type: "startSpeaking",
    id,
    timing,
    emotion,
    text,
    audioUrl: `/audio/${id}/voice.mp3`,
  });
  console.log(
    `📤 Forwarded to renderer: startSpeaking (${timing.length} phonemes)`,
  );
}

function scheduleReturnToIdle(avatarState, durationSeconds) {
  setTimeout(
    () => {
      if (avatarState.finishSpeakingIfStillSpeaking()) {
        console.log("🔄 Auto-transitioned to IDLE");
      }
    },
    (durationSeconds + 0.5) * 1000,
  );
}

async function handleSpeakCommand(command, connection, context) {
  const {
    text,
    emotion = "neutral",
    output = "speakers",
    voice = null,
    id = Date.now().toString(),
  } = command;

  if (!text) {
    sendError(connection, "Missing required field: text");
    return;
  }

  const {
    avatarState,
    clientRegistry,
    textToSpeechGenerator,
    speakerSinkName,
  } = context;

  avatarState.beginSpeaking(emotion);

  try {
    const speech = await textToSpeechGenerator.generate(text, id, voice);

    if (clientRegistry.hasRenderer()) {
      forwardSpeechToRenderer(clientRegistry, {
        id,
        timing: speech.timing,
        emotion,
        text,
      });
      if (output === "mic" || output === "both") {
        playAudioFileToSink(speech.audioPath, MIC_SINK_NAME);
        console.log(`🔊 Playing audio to: ${MIC_SINK_NAME} (virtual mic)`);
      }
    } else {
      const sinks = resolveRequestedSinks(output, speakerSinkName);
      for (const sinkName of sinks) {
        playAudioFileToSink(speech.audioPath, sinkName);
      }
      console.log(`🔊 Playing audio to: ${sinks.join(", ")}`);
    }

    sendResponse(connection, {
      type: "speakAck",
      id,
      duration: speech.duration,
      output,
      status: "started",
    });

    scheduleReturnToIdle(avatarState, speech.duration);
  } catch (error) {
    avatarState.finishSpeaking();
    sendError(connection, `TTS generation failed: ${error.message}`);
  }
}

module.exports = { handleSpeakCommand };
