const {
  playAudioFileToSink,
} = require("../audio-playback/pulse-audio-sink-player");
const { playSpeechChunks } = require("../audio-playback/speech-chunk-sequence");
const { speechChunks } = require("../speech/speech-chunks");
const {
  sendResponse,
  sendError,
} = require("../messaging/client-response-sender");

const MIC_SINK_NAME = "AvatarMic";
const LIP_SYNC_SINK_NAME = "AvatarLipSync";

function resolveRequestedSinks(output, speakerSinkName) {
  const sinks = [LIP_SYNC_SINK_NAME];
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

function playToRequestedSinks(audioPath, output, context) {
  return controlPlaybacks(
    resolveRequestedSinks(output, context.speakerSinkName).map((sinkName) =>
      playAudioFileToSink(audioPath, sinkName),
    ),
  );
}

function playerFor(output, context) {
  if (output === "discord") return context.playToDiscord;
  return context.playSpeech ?? playToRequestedSinks;
}

function performSpeech(command, context, delivery) {
  const { text, emotion, output, voice, model, id } = command;
  const { clientRegistry, textToSpeechGenerator } = context;
  const chunks = speechChunks(text).filter((chunk) => chunk.trim());
  return (holdsFloor) =>
    playSpeechChunks(chunks.length, {
      holdsFloor,
      synthesizeChunk: async (index) => {
        delivery.timing.synthesisStarted ??= Date.now();
        const speech = await textToSpeechGenerator.generate(
          chunks[index],
          `${id}-${index}`,
          voice,
          emotion,
          model,
        );
        delivery.sources.add(speech.source);
        delivery.timing.synthesized ??= Date.now();
        return speech;
      },
      playChunk: (speech, index) => {
        announceSpeechToRenderer(
          clientRegistry,
          { id, emotion, text: chunks[index] },
          speech,
        );
        const playback = playerFor(output, context)(
          speech.audioPath,
          output,
          context,
        );
        delivery.timing.playing ??= Date.now();
        return playback;
      },
    });
}

function isSpeakable(text) {
  return typeof text === "string" && text.trim() !== "";
}

function spokenSources(sources) {
  return [...sources].join("+") || undefined;
}

async function handleSpeakCommand(command, connection, context) {
  const {
    text,
    emotion = "neutral",
    output = "speakers",
    voice = null,
    model,
    id = Date.now().toString(),
  } = command;

  if (!isSpeakable(text)) {
    sendError(connection, "Missing required field: text");
    return;
  }

  const usesAgentChannel = output === "mic" || output === "both";
  const delivery = { sources: new Set(), timing: { received: Date.now() } };
  const speech = performSpeech(
    { text, emotion, output, voice, model, id },
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
      source: spokenSources(delivery.sources),
      timing: delivery.timing,
    });
  } catch (error) {
    sendError(connection, `Speech failed: ${error.message}`);
  } finally {
    context.clientRegistry.sendToRenderer({ type: "speechEnded", id });
  }
}

module.exports = { handleSpeakCommand };
