const CONTROL_SOCKET = "ws://localhost:8765";
const SMALLEST_REPORTED_CHANGE_SECONDS = 0.03;

export function outputDelaySeconds(context) {
  return context.baseLatency + (context.outputLatency || 0);
}

export function voiceDelays(queuedSeconds, outputsByDisplayCopy) {
  return Object.fromEntries(
    Object.entries(outputsByDisplayCopy).map(([role, context]) => [
      role,
      queuedSeconds + outputDelaySeconds(context),
    ]),
  );
}

export function changedEnough(reported, measured) {
  if (!reported) return true;
  return Object.entries(measured).some(
    ([role, seconds]) =>
      Math.abs(seconds - (reported[role] ?? 0)) >=
      SMALLEST_REPORTED_CHANGE_SECONDS,
  );
}

export function reportVoiceDelay(
  voice,
  outputsByDisplayCopy,
  socket = new WebSocket(CONTROL_SOCKET),
) {
  let reported = null;
  socket.onopen = () =>
    socket.send(JSON.stringify({ type: "identify", role: "seat" }));
  voice.port.onmessage = ({ data }) => {
    if (socket.readyState !== WebSocket.OPEN) return;
    const measured = voiceDelays(data.queuedSeconds, outputsByDisplayCopy);
    if (!changedEnough(reported, measured)) return;
    socket.send(JSON.stringify({ type: "voiceDelay", ...measured }));
    reported = measured;
  };
  return socket;
}
