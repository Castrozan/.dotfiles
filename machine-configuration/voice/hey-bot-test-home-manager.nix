{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.hey-bot;

  keywordsPrompt = builtins.concatStringsSep ", " cfg.keywords;

  heyBotTest = pkgs.writeShellApplication {
    name = "hey-bot-test";
    runtimeInputs = with pkgs; [
      whisper-cpp
      ffmpeg
      python3Packages.edge-tts
      sox
      jq
    ];
    runtimeEnv = {
      HEY_BOT_WHISPER_MODEL = cfg.whisperModel;
      HEY_BOT_KEYWORDS_PROMPT = keywordsPrompt;
    };
    text = builtins.readFile ./scripts/hey-bot-test;
  };
in
{
  config = lib.mkIf cfg.enable {
    home.packages = [ heyBotTest ];
  };
}
