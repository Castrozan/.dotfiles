# OpenClaw (formerly Clawdbot/Moltbot) - Personal AI assistant
# https://github.com/openclaw/openclaw
# https://openclaw.ai
{ pkgs, lib, ... }:
let
  nodejs = pkgs.nodejs_22;

  # Nix-managed core OpenClaw config (runtime fields are merged in activation)
  clawdbotBaseConfig = {
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

    model = "anthropic/claude-opus-4-5";

    agents = {
      defaults = {
        model = {
          primary = "anthropic/claude-opus-4-5";
        };
        models = {
          "anthropic/claude-opus-4-5" = {
            alias = "opus";
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
        # botToken managed at runtime via ~/.clawdbot/clawdbot.json (secret - do not commit)
        groups = {
          "*" = {
            requireMention = true;
          };
        };
        allowFrom = [
          "8128478854"
          "6716764001"
          "*"
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

  # OpenClaw wrapper — prefers npm-global install, falls back to installer
  openclaw = pkgs.writeShellScriptBin "openclaw" ''
    export PATH="${nodejs}/bin:$PATH"
    export NPM_CONFIG_PREFIX="$HOME/.npm-global"
    OPENCLAW_DIR="$HOME/.openclaw"
    NPM_BIN="$HOME/.npm-global/bin/openclaw"
    LEGACY_NPM_BIN="$HOME/.npm-global/bin/clawdbot"

    if [ -x "$NPM_BIN" ]; then
      exec "$NPM_BIN" "$@"
    elif [ -x "$LEGACY_NPM_BIN" ]; then
      exec "$LEGACY_NPM_BIN" "$@"
    elif [ -x "$OPENCLAW_DIR/openclaw.mjs" ]; then
      exec ${nodejs}/bin/node "$OPENCLAW_DIR/openclaw.mjs" "$@"
    else
      echo "OpenClaw not found. Running installer..."
      ${pkgs.curl}/bin/curl -fsSL https://openclaw.ai/install.sh | ${pkgs.bash}/bin/bash
      if [ -x "$NPM_BIN" ]; then
        exec "$NPM_BIN" "$@"
      else
        exec "$HOME/.local/bin/openclaw" "$@"
      fi
    fi
  '';

  # Backwards compatibility: clawdbot → openclaw
  clawdbot = pkgs.writeShellScriptBin "clawdbot" ''
    exec ${openclaw}/bin/openclaw "$@"
  '';

  # Layer 1: Nix-managed workspace files (read-only symlinks)
  clawdbotDir = ../../agents/clawdbot;
  clawdbotFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir clawdbotDir)
  );
  workspaceSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/${filename}";
      value = {
        source = clawdbotDir + "/${filename}";
      };
    }) clawdbotFiles
  );

  # Shared rules (from agents/rules/*.md)
  rulesDir = ../../agents/rules;
  rulesFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir rulesDir)
  );
  rulesSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/rules/${filename}";
      value = {
        source = rulesDir + "/${filename}";
      };
    }) rulesFiles
  );

  # Shared skills (from agents/skills/*/SKILL.md)
  skillsDir = ../../agents/skills;
  skillDirs = builtins.filter (name: (builtins.readDir skillsDir).${name} == "directory") (
    builtins.attrNames (builtins.readDir skillsDir)
  );
  skillsSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = "clawd/.nix/skills/${dirname}/SKILL.md";
      value = {
        source = skillsDir + "/${dirname}/SKILL.md";
      };
    }) skillDirs
  );

  # Shared subagents (from agents/subagent/*.md)
  subagentDir = ../../agents/subagent;
  subagentFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir subagentDir)
  );
  subagentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/subagents/${filename}";
      value = {
        source = subagentDir + "/${filename}";
      };
    }) subagentFiles
  );
in
{
  home = {
    packages = [
      openclaw
      clawdbot # backwards compat shim
      nodejs
    ];
    file = workspaceSymlinks // rulesSymlinks // skillsSymlinks // subagentSymlinks // {
      ".clawdbot/clawdbot.base.json".text = builtins.toJSON clawdbotBaseConfig;
    };

    activation.mergeClawdbotConfig = {
      after = [ "writeBoundary" ];
      before = [ ];
      data = ''
        BASE="$HOME/.clawdbot/clawdbot.base.json"
        RUNTIME="$HOME/.clawdbot/clawdbot.json"
        mkdir -p "$HOME/.clawdbot"
        if [ -f "$RUNTIME" ]; then
          ${pkgs.jq}/bin/jq -s '.[1] * .[0]' "$RUNTIME" "$BASE" > "$RUNTIME.tmp" && mv "$RUNTIME.tmp" "$RUNTIME"
        else
          cp "$BASE" "$RUNTIME"
        fi
      '';
    };
  };
}
