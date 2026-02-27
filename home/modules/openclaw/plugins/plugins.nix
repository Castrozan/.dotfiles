{ ... }:
{
  config = {
    openclaw.configDeletes = [
      ".memory"
      ".plugins.entries.hindsight-openclaw"
    ];

    openclaw.configPatches = {
      ".plugins.allow" = [
        "telegram"
        "device-pair"
        "phone-control"
        "talk-voice"
        "discord"
        "memory-core"
      ];

      ".plugins.slots.memory" = "memory-core";

      ".plugins.entries.memory-core" = {
        enabled = true;
      };

      ".plugins.installs" = { };
    };
  };
}
