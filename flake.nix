{
  description = "Flake for OpenAI Codex CLI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        codex-cli = pkgs.buildNpmPackage rec {
          pname = "codex-cli";
          version = "unstable-2025-04-18";

          src = pkgs.fetchFromGitHub {
            owner = "openai";
            repo = "codex";
            rev = "057f113c6d7a770528033d6be13770f565a46c99";
            sha256 = "sha256-QHeap2nV0d4+jAHXtVGqX2XemtQIaFDCjU0mlUn6PrI=";
          };

          sourceRoot = "${src.name}/codex-cli";

          npmDepsHash = "sha256-XMDGNdAEh0e0hSCgObsV8haZCRYJ8bS2PzIT+yes6GQ="; # Update after first build

          npmBuildScript = "build";
          npmFlags = "--include=dev";

          installPhase = ''
            mkdir -p $out/bin
            cp -r dist $out/
            # Create proper executable wrapper
            echo "#!/usr/bin/env bash" > $out/bin/codex
            echo "exec ${pkgs.nodejs}/bin/node $out/dist/cli.js \"\$@\"" >> $out/bin/codex
            chmod +x $out/bin/codex
          '';

          meta = with pkgs.lib; {
            description = "OpenAI Codex CLI - Terminal coding assistant";
            homepage = "https://github.com/openai/codex";
            license = licenses.asl20;
            platforms = platforms.linux ++ platforms.darwin;
          };
        };
      in
      {
        packages.default = codex-cli;
        devShells.default = pkgs.mkShell { packages = [ codex-cli ]; };
      }
    );
}
