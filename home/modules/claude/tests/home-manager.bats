#!/usr/bin/env bats

setup_file() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    _evaluate_claude_module_data
}

setup() {
    CLAUDE_CONFIG="$BATS_FILE_TMPDIR/claude-config.json"
}

_evaluate_claude_module_data() {
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; };
        hm = dotfiles.inputs.home-manager;
        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            dotfiles.homeManagerModules.claude-code
            { home.username = "test"; home.homeDirectory = "/home/test"; home.stateVersion = "25.11"; }
          ];
        }).config;
        fileNames = builtins.attrNames cfg.home.file;
      in {
        hasSettings = builtins.hasAttr ".claude/settings.json" cfg.home.file;
        hasHooks = builtins.length (builtins.filter (n: builtins.substring 0 14 n == ".claude/hooks/") fileNames) > 0;
        hasSkills = builtins.length (builtins.filter (n: builtins.substring 0 15 n == ".claude/skills/") fileNames) > 0;
        hasMcp = builtins.hasAttr ".claude/mcp.json" cfg.home.file;
        hasBin = builtins.hasAttr ".local/bin/claude" cfg.home.file;
      }
    ' --impure --json 2>/dev/null > "$BATS_FILE_TMPDIR/claude-config.json"

    [ -s "$BATS_FILE_TMPDIR/claude-config.json" ] || {
        echo "Failed to evaluate claude module data" >&2
        return 1
    }
}

@test "claude: settings.json in home.file" {
    [ "$(jq '.hasSettings' "$CLAUDE_CONFIG")" = "true" ]
}

@test "claude: hooks directory entries in home.file" {
    [ "$(jq '.hasHooks' "$CLAUDE_CONFIG")" = "true" ]
}

@test "claude: skills directory entries in home.file" {
    [ "$(jq '.hasSkills' "$CLAUDE_CONFIG")" = "true" ]
}

@test "claude: mcp.json in home.file" {
    [ "$(jq '.hasMcp' "$CLAUDE_CONFIG")" = "true" ]
}

@test "claude: .local/bin/claude in home.file" {
    [ "$(jq '.hasBin' "$CLAUDE_CONFIG")" = "true" ]
}
