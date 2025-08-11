# TODO: This is needed?
{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    openai-whisper # The official OpenAI Whisper implementation

    # Optional dependencies
    ffmpeg
  ];

  # Create a simple script to make usage easier
  environment.shellAliases = {
    "whisper-transcribe" = "whisper --model small --language en";
  };
}
