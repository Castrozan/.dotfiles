# Configuration for Whisper speech-to-text
{ pkgs, lib, ... }:

{
  environment.systemPackages = with pkgs; [
    # Use the official OpenAI Whisper implementation
    openai-whisper

    # Optional dependencies
    ffmpeg
  ];

  # Create a simple script to make usage easier
  environment.shellAliases = {
    "whisper-transcribe" = "whisper --model small --language en";
  };
}
