const status = document.querySelector("#status");
const devices = document.querySelector("#devices");
const socket = new WebSocket("ws://127.0.0.1:8765");

const choices = new Set();

function send(command) {
  const id = crypto.randomUUID();
  socket.send(JSON.stringify({ ...command, id }));
  return id;
}

function choose(command) {
  choices.add(send(command));
}

function listCameras({ cameras }) {
  const chosen = devices.value;
  devices.replaceChildren(
    ...cameras.map(
      (camera) => new Option(camera.label || "Camera", camera.deviceId),
    ),
  );
  if (cameras.some((camera) => camera.deviceId === chosen))
    devices.value = chosen;
}

const shown = {
  identifyAck: () => {
    status.textContent = "Connected";
    send({ type: "listCameras" });
  },
  cameraList: listCameras,
  cameraResult: ({ message, id }) => {
    status.textContent = message;
    if (choices.delete(id)) send({ type: "listCameras" });
  },
};

socket.onopen = () => {
  socket.send(JSON.stringify({ type: "identify", role: "agent" }));
};
socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (Object.hasOwn(shown, message.type)) shown[message.type](message);
  else
    status.textContent =
      message.message || message.error || message.mode || message.type;
};
socket.onclose = () => {
  status.textContent = "Disconnected; reload after starting the avatar";
};
document.querySelectorAll("[data-mode]").forEach((button) => {
  button.onclick = () =>
    send({ type: "setVideoMode", mode: button.dataset.mode });
});
document.querySelector("#enable").onclick = () =>
  choose({ type: "enableCamera", deviceId: devices.value });
document.querySelector("#disable").onclick = () =>
  choose({ type: "disableCamera" });
