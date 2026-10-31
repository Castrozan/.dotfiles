const status = document.querySelector("#status");
const devices = document.querySelector("#devices");
const channel = new BroadcastChannel("avatar-local-controls");
const socket = new WebSocket("ws://127.0.0.1:8765");
socket.onopen = () => {
  socket.send(JSON.stringify({ type: "identify", role: "agent" }));
  status.textContent = "Connected";
};
socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type !== "identifyAck")
    status.textContent =
      message.message || message.error || message.mode || message.type;
};
socket.onclose = () => {
  status.textContent = "Disconnected; reload after starting the avatar";
};
document.querySelectorAll("[data-mode]").forEach((button) => {
  button.onclick = () =>
    socket.send(
      JSON.stringify({ type: "setVideoMode", mode: button.dataset.mode }),
    );
});
document.querySelector("#enable").onclick = () =>
  channel.postMessage({ type: "enableCamera", deviceId: devices.value });
document.querySelector("#disable").onclick = () =>
  channel.postMessage({ type: "disableCamera" });
channel.onmessage = async (event) => {
  if (event.data.type !== "cameraResult") return;
  status.textContent = event.data.message;
  const cameras = (await navigator.mediaDevices.enumerateDevices()).filter(
    (device) =>
      device.kind === "videoinput" && !/Avatar Cam/i.test(device.label),
  );
  devices.replaceChildren(
    ...cameras.map(
      (device) => new Option(device.label || "Camera", device.deviceId),
    ),
  );
};
