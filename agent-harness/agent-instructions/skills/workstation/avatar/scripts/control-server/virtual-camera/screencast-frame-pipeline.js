const { spawn } = require("child_process");

class ScreencastFramePipeline {
  constructor({ framesPerSecond, width, height, videoDevice }) {
    this.encoder = spawn(
      "ffmpeg",
      [
        "-y",
        "-probesize",
        "32",
        "-analyzeduration",
        "0",
        "-threads",
        "1",
        "-f",
        "mjpeg",
        "-framerate",
        String(framesPerSecond),
        "-i",
        "pipe:0",
        "-vf",
        `scale=${width}:${height}`,
        "-pix_fmt",
        "yuv420p",
        "-threads:v",
        "1",
        "-f",
        "v4l2",
        videoDevice,
      ],
      { stdio: ["pipe", "pipe", "pipe"] },
    );

    this.encoder.stdin.on("error", (error) => console.error(error.message));

    this.encoder.stderr.on("data", (chunk) => {
      const line = chunk.toString().trim();
      if (line && !line.startsWith("frame=")) {
        console.log(`[ffmpeg] ${line}`);
      }
    });

    this.encoder.on("close", (exitCode) => {
      console.log(`[ffmpeg] Exited with code ${exitCode}`);
      process.exit(exitCode || process.exitCode || 0);
    });
  }

  writeFrame(frameBuffer) {
    if (this.encoder.stdin.destroyed || this.encoder.stdin.writableNeedDrain) {
      return false;
    }
    this.encoder.stdin.write(frameBuffer);
    return true;
  }

  end() {
    this.encoder.stdin.end();
  }
}

module.exports = { ScreencastFramePipeline };
