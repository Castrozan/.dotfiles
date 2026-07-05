{
  pkgs,
  lib,
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  composeText = builtins.readFile ../../../home/linux/arr-stack/docker-compose.yml;
  envText = builtins.readFile ../../../home/linux/arr-stack/env;
  readmeText = builtins.readFile ../../../home/linux/arr-stack/README.md;
  homepageServicesText = builtins.readFile ../../../home/linux/arr-stack/homepage/services.yaml;

  machineIdentityMapPath = ../../../private-config/machines.nix;
  privateConfigPresent = builtins.pathExists machineIdentityMapPath;
  forbiddenTailnetBindAddress =
    if privateConfigPresent then (import machineIdentityMapPath).chise.tailscaleIp else null;
  publicSourcesCarryNoTailnetIpLiteral =
    forbiddenTailnetBindAddress == null
    || (
      !(lib.hasInfix forbiddenTailnetBindAddress composeText)
      && !(lib.hasInfix forbiddenTailnetBindAddress homepageServicesText)
      && !(lib.hasInfix forbiddenTailnetBindAddress readmeText)
    );

  serviceNames = [
    "qbittorrent"
    "prowlarr"
    "sonarr"
    "radarr"
    "lidarr"
    "readarr"
    "bazarr"
  ];
  composeContainsEveryService = builtins.all (service: lib.hasInfix service composeText) serviceNames;
  restartNoCount = (builtins.length (lib.splitString ''restart: "no"'' composeText)) - 1;
  hasForbiddenRestartPolicy =
    lib.hasInfix "unless-stopped" composeText || lib.hasInfix "restart: always" composeText;

  composeLines = lib.splitString "\n" composeText;
  publishedPortLines = builtins.filter (
    line: builtins.match ''.*- "[0-9$].*'' line != null
  ) composeLines;
  tailnetBindVariable = "\${ARR_BIND_ADDR";
  funnelLoopbackPublishes = [
    "127.0.0.1:8096:8096"
    "127.0.0.1:5055:5055"
  ];
  lineIsFunnelLoopbackPublish =
    line: builtins.any (publish: lib.hasInfix publish line) funnelLoopbackPublishes;
  tailnetBoundPublishCount = builtins.length (
    builtins.filter (line: lib.hasInfix tailnetBindVariable line) publishedPortLines
  );
  everyPublishedPortIsTailnetBoundOrFunnelLoopback =
    publishedPortLines != [ ]
    && tailnetBoundPublishCount >= builtins.length serviceNames
    && builtins.all (
      line: lib.hasInfix tailnetBindVariable line || lineIsFunnelLoopbackPublish line
    ) publishedPortLines;
  composeBindsAWildcardInterface = lib.hasInfix "0.0.0.0" composeText;
  composeLoopbackPublishesOnlyFunnelTargets = builtins.all lineIsFunnelLoopbackPublish (
    builtins.filter (line: lib.hasInfix "127.0.0.1" line) publishedPortLines
  );
  everyServiceHasConfigVolume = builtins.all (
    service: lib.hasInfix ("\${ARR_CONFIG_ROOT}/" + service) composeText
  ) serviceNames;
  envPinsChiseConfigRoot = lib.hasInfix "ARR_CONFIG_ROOT=/home/zanoni/arr-stack/config" envText;
  envPinsChiseDataRoot = lib.hasInfix "ARR_DATA_ROOT=/home/zanoni/arr-stack/data" envText;
  envMatchesChiseUserAndGroup = lib.hasInfix "PUID=1000" envText && lib.hasInfix "PGID=100" envText;

  composeHasNoVpnContainer =
    !(lib.hasInfix "gluetun" composeText) && !(lib.hasInfix "service:gluetun" composeText);
  qbittorrentPinnedToV4 = lib.hasInfix "qbittorrent:4" composeText;
  readmeDocumentsHostLevelVpn =
    lib.hasInfix "nord-on-us" readmeText && lib.hasInfix "nord-off" readmeText;

  moduleConditionForHostname =
    candidateHostname:
    (import ../../../home/linux/arr-stack/default.nix {
      config = {
        home.homeDirectory = "/home/test";
      };
      inherit lib;
      hostname = candidateHostname;
    }).condition;
in
{
  chise-arr-stack-roster-complete =
    mkEvalCheck "chise-arr-stack-roster-complete" composeContainsEveryService
      "the compose file must define every mandated service (qbittorrent, prowlarr, sonarr, radarr, lidarr, readarr, bazarr) so the full *arr stack is present";

  chise-arr-stack-down-by-default-restart-no =
    mkEvalCheck "chise-arr-stack-down-by-default-restart-no"
      (restartNoCount >= builtins.length serviceNames)
      ''every service must set restart: "no" so the stack never auto-starts or auto-restarts; it is brought up by hand only'';

  chise-arr-stack-no-auto-restart-policy =
    mkEvalCheck "chise-arr-stack-no-auto-restart-policy" (!hasForbiddenRestartPolicy)
      "the compose file must not use unless-stopped or restart: always, which would resurrect the stack on boot and defeat down-by-default";

  chise-arr-stack-no-vpn-container =
    mkEvalCheck "chise-arr-stack-no-vpn-container" composeHasNoVpnContainer
      "the stack must ship no per-container VPN (no gluetun); qBittorrent runs direct and the optional VPN is host-level wgnord";

  chise-arr-stack-qbittorrent-pinned-to-v4 =
    mkEvalCheck "chise-arr-stack-qbittorrent-pinned-to-v4" qbittorrentPinnedToV4
      "qBittorrent is pinned to a 4.x image because the EOL Readarr 0.4.18 client cannot authenticate against qBittorrent v5's WebUI";

  chise-arr-stack-documents-host-level-vpn =
    mkEvalCheck "chise-arr-stack-documents-host-level-vpn" readmeDocumentsHostLevelVpn
      "the README must point at the host-level wgnord toggles (nord-on-us / nord-off) as the way to route the stack through a VPN, rather than a per-container gateway";

  chise-arr-stack-enabled-on-chise =
    mkEvalCheck "chise-arr-stack-enabled-on-chise" (moduleConditionForHostname "chise")
      "the arr-stack module must materialize on chise";

  chise-arr-stack-noop-off-chise =
    mkEvalCheck "chise-arr-stack-noop-off-chise"
      (!(moduleConditionForHostname "kira") && !(moduleConditionForHostname "rin"))
      "the arr-stack module must be a no-op on every host other than chise so kira/rin never deploy the stack";

  chise-arr-stack-published-ports-tailnet-bound =
    mkEvalCheck "chise-arr-stack-published-ports-tailnet-bound"
      (
        everyPublishedPortIsTailnetBoundOrFunnelLoopback
        && !composeBindsAWildcardInterface
        && composeLoopbackPublishesOnlyFunnelTargets
      )
      "every published port must bind chise's tailnet address through the \${ARR_BIND_ADDR} variable, except the Jellyfin 127.0.0.1:8096 and Jellyseerr 127.0.0.1:5055 loopback publishes the Tailscale Funnels proxy to reach the public internet; no port may bind the 0.0.0.0 wildcard, and loopback may publish nothing but those funnel targets";

  chise-arr-stack-no-tailnet-ip-literal-in-public-sources =
    mkEvalCheck "chise-arr-stack-no-tailnet-ip-literal-in-public-sources"
      publicSourcesCarryNoTailnetIpLiteral
      "chise's tailnet bind address must never appear as a literal in the public compose, homepage services, or README; it flows in only through the runtime ARR_BIND_ADDR variable and the private-config machine map, so any reintroduction of the raw IP fails this guard on a checkout that has the private submodule";

  chise-arr-stack-config-volume-per-service =
    mkEvalCheck "chise-arr-stack-config-volume-per-service" everyServiceHasConfigVolume
      "every service must bind-mount a config volume under ARR_CONFIG_ROOT so a service added to the compose roster cannot drift away from the persistence directories the module creates";

  chise-arr-stack-env-roots-pinned-to-chise-home =
    mkEvalCheck "chise-arr-stack-env-roots-pinned-to-chise-home"
      (envPinsChiseConfigRoot && envPinsChiseDataRoot)
      "the env config and data roots must point at zanoni's home on chise so the compose bind mounts match the persistence directories the module activation creates";

  chise-arr-stack-env-matches-chise-user-and-group =
    mkEvalCheck "chise-arr-stack-env-matches-chise-user-and-group" envMatchesChiseUserAndGroup
      "PUID/PGID must match zanoni on chise (uid 1000, gid 100 = users group), or the linuxserver containers write files the user cannot manage and chown the bind mounts to the wrong group";
}
