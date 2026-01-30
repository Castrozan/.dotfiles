# OpenClaw (formerly Clawdbot/Moltbot) - Personal AI assistant
# https://github.com/openclaw/openclaw
# https://openclaw.ai
{ pkgs, lib, ... }:
let
  nodejs = pkgs.nodejs_22;

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
    file = workspaceSymlinks // rulesSymlinks // skillsSymlinks // subagentSymlinks;
  };
}
