{ pkgs }:
let
  package = import ./package.nix { inherit pkgs; };
in
{
  inherit package;
  buildPlugin =
    {
      source,
      opencodeDataRoot ? null,
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
        ${
          pkgs.lib.escapeShellArgs (
            pkgs.lib.concatMap (target: [
              "--target"
              target
            ]) targets
          )
        } ${
          pkgs.lib.optionalString (
            opencodeDataRoot != null
          ) "--opencode-data-root ${pkgs.lib.escapeShellArg opencodeDataRoot}"
        }
    '';
}
