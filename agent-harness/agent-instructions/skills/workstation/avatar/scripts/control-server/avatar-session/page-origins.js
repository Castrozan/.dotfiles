const REMOTE_WINDOW_PORT = "8770";
const REMOTE_SEAT_PORT = "8769";

function pageOrigins(port) {
  return [`http://localhost:${port}`, `http://127.0.0.1:${port}`];
}

function controlOrigins(rendererPort) {
  return [
    ...pageOrigins(rendererPort),
    ...pageOrigins(REMOTE_WINDOW_PORT),
    ...pageOrigins(REMOTE_SEAT_PORT),
  ];
}

module.exports = { pageOrigins, controlOrigins };
