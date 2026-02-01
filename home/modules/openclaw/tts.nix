{ lib, config, ... }:
let
  tts = config.openclaw.tts;
in
{
  options.openclaw.tts = {
    voice = lib.mkOption {
      type = lib.types.str;
      default = "en-US-GuyNeural";
      description = "Default edge-tts voice for this agent";
    };

    voiceAlt = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Alternative voice for secondary language";
    };

    engine = lib.mkOption {
      type = lib.types.str;
      default = "edge-tts";
      description = "TTS engine to use";
    };
  };

  config.home.file."${config.openclaw.workspacePath}/tts.json" = {
    text = builtins.toJSON {
      engine = tts.engine;
      voice = tts.voice;
      voiceAlt = tts.voiceAlt;
    };
  };
}
