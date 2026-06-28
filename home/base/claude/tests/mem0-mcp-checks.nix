{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
}:
{
  mem0-mcp-prewarm-activation-registered =
    mkEvalCheck "mem0-mcp-prewarm-activation-registered"
      (cfg.home.activation ? prewarmMem0McpDependencies)
      "the mem0 MCP module must register its dependency prewarm activation so the local fallback's python deps resolve at rebuild time instead of stalling the first session on an uncached uv resolve";

  mem0-mcp-defaults-to-local-when-no-private-host-file =
    mkEvalCheck "mem0-mcp-defaults-to-local-when-no-private-host-file"
      (
        let
          mem0WrapperForHostWithoutRemote = import ../mcps/mem0/wrapper.nix {
            inherit pkgs lib;
            hostname = "host-without-a-private-mem0-host-file";
            homeDir = "/home/test";
            privateConfigRoot = ../../../../private-config;
          };
        in
        mem0WrapperForHostWithoutRemote.remoteConfigured == false
        && mem0WrapperForHostWithoutRemote.mcpServerCommand != ""
      )
      "a host without a private mem0-host.nix must resolve to the local fallback (remoteConfigured=false) while still producing a runnable MCP server command; this guards the public switchable mechanism plus local degradation for every non-configured machine";

  mem0-mcp-uses-remote-when-private-host-file-is-present =
    mkEvalCheck "mem0-mcp-uses-remote-when-private-host-file-is-present"
      (
        let
          privateTestHostFile = ../../../../private-config/machines/test/mem0-host.nix;
          mem0WrapperForHostWithRemote = import ../mcps/mem0/wrapper.nix {
            inherit pkgs lib;
            hostname = "test";
            homeDir = "/home/test";
            privateConfigRoot = ../../../../private-config;
          };
        in
        (!builtins.pathExists privateTestHostFile) || mem0WrapperForHostWithRemote.remoteConfigured == true
      )
      "when private-config/machines/<host>/mem0-host.nix exists, the wrapper must resolve the remote backend (remoteConfigured=true) by importing that file; this guards the production-active host-switch branch that threads the remote URL into MEM0_REMOTE_BASE_URL, which the fallback-only check cannot see";
}
