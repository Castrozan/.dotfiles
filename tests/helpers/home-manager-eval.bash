#!/usr/bin/env bash

_warm_flake_eval() {
	local repoDir
	repoDir="$(cd "$(dirname "$BATS_TEST_FILENAME")" && git rev-parse --show-toplevel)"
	nix eval --expr "builtins.getFlake (toString $repoDir)" --impure >/dev/null 2>&1 || true
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
    ' --impure --json 2>/dev/null | tail -n1
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
    ' --impure --json 2>/dev/null | tail -n1
}
