const RGBA_BYTES_PER_PIXEL = 4;
const RECONNECT_MILLISECONDS = 1500;

export class CameraFrameStream {
  constructor(context, width, height, url) {
    this.context = context;
    this.width = width;
    this.height = height;
    this.url = url;
    this.pixels = new Uint8Array(width * height * RGBA_BYTES_PER_PIXEL);
  }

  connect() {
    this.socket = new WebSocket(this.url);
    this.socket.onclose = () =>
      setTimeout(() => this.connect(), RECONNECT_MILLISECONDS);
  }

  sendFrame() {
    if (this.socket?.readyState !== WebSocket.OPEN) return;
    if (this.socket.bufferedAmount > this.pixels.length) return;
    this.context.readPixels(
      0,
      0,
      this.width,
      this.height,
      this.context.RGBA,
      this.context.UNSIGNED_BYTE,
      this.pixels,
    );
    this.socket.send(this.pixels);
  }
}
