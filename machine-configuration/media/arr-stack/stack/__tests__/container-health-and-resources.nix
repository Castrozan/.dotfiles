{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  composeText = builtins.readFile ../docker-compose.yml;
  containerContracts = [
    {
      name = "qbittorrent";
      nextName = "prowlarr";
      memoryLimit = "2g";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:8080/"]'';
    }
    {
      name = "prowlarr";
      nextName = "sonarr";
      memoryLimit = "768m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:9696/ping"]'';
    }
    {
      name = "sonarr";
      nextName = "radarr";
      memoryLimit = "768m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:8989/ping"]'';
    }
    {
      name = "radarr";
      nextName = "bazarr";
      memoryLimit = "512m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:7878/ping"]'';
    }
    {
      name = "bazarr";
      nextName = "jellyfin";
      memoryLimit = "512m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:6767/"]'';
    }
    {
      name = "jellyfin";
      nextName = "jellyseerr";
      memoryLimit = "2g";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:8096/health"]'';
    }
    {
      name = "jellyseerr";
      nextName = "kavita";
      memoryLimit = "768m";
      healthProbe = ''["CMD", "wget", "-qO-", "http://127.0.0.1:5055/api/v1/status"]'';
    }
    {
      name = "kavita";
      nextName = "miwayomi";
      memoryLimit = "768m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:5000/api/health"]'';
    }
    {
      name = "miwayomi";
      nextName = "miwayomi-gateway";
      memoryLimit = "768m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:4567/api/v1/health"]'';
    }
    {
      name = "miwayomi-gateway";
      nextName = "flaresolverr";
      memoryLimit = "128m";
      healthProbe = ''["CMD", "wget", "-qO-", "http://127.0.0.1:4568/api/v1/health"]'';
    }
    {
      name = "flaresolverr";
      memoryLimit = "1536m";
      healthProbe = ''["CMD", "curl", "-fsS", "http://127.0.0.1:8191/"]'';
    }
  ];
  occurrenceCount = needle: (builtins.length (lib.splitString needle composeText)) - 1;
  serviceBody =
    contract:
    let
      body = lib.elemAt (lib.splitString "\n  ${contract.name}:\n" composeText) 1;
    in
    if contract ? nextName then lib.head (lib.splitString "\n  ${contract.nextName}:\n" body) else body;
  everyContainerUsesTheSharedSliceAndMeasuredLimit = builtins.all (
    contract: lib.hasInfix "    <<: *media-${contract.memoryLimit}\n" (serviceBody contract)
  ) containerContracts;
  resourceLimits = lib.unique (map (contract: contract.memoryLimit) containerContracts);
  everyMeasuredLimitDeclaresTheSharedSlice = builtins.all (
    memoryLimit:
    lib.hasInfix "&media-${memoryLimit} { cgroup_parent: media-containers.slice, mem_limit: ${memoryLimit} }" composeText
  ) resourceLimits;
  everyContainerHasAnApplicationHealthProbe =
    builtins.all (contract: lib.hasInfix contract.healthProbe (serviceBody contract)) containerContracts
    && occurrenceCount "    healthcheck:\n" == builtins.length containerContracts;
in
{
  chise-arr-stack-containers-use-measured-memory-bounds =
    mkEvalCheck "chise-arr-stack-containers-use-measured-memory-bounds"
      (
        everyContainerUsesTheSharedSliceAndMeasuredLimit
        && everyMeasuredLimitDeclaresTheSharedSlice
        && occurrenceCount "    <<: *media-" == builtins.length containerContracts
        && occurrenceCount "cgroup_parent: media-containers.slice" == builtins.length resourceLimits
        && occurrenceCount "mem_limit:" == builtins.length resourceLimits
      )
      "every Compose container must join the aggregate media slice and carry its measured hard memory ceiling, so one cache-heavy service cannot consume the headroom a rebuild needs";

  chise-arr-stack-containers-have-health-probes =
    mkEvalCheck "chise-arr-stack-containers-have-health-probes"
      everyContainerHasAnApplicationHealthProbe
      "every Compose container must probe its own application endpoint with a binary present in that image, so running-but-dead processes are visible as unhealthy rather than mistaken for service readiness";
}
