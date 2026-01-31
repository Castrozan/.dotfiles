# OpenClaw base config JSON — Nix-managed settings
# Keys defined here ALWAYS win over runtime config on rebuild.
# Runtime-only keys (added via config.patch) are preserved.
{ ... }:
let
  openclawBaseConfig = {
    env = {
      shellEnv = {
        enabled = true;
      };
    };

    browser = {
      executablePath = "/run/current-system/sw/bin/brave";
      defaultProfile = "brave";
      profiles = {
        brave = {
          cdpUrl = "http://127.0.0.1:9222";
          color = "#FB542B";
        };
        clawd = {
          cdpPort = 18800;
          color = "#FF4500";
        };
      };
    };

    auth = {
      profiles = {
        "anthropic:default" = {
          provider = "anthropic";
          mode = "token";
        };
      };
    };

    agents = {
      defaults = {
        model = {
          primary = "anthropic/claude-opus-4-5";
        };
        models = {
          "anthropic/claude-opus-4-5" = {
            alias = "opus";
          };
          "anthropic/claude-sonnet-4-5" = {
            alias = "sonnet";
          };
        };
        workspace = "/home/zanoni/clawd";
        compaction = {
          mode = "safeguard";
        };
        heartbeat = {
          every = "15m";
          target = "telegram";
          to = "8128478854";
        };
        maxConcurrent = 4;
        subagents = {
          maxConcurrent = 8;
        };
      };
    };

    tools = {
      media = {
        audio = {
          enabled = true;
          maxBytes = 20971520;
          language = "pt";
          models = [
            {
              type = "cli";
              command = "/run/current-system/sw/bin/whisper";
              args = [
                "{{MediaPath}}"
                "--language"
                "pt"
                "--model"
                "small"
                "--output_format"
                "txt"
                "--output_dir"
                "/tmp/whisper-out"
              ];
            }
          ];
        };
      };
      elevated = {
        enabled = true;
        allowFrom = {
          whatsapp = [ "+554899768269" ];
          telegram = [ "8128478854" ];
        };
      };
      exec = {
        host = "gateway";
        security = "full";
        ask = "off";
        pathPrepend = [
          "/run/wrappers/bin"
          "/run/current-system/sw/bin"
          "/etc/profiles/per-user/zanoni/bin"
          "/home/zanoni/.nix-profile/bin"
        ];
      };
    };

    messages = {
      ackReactionScope = "group-mentions";
    };

    commands = {
      native = "auto";
      nativeSkills = "auto";
      bash = true;
      config = true;
      restart = true;
    };

    hooks = {
      internal = {
        enabled = true;
        entries = {
          "boot-md" = {
            enabled = true;
          };
          "session-memory" = {
            enabled = true;
          };
          "command-logger" = {
            enabled = true;
          };
        };
      };
    };

    channels = {
      whatsapp = {
        dmPolicy = "allowlist";
        selfChatMode = true;
        allowFrom = [ "+48999768269" ];
        groupPolicy = "open";
        mediaMaxMb = 50;
        groups = {
          "*" = {
            requireMention = true;
          };
        };
        debounceMs = 0;
      };
      telegram = {
        enabled = true;
        dmPolicy = "allowlist";
        tokenFile = "/run/agenix/telegram-bot-token";
        groups = {
          "*" = {
            requireMention = true;
          };
        };
        allowFrom = [
          "8128478854" # Lucas
          "6716764001" # Joel
        ];
        groupPolicy = "open";
        streamMode = "partial";
        reactionNotifications = "all";
        reactionLevel = "minimal";
      };
    };

    gateway = {
      port = 18789;
      mode = "local";
      bind = "loopback";
      auth = {
        mode = "token";
        # Token read from agenix at runtime; this is a fallback
        token = "REDACTED_TOKEN";
      };
      tailscale = {
        mode = "off";
        resetOnExit = false;
      };
      http = {
        endpoints = {
          chatCompletions = {
            enabled = true;
          };
        };
      };
    };

    skills = {
      install = {
        nodeManager = "npm";
      };
    };

    plugins = {
      entries = {
        whatsapp = {
          enabled = true;
        };
        telegram = {
          enabled = true;
        };
      };
    };
  };
in
{
  # Write base config to ~/.openclaw/ (new canonical path)
  home.file.".openclaw/openclaw.base.json".text = builtins.toJSON openclawBaseConfig;
}
