{ lib, ... }:
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault {
      ".plugins.allow" = [
        "telegram"
        "hindsight-openclaw"
        "device-pair"
        "phone-control"
        "talk-voice"
        "discord"
      ];

      ".plugins.slots.memory" = "hindsight-openclaw";

      ".plugins.entries.hindsight-openclaw" = {
        enabled = true;
        config = {
          llmProvider = "gemini";
          daemonIdleTimeout = 300;
          dynamicBankId = true;
          bankIdPrefix = "oc";
        };
      };

      ".plugins.entries.memory-core" = {
        enabled = false;
      };

      ".plugins.installs" = { };
    };
  };
}
