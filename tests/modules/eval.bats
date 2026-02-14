#!/usr/bin/env bats

setup() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
}

homeManagerModuleConfig() {
    local moduleName="$1"
    local nixExpr="$2"
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; };
        hm = dotfiles.inputs.home-manager;
        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            dotfiles.homeManagerModules.'"$moduleName"'
            { home.username = "test"; home.homeDirectory = "/home/test"; home.stateVersion = "25.11"; }
          ];
        }).config;
      in '"$nixExpr"'
    ' --impure --json 2>&1
}

homeManagerModuleConfigWithAgents() {
    local moduleName="$1"
    local nixExpr="$2"
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; };
        hm = dotfiles.inputs.home-manager;
        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            dotfiles.homeManagerModules.'"$moduleName"'
            {
              home.username = "test";
              home.homeDirectory = "/home/test";
              home.stateVersion = "25.11";
              openclaw.agents.eval-bot = {
                enable = true;
                workspace = "openclaw/eval-bot";
              };
            }
          ];
        }).config;
      in '"$nixExpr"'
    ' --impure --json 2>&1
}

# ---------- Importability ----------

@test "module: openclaw evaluates without error" {
    run homeManagerModuleConfig openclaw 'builtins.hasAttr "openclaw" cfg'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "module: claude-code evaluates without error" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".claude/settings.json" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "module: codex evaluates without error" {
    run homeManagerModuleConfig codex 'builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "module: default evaluates with all three combined" {
    run homeManagerModuleConfig default \
        'builtins.hasAttr "openclaw" cfg
         && builtins.hasAttr ".claude/settings.json" cfg.home.file
         && builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

# ---------- Openclaw ----------

@test "openclaw: config option namespace exists" {
    run homeManagerModuleConfig openclaw 'builtins.hasAttr "agents" cfg.openclaw'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "openclaw: agents attr accepts submodule type" {
    run homeManagerModuleConfigWithAgents openclaw 'builtins.hasAttr "eval-bot" cfg.openclaw.agents'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "openclaw: agent config evaluates with test agent" {
    run homeManagerModuleConfigWithAgents openclaw \
        'cfg.openclaw.agents.eval-bot.enable == true
         && cfg.openclaw.defaultAgent == "eval-bot"'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

# ---------- Claude ----------

@test "claude: settings.json in home.file (config.nix)" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".claude/settings.json" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: hooks directory entries in home.file (hooks.nix)" {
    run homeManagerModuleConfig claude-code \
        'let
           hookFiles = builtins.filter
             (n: builtins.substring 0 14 n == ".claude/hooks/")
             (builtins.attrNames cfg.home.file);
         in builtins.length hookFiles > 0'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: skills directory entries in home.file (skills.nix)" {
    run homeManagerModuleConfig claude-code \
        'let
           skillFiles = builtins.filter
             (n: builtins.substring 0 15 n == ".claude/skills/")
             (builtins.attrNames cfg.home.file);
         in builtins.length skillFiles > 0'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: mcp.json in home.file (mcp.nix)" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".claude/mcp.json" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: .local/bin/claude in home.file (claude.nix)" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".local/bin/claude" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

# ---------- Codex ----------

@test "codex: .local/bin/codex in home.file (package.nix)" {
    run homeManagerModuleConfig codex 'builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "codex: skills directory entries in home.file (skills.nix)" {
    run homeManagerModuleConfig codex \
        'let
           skillFiles = builtins.filter
             (n: builtins.substring 0 14 n == ".codex/skills/")
             (builtins.attrNames cfg.home.file);
         in builtins.length skillFiles > 0'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

# ---------- Default (combined) ----------

@test "default: has openclaw options + claude files + codex files" {
    run homeManagerModuleConfig default \
        'builtins.hasAttr "openclaw" cfg
         && builtins.hasAttr ".claude/settings.json" cfg.home.file
         && builtins.hasAttr ".claude/mcp.json" cfg.home.file
         && builtins.hasAttr ".local/bin/claude" cfg.home.file
         && builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}
