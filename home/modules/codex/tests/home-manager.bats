#!/usr/bin/env bats

setup_file() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    _evaluate_codex_module_data
}

setup() {
    CODEX_CONFIG="$BATS_FILE_TMPDIR/codex-config.json"
}

_evaluate_codex_module_data() {
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; };
        hm = dotfiles.inputs.home-manager;
        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            dotfiles.homeManagerModules.codex
            { home.username = "test"; home.homeDirectory = "/home/test"; home.stateVersion = "25.11"; }
          ];
        }).config;
        fileNames = builtins.attrNames cfg.home.file;
      in {
        hasBin = builtins.hasAttr ".local/bin/codex" cfg.home.file;
        hasSkills = builtins.length (builtins.filter (n: builtins.substring 0 14 n == ".codex/skills/") fileNames) > 0;
      }
    ' --impure --json 2>/dev/null > "$BATS_FILE_TMPDIR/codex-config.json"

    [ -s "$BATS_FILE_TMPDIR/codex-config.json" ] || {
        echo "Failed to evaluate codex module data" >&2
        return 1
    }
}

@test "codex: .local/bin/codex in home.file" {
    [ "$(jq '.hasBin' "$CODEX_CONFIG")" = "true" ]
}

@test "codex: skills directory entries in home.file" {
    [ "$(jq '.hasSkills' "$CODEX_CONFIG")" = "true" ]
}
