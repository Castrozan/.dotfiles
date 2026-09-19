{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  composeText = builtins.readFile ../docker-compose.yml;
  serviceNames = [
    "qbittorrent"
    "prowlarr"
    "sonarr"
    "radarr"
    "bazarr"
  ];
  composeContainsEveryService = builtins.all (service: lib.hasInfix service composeText) serviceNames;
  restartNoCount = (builtins.length (lib.splitString ''restart: "no"'' composeText)) - 1;
  unlessStoppedCount = (builtins.length (lib.splitString "restart: unless-stopped" composeText)) - 1;
  alwaysOnServices = [
    "jellyfin"
    "jellyseerr"
    "kavita"
    "suwayomi"
    "miwayomi"
    "miwayomi-gateway"
    "flaresolverr"
  ];
  serviceRestartPolicyBlock =
    service: policy: "container_name: arr-${service}\n    restart: ${policy}";
  downloadChainServicesPinnedToRestartNo = builtins.all (
    service: lib.hasInfix (serviceRestartPolicyBlock service ''"no"'') composeText
  ) serviceNames;
  alwaysOnServicesPinnedToUnlessStopped = builtins.all (
    service: lib.hasInfix (serviceRestartPolicyBlock service "unless-stopped") composeText
  ) alwaysOnServices;
  composeHasNoAlwaysRestartPolicy = !(lib.hasInfix "restart: always" composeText);
  moduleConditionForHostname =
    candidateHostname:
    (import ../arr-stack-home-manager.nix {
      config.home.homeDirectory = "/home/test";
      inherit lib pkgs;
      hostname = candidateHostname;
    }).condition;
in
{
  chise-arr-stack-roster-complete =
    mkEvalCheck "chise-arr-stack-roster-complete" composeContainsEveryService
      "the compose file must define every mandated service (qbittorrent, prowlarr, sonarr, radarr, bazarr) so the full *arr stack is present";

  chise-arr-stack-download-chain-restart-no =
    mkEvalCheck "chise-arr-stack-download-chain-restart-no"
      (downloadChainServicesPinnedToRestartNo && restartNoCount == builtins.length serviceNames)
      ''the five download-chain *arr services (qbittorrent, prowlarr, sonarr, radarr, bazarr) must each set restart: "no", and no other service may, so docker never resurrects the download chain on boot: the on-demand supervisor, not docker, owns its lifecycle'';

  chise-arr-stack-front-ends-restart-unless-stopped =
    mkEvalCheck "chise-arr-stack-front-ends-restart-unless-stopped"
      (
        alwaysOnServicesPinnedToUnlessStopped
        && unlessStoppedCount == builtins.length alwaysOnServices
        && composeHasNoAlwaysRestartPolicy
      )
      "restart: unless-stopped is allowed only on the declared always-on front ends so they self-heal and return after reboot, is forbidden on every download-chain service, and restart: always is never allowed";

  chise-arr-stack-enabled-on-chise =
    mkEvalCheck "chise-arr-stack-enabled-on-chise" (moduleConditionForHostname "chise")
      "the arr-stack module must materialize on chise";

  chise-arr-stack-noop-off-chise =
    mkEvalCheck "chise-arr-stack-noop-off-chise"
      (!(moduleConditionForHostname "kira") && !(moduleConditionForHostname "rin"))
      "the arr-stack module must be a no-op on every host other than chise so kira/rin never deploy the stack";
}
