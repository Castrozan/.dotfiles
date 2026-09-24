{ pkgs }:
let
  package = import ./package.nix { inherit pkgs; };
in
{
  inherit package;
  opencodeMcpCommand = [
    "${pkgs.python312}/bin/python3"
    "${./scripts}/opencode_mcp.py"
  ];
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
