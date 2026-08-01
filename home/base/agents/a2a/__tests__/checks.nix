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

  declaresNoFileUnder =
    directory: !(lib.any (lib.hasPrefix directory) (builtins.attrNames cfg.home.file));
in
{
  domain-agents-a2a-keeps-no-generated-peer-registry =
    mkEvalCheck "domain-agents-a2a-keeps-no-generated-peer-registry" (declaresNoFileUnder ".claude/a2a")
      "the set of reachable agents is whatever panes are running one right now, which a rebuild-time file cannot know; generating one again would make `a2a list` answer from a snapshot that misses every session opened since the last rebuild and names every session closed since it";

  domain-agents-a2a-declares-no-mcp-server =
    mkEvalCheck "domain-agents-a2a-declares-no-mcp-server"
      (!(cfg.home ? activation.installA2aMcpServer))
      "a2a is reached through the `a2a` command, never an MCP. Re-introducing the npm a2a-mcp-server install would put its tool schemas back into every agent's session prefix, which is the cost this module exists to avoid, and would resurrect an unbounded `npm install -g` inside activation";
}
