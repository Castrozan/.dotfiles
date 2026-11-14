const WebSocket = require("ws");

const SPEECH_TURN_TIMEOUT_MILLISECONDS = 300000;
const SEAT_HEALTH_URL = "http://127.0.0.1:8769/health";
const SEAT_HEALTH_TIMEOUT_MILLISECONDS = 300;
const IDENTIFIED_RESPONSES = [
  "videoModeChanged",
  "videoModeError",
  "performanceApplied",
  "performanceError",
  "characterChanged",
  "characterError",
  "cameraList",
  "cameraResult",
];

const builders = {
  status: () => ({ type: "getStatus" }),
  mode: (mode) => ({ type: "setVideoMode", mode }),
  character: (name) => ({ type: "setCharacter", name }),
  capabilities: () => ({ type: "perform", action: "capabilities" }),
  expression: (name, intensity = 1) => ({
    type: "setExpression",
    name,
    intensity: Number(intensity),
  }),
  gesture: (name) => ({ type: "perform", action: "gesture", name }),
  pose: (name) => ({ type: "perform", action: "pose", name }),
  look: (name) => ({ type: "perform", action: "look", name }),
  idle: (mode) => ({ type: "setIdle", mode }),
  presence: (presence) => ({
    type: "setPresented",
    presented: presence === "shown",
  }),
  "stop-speaking": () => ({ type: "stopSpeaking" }),
  speak: (text, emotion = "neutral", output, voice) => ({
    type: "speak",
    text,
    emotion,
    output,
    voice,
  }),
};

function parseCommand(arguments_) {
  const build = Object.hasOwn(builders, arguments_[0])
    ? builders[arguments_[0]]
    : null;
  if (!build)
    throw new Error(
      "Usage: avatar-command status | mode avatar|camera|composite | character NAME | expression NAME [INTENSITY] | gesture NAME | pose NAME | look TARGET | capabilities | idle MODE | presence shown|hidden | stop-speaking | speak TEXT [EMOTION] [mic|speakers|both|remote] [VOICE] (the output defaults to both, or to remote while a Mac holds the seat)",
    );
  return build(...arguments_.slice(1));
}

async function seatIsAttached(healthUrl = SEAT_HEALTH_URL) {
  try {
    const response = await fetch(healthUrl, {
      signal: AbortSignal.timeout(SEAT_HEALTH_TIMEOUT_MILLISECONDS),
    });
    return (await response.json()).attached === true;
  } catch {
    return false;
  }
}

async function withSpeechOutput(command, lookUpSeat = seatIsAttached) {
  if (command.type !== "speak" || command.output) return command;
  return { ...command, output: (await lookUpSeat()) ? "remote" : "both" };
}

function responseBelongsToCommand(response, command) {
  return (
    !IDENTIFIED_RESPONSES.includes(response.type) || response.id === command.id
  );
}

function handleResponse(response, context) {
  if (response.type === "identifyAck") {
    context.connection.send(JSON.stringify(context.command));
    return;
  }
  if (
    [
      "videoModeRequested",
      "performanceRequested",
      "characterRequested",
    ].includes(response.type)
  )
    return;
  if (!responseBelongsToCommand(response, context.command)) return;
  console.log(JSON.stringify(response));
  if (
    ["error", "videoModeError", "performanceError", "characterError"].includes(
      response.type,
    )
  )
    process.exitCode = 1;
  clearTimeout(context.timeout);
  context.connection.close();
}

function sendCommand(command) {
  command.id = require("node:crypto").randomUUID();
  const connection = new WebSocket("ws://127.0.0.1:8765");
  const timeout = setTimeout(
    () => {
      console.error("Avatar command timed out");
      process.exitCode = 1;
      connection.terminate();
    },
    command.type === "speak" ? SPEECH_TURN_TIMEOUT_MILLISECONDS : 10000,
  );
  const context = { connection, command, timeout };
  connection.on("open", () =>
    connection.send(JSON.stringify({ type: "identify", role: "agent" })),
  );
  connection.on("message", (bytes) =>
    handleResponse(JSON.parse(bytes.toString()), context),
  );
  connection.on("error", (error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
  connection.on("close", () => clearTimeout(timeout));
}

async function run(arguments_) {
  try {
    sendCommand(await withSpeechOutput(parseCommand(arguments_)));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

if (require.main === module) run(process.argv.slice(2));

module.exports = { parseCommand, seatIsAttached, withSpeechOutput };
