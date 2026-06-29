{
  lib,
  hostname,
  privateConfigRoot,
  defaultUserId,
  localBaseUrl,
}:
let
  privateMem0HostFile = "${toString privateConfigRoot}/machines/${hostname}/mem0-host.nix";
  remoteBaseUrl =
    if builtins.pathExists privateMem0HostFile then import privateMem0HostFile else null;
  selectedBaseUrl = if remoteBaseUrl != null then remoteBaseUrl else localBaseUrl;
  normalizedBaseUrl = lib.removeSuffix "/" selectedBaseUrl;
  memoryServerUrl = "${normalizedBaseUrl}/mcp/claude/sse/${defaultUserId}";
in
{
  remoteConfigured = remoteBaseUrl != null;
  serverConfig = {
    type = "sse";
    url = memoryServerUrl;
  };
}
