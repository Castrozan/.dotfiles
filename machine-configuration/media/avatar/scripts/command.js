const WebSocket = require("ws");

const builders = {
  status: () => ({ type: "getStatus" }),
  mode: (mode) => ({ type: "setVideoMode", mode }),
  expression: (name) => ({ type: "setExpression", name }),
  idle: (mode) => ({ type: "setIdle", mode }),
  speak: (text, emotion = "neutral", output = "mic", voice) => ({
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
      "Usage: avatar-command status | mode avatar|camera|composite | expression NAME | idle MODE | speak TEXT [EMOTION] [mic|speakers|both] [VOICE]",
    );
  return build(...arguments_.slice(1));
}

function responseBelongsToCommand(response, command) {
  return (
    !["videoModeChanged", "videoModeError"].includes(response.type) ||
    response.id === command.id
  );
}

function handleResponse(response, context) {
  if (response.type === "identifyAck") {
    context.connection.send(JSON.stringify(context.command));
    return;
  }
  if (response.type === "videoModeRequested") return;
  if (!responseBelongsToCommand(response, context.command)) return;
  console.log(JSON.stringify(response));
  if (["error", "videoModeError"].includes(response.type)) process.exitCode = 1;
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
    command.type === "speak" ? 120000 : 10000,
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

if (require.main === module) {
  try {
    sendCommand(parseCommand(process.argv.slice(2)));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

module.exports = { parseCommand };
