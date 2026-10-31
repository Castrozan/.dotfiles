const WebSocket = require("ws");

function parseCommand(arguments_) {
  const [action, value, emotion = "neutral", output = "mic", voice] =
    arguments_;
  if (action === "status") return { type: "getStatus" };
  if (action === "mode") return { type: "setVideoMode", mode: value };
  if (action === "expression") return { type: "setExpression", name: value };
  if (action === "idle") return { type: "setIdle", mode: value };
  if (action === "speak")
    return { type: "speak", text: value, emotion, output, voice };
  throw new Error(
    "Usage: avatar-command status | mode avatar|camera|composite | expression NAME | idle MODE | speak TEXT [EMOTION] [mic|speakers|both] [VOICE]",
  );
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
  connection.on("open", () =>
    connection.send(JSON.stringify({ type: "identify", role: "agent" })),
  );
  connection.on("message", (bytes) => {
    const response = JSON.parse(bytes.toString());
    if (response.type === "identifyAck") {
      connection.send(JSON.stringify(command));
      return;
    }
    if (response.type === "videoModeRequested") return;
    if (
      ["videoModeChanged", "videoModeError"].includes(response.type) &&
      response.id !== command.id
    )
      return;
    console.log(JSON.stringify(response));
    if (["error", "videoModeError"].includes(response.type))
      process.exitCode = 1;
    clearTimeout(timeout);
    connection.close();
  });
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
