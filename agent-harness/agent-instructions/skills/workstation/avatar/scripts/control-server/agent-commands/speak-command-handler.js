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

function announceSpeechToRenderer(clientRegistry, command, speech) {
  if (!clientRegistry.hasRenderer()) return;
  const { id, emotion, text } = command;
  clientRegistry.sendToRenderer({
    type: "startSpeaking",
    id,
    emotion,
    text,
    vowels: speech.vowels ?? [],
  });
}

function controlPlaybacks(playbacks) {
  return {
    finished: Promise.all(playbacks.map((playback) => playback.finished)),
    stop: () => {
      for (const playback of playbacks) playback.stop();
    },
  };
}

function performSpeech(command, context, delivery) {
  const { text, emotion, output, voice, id } = command;
  const { avatarState, clientRegistry, textToSpeechGenerator } = context;
  return async () => {
    avatarState.beginSpeaking(emotion);
    const speech = await textToSpeechGenerator.generate(
      text,
      id,
      voice,
      emotion,
    );
    delivery.source = speech.source;
    announceSpeechToRenderer(clientRegistry, command, speech);
    const playbacks = resolveRequestedSinks(
      output,
      context.speakerSinkName,
    ).map((sinkName) => playAudioFileToSink(speech.audioPath, sinkName));
    return controlPlaybacks(playbacks);
  };
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

  const usesAgentChannel = output === "mic" || output === "both";
  const delivery = {};
  const speech = performSpeech(
    { text, emotion, output, voice, id },
    context,
    delivery,
  );

  try {
    const { status } = await context.speechFloor.enqueue(
      usesAgentChannel,
      speech,
    );
    sendResponse(connection, {
      type: "speakAck",
      id,
      output,
      status,
      source: delivery.source,
    });
  } catch (error) {
    sendError(connection, `Speech failed: ${error.message}`);
  } finally {
    context.avatarState.finishSpeaking();
    context.clientRegistry.sendToRenderer({ type: "speechEnded", id });
  }
}

module.exports = { handleSpeakCommand };
