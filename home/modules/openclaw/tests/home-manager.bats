#!/usr/bin/env bats

setup_file() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    _evaluate_openclaw_module_data
    _evaluate_openclaw_module_with_agents_data
}

setup() {
    OPENCLAW_CONFIG="$BATS_FILE_TMPDIR/openclaw-config.json"
    OPENCLAW_AGENTS_CONFIG="$BATS_FILE_TMPDIR/openclaw-agents-config.json"
}

_evaluate_openclaw_module_data() {
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; };
        hm = dotfiles.inputs.home-manager;
        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            dotfiles.homeManagerModules.openclaw
            { home.username = "test"; home.homeDirectory = "/home/test"; home.stateVersion = "25.11"; }
          ];
        }).config;
      in {
        hasAgentsAttr = builtins.hasAttr "agents" cfg.openclaw;
      }
    ' --impure --json 2>/dev/null > "$BATS_FILE_TMPDIR/openclaw-config.json"

    [ -s "$BATS_FILE_TMPDIR/openclaw-config.json" ] || {
        echo "Failed to evaluate openclaw module data" >&2
        return 1
    }
}

_evaluate_openclaw_module_with_agents_data() {
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; };
        hm = dotfiles.inputs.home-manager;
        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          modules = [
            dotfiles.homeManagerModules.openclaw
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
      in {
        hasEvalBot = builtins.hasAttr "eval-bot" cfg.openclaw.agents;
        evalBotEnabled = cfg.openclaw.agents.eval-bot.enable == true;
        defaultAgent = cfg.openclaw.defaultAgent == "eval-bot";
      }
    ' --impure --json 2>/dev/null > "$BATS_FILE_TMPDIR/openclaw-agents-config.json"

    [ -s "$BATS_FILE_TMPDIR/openclaw-agents-config.json" ] || {
        echo "Failed to evaluate openclaw module with agents data" >&2
        return 1
    }
}

@test "openclaw: config option namespace exists" {
    [ "$(jq '.hasAgentsAttr' "$OPENCLAW_CONFIG")" = "true" ]
}

@test "openclaw: agents attr accepts submodule type" {
    [ "$(jq '.hasEvalBot' "$OPENCLAW_AGENTS_CONFIG")" = "true" ]
}

@test "openclaw: agent config evaluates with test agent" {
    [ "$(jq '.evalBotEnabled' "$OPENCLAW_AGENTS_CONFIG")" = "true" ]
    [ "$(jq '.defaultAgent' "$OPENCLAW_AGENTS_CONFIG")" = "true" ]
}
