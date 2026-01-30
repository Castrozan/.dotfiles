# clawdbot - Personal AI assistant
# https://github.com/moltbot/moltbot
# https://clawd.bot
{ pkgs, lib, ... }:
let
  nodejs = pkgs.nodejs_22;

  clawdbot = pkgs.writeShellScriptBin "clawdbot" ''
    export PATH="${nodejs}/bin:$PATH"
    export NPM_CONFIG_PREFIX="$HOME/.npm-global"
    CLAWDBOT_DIR="$HOME/.clawdbot"
    NPM_BIN="$HOME/.npm-global/bin/clawdbot"

    if [ ! -d "$CLAWDBOT_DIR" ]; then
      echo "Installing clawdbot..."
      ${pkgs.curl}/bin/curl -fsSL https://molt.bot/install.sh | ${pkgs.bash}/bin/bash
    fi

    if [ -x "$NPM_BIN" ]; then
      exec "$NPM_BIN" "$@"
    elif [ -x "$HOME/.local/bin/clawdbot" ]; then
      exec "$HOME/.local/bin/clawdbot" "$@"
    elif [ -x "$CLAWDBOT_DIR/moltbot.mjs" ]; then
      exec ${nodejs}/bin/node "$CLAWDBOT_DIR/moltbot.mjs" "$@"
    else
      echo "clawdbot not found. Running installer..."
      ${pkgs.curl}/bin/curl -fsSL https://molt.bot/install.sh | ${pkgs.bash}/bin/bash
      if [ -x "$NPM_BIN" ]; then
        exec "$NPM_BIN" "$@"
      else
        exec "$HOME/.local/bin/clawdbot" "$@"
      fi
    fi
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
      clawdbot
      nodejs
    ];
    file = workspaceSymlinks // rulesSymlinks // skillsSymlinks // subagentSymlinks;
  };
}
