{ pkgs }:
pkgs.fetchurl {
  url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin";
  sha256 = "1fqi0h90ig4ifpyb44cfc7dmnndv2vy5mr9g22yng9fp6nly91df";
}
