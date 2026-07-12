{
  lib,
  hostname,
  privateConfigRoot,
  defaultUserId,
}:
let
  privateMem0HostFile = "${toString privateConfigRoot}/machines/${hostname}/mem0-host.nix";
  remoteConfigured = builtins.pathExists privateMem0HostFile;
  remoteBaseUrl = if remoteConfigured then import privateMem0HostFile else "";
  normalizedBaseUrl = lib.removeSuffix "/" remoteBaseUrl;
  memoryServerUrl = "${normalizedBaseUrl}/mcp/claude/sse/${defaultUserId}";
in
{
  inherit remoteConfigured;
  serverConfig = {
    type = "sse";
    url = memoryServerUrl;
  };
}
