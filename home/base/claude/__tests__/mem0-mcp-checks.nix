{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
}:
let
  mem0WrapperFor =
    hostname:
    import ../mcps/mem0/wrapper.nix {
      inherit lib hostname;
      privateConfigRoot = ../../../../private-config;
      defaultUserId = "lucas";
    };
in
{
  mem0-mcp-omitted-when-no-private-host-file =
    mkEvalCheck "mem0-mcp-omitted-when-no-private-host-file"
      (
        let
          wrapper = mem0WrapperFor "host-without-a-private-mem0-host-file";
        in
        !wrapper.remoteConfigured
      )
      "a host without a private mem0-host.nix must not be marked remote-configured, so the injector leaves mem0 out of ~/.claude.json entirely; there is no local self-hosted stack to fall back to, mem0 is wired only on hosts pointed at a reachable remote OpenMemory";

  mem0-mcp-normalizes-trailing-slash-base-url-into-a-single-sse-path =
    mkEvalCheck "mem0-mcp-normalizes-trailing-slash-base-url-into-a-single-sse-path"
      (
        let
          wrapper = import ../mcps/mem0/wrapper.nix {
            inherit lib;
            hostname = "synthetic-remote-host";
            privateConfigRoot = ./fixtures/mem0-remote-host-fixture;
            defaultUserId = "lucas";
          };
        in
        wrapper.remoteConfigured
        && wrapper.serverConfig.type == "sse"
        && wrapper.serverConfig.url == "https://synthetic-mem0-host.test/mcp/claude/sse/lucas"
      )
      "a mem0-host.nix base URL ending in a slash (the production shape) must normalize to a single-slash sse path, not a //mcp double slash the remote MCP would reject; this uses an in-tree fixture so the endpoint construction is exercised under the standard nix test tier without depending on the private-config submodule being checked out";

  mem0-mcp-points-at-remote-when-private-host-file-is-present =
    mkEvalCheck "mem0-mcp-points-at-remote-when-private-host-file-is-present"
      (
        let
          privateTestHostFile = ../../../../private-config/machines/test/mem0-host.nix;
          wrapper = mem0WrapperFor "test";
        in
        (!builtins.pathExists privateTestHostFile)
        || (
          wrapper.remoteConfigured
          && wrapper.serverConfig.type == "sse"
          && wrapper.serverConfig.url == "http://mem0-remote.test.invalid/mcp/claude/sse/lucas"
        )
      )
      "when private-config/machines/<host>/mem0-host.nix exists, the wrapper must mark the host remote-configured and emit exactly the normalized sse endpoint at that remote host; guards the production-active per-machine host-switch the omitted-default check cannot see";

  mem0-mcp-no-self-host-machinery-remains =
    mkEvalCheck "mem0-mcp-no-self-host-machinery-remains"
      (
        (!(cfg.home.file ? ".config/mem0/openmemory-compose.yaml"))
        && !builtins.any (
          package: (package.pname or package.name or "") == "mem0-openmemory-up"
        ) cfg.home.packages
      )
      "the docker self-hosted OpenMemory stack is removed: no openmemory-compose.yaml is deployed and no mem0-openmemory-up command is on PATH, so no host tries to bring up a local mem0 server";
}
