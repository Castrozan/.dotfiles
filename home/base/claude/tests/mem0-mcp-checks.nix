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
      localBaseUrl = "http://localhost:8765";
    };
in
{
  mem0-mcp-self-host-tooling-is-deployed =
    mkEvalCheck "mem0-mcp-self-host-tooling-is-deployed"
      (
        (cfg.home.file ? ".config/mem0/openmemory-compose.yaml")
        && builtins.any (
          package: (package.pname or package.name or "") == "mem0-openmemory-up"
        ) cfg.home.packages
      )
      "the official OpenMemory self-host must be deployable: the compose file lands in ~/.config/mem0 and the mem0-openmemory-up bring-up command is on PATH; without these there is no self-hosted server for the local endpoint to reach";

  mem0-mcp-defaults-to-local-openmemory-when-no-private-host-file =
    mkEvalCheck "mem0-mcp-defaults-to-local-openmemory-when-no-private-host-file"
      (
        let
          wrapper = mem0WrapperFor "host-without-a-private-mem0-host-file";
        in
        !wrapper.remoteConfigured
        && wrapper.serverConfig.type == "sse"
        && lib.hasInfix "localhost:8765/mcp/claude/sse/" wrapper.serverConfig.url
      )
      "a host without a private mem0-host.nix must point Claude at the local self-hosted OpenMemory instance (http://localhost:8765/mcp/...); this guards the per-machine default for every non-configured machine";

  mem0-mcp-points-at-remote-when-private-host-file-is-present =
    mkEvalCheck "mem0-mcp-points-at-remote-when-private-host-file-is-present"
      (
        let
          privateTestHostFile = ../../../../private-config/machines/test/mem0-host.nix;
          wrapper = mem0WrapperFor "test";
        in
        (!builtins.pathExists privateTestHostFile)
        || (wrapper.remoteConfigured && lib.hasInfix "mem0-remote.test.invalid" wrapper.serverConfig.url)
      )
      "when private-config/machines/<host>/mem0-host.nix exists, the wrapper must point Claude at that remote host's OpenMemory endpoint; guards the production-active per-machine host-switch the local-default check cannot see";

  mem0-mcp-launchd-autostart-guarded-to-darwin-local =
    mkEvalCheck "mem0-mcp-launchd-autostart-guarded-to-darwin-local"
      (
        let
          autostartFor =
            { isDarwin, usesLocalStack }:
            import ../mcps/mem0/autostart.nix {
              inherit lib isDarwin usesLocalStack;
              bringUpScriptBin = "/nix/store/fake-mem0-openmemory-up";
              environmentPath = "/usr/bin:/bin";
            };
          enabled = autostartFor {
            isDarwin = true;
            usesLocalStack = true;
          };
          onLinux = autostartFor {
            isDarwin = false;
            usesLocalStack = true;
          };
          onRemoteHost = autostartFor {
            isDarwin = true;
            usesLocalStack = false;
          };
        in
        enabled.config.condition
        && (enabled.config.content.launchd.agents ? mem0-openmemory-autostart)
        && enabled.config.content.launchd.agents.mem0-openmemory-autostart.config.RunAtLoad
        && !onLinux.config.condition
        && !onRemoteHost.config.condition
      )
      "the OpenMemory launchd auto-start must register only on darwin hosts that run the local stack (kira), with RunAtLoad so the stack survives reboots; it must stay off on linux and off on hosts pointed at a remote OpenMemory";
}
