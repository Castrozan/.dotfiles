{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  peerRegistryText = cfg.home.file.".claude/a2a/peers.json".text;
  peerRegistry = builtins.fromJSON peerRegistryText;
in
{
  domain-agents-a2a-peer-registry-is-always-written =
    mkEvalCheck "domain-agents-a2a-peer-registry-is-always-written" (peerRegistry ? peers)
      "The a2a CLI reads ~/.claude/a2a/peers.json to learn which agents answer. The file must exist with a peers object even when no agent exposes itself, because the CLI treats a missing file and an empty registry identically only if the shape is stable; a null or absent peers key would make every command fail with a parse error instead of the intended `no A2A peers declared`";

  domain-agents-a2a-declares-no-mcp-server =
    mkEvalCheck "domain-agents-a2a-declares-no-mcp-server"
      (!(lib.hasInfix "a2a-mcp-server" peerRegistryText) && !(cfg.home ? activation.installA2aMcpServer))
      "a2a is reached through the `a2a` command, never an MCP. Re-introducing the npm a2a-mcp-server install would put its tool schemas back into every agent's session prefix, which is the cost this module exists to avoid, and would resurrect an unbounded `npm install -g` inside activation";
}
