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
        "pi"
        "hermes"
      ],
    }:
    pkgs.runCommand "agent-plugin-bundle" { nativeBuildInputs = [ package ]; } ''
      agent-plugin-build ${pkgs.lib.escapeShellArg "${source}"} --output "$out" \
        ${pkgs.lib.escapeShellArgs (
          pkgs.lib.concatMap (target: [
            "--target"
            target
          ]) targets
        )}
    '';
}
