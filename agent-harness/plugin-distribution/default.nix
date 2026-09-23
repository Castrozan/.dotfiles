{ pkgs }:
let
  package = import ./package.nix { inherit pkgs; };
in
{
  inherit package;
  buildPlugin =
    {
      source,
      targets ? [
        "claude"
        "codex"
        "opencode"
      ],
    }:
    pkgs.runCommand "agent-plugin-bundle" { nativeBuildInputs = [ package ]; } ''
      agent-plugin-build ${pkgs.lib.escapeShellArg (toString source)} --output "$out" \
        ${pkgs.lib.escapeShellArgs (
          pkgs.lib.concatMap (target: [
            "--target"
            target
          ]) targets
        )}
    '';
}
