{
  pkgs,
  lib,
  self,
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  nixosCfg = self.nixosConfigurations.chise.config;

  composeText = builtins.readFile ../../../home/linux/arr-stack/docker-compose.yml;
  envText = builtins.readFile ../../../home/linux/arr-stack/env;

  serviceNames = [
    "gluetun"
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
    line: builtins.match ''.*- "[0-9].*'' line != null
  ) composeLines;
  everyPublishedPortIsLoopbackBound =
    publishedPortLines != [ ] && builtins.all (line: lib.hasInfix "127.0.0.1:" line) publishedPortLines;
  composeBindsANonLoopbackInterface = lib.hasInfix "0.0.0.0" composeText;
  everyServiceHasConfigVolume = builtins.all (
    service: lib.hasInfix ("\${ARR_CONFIG_ROOT}/" + service) composeText
  ) serviceNames;
  envPinsChiseConfigRoot = lib.hasInfix "ARR_CONFIG_ROOT=/home/zanoni/arr-stack/config" envText;
  envPinsChiseDataRoot = lib.hasInfix "ARR_DATA_ROOT=/home/zanoni/arr-stack/data" envText;
  envMatchesChiseUserAndGroup = lib.hasInfix "PUID=1000" envText && lib.hasInfix "PGID=100" envText;

  moduleConditionForHostname =
    candidateHostname:
    (import ../../../home/linux/arr-stack/default.nix {
      config = {
        home.homeDirectory = "/home/test";
      };
      inherit lib;
      hostname = candidateHostname;
    }).condition;

  vpnSecret = nixosCfg.age.secrets.arr-vpn-env or null;
in
{
  chise-arr-stack-roster-complete =
    mkEvalCheck "chise-arr-stack-roster-complete" composeContainsEveryService
      "the compose file must define every mandated service (prowlarr, sonarr, radarr, lidarr, readarr, bazarr, qbittorrent, gluetun) so the full *arr stack is present";

  chise-arr-stack-down-by-default-restart-no =
    mkEvalCheck "chise-arr-stack-down-by-default-restart-no"
      (restartNoCount >= builtins.length serviceNames)
      ''every service must set restart: "no" so the stack never auto-starts or auto-restarts; it is brought up by hand only'';

  chise-arr-stack-no-auto-restart-policy =
    mkEvalCheck "chise-arr-stack-no-auto-restart-policy" (!hasForbiddenRestartPolicy)
      "the compose file must not use unless-stopped or restart: always, which would resurrect the stack on boot and defeat down-by-default";

  chise-arr-stack-qbittorrent-routed-through-vpn =
    mkEvalCheck "chise-arr-stack-qbittorrent-routed-through-vpn"
      (lib.hasInfix ''network_mode: "service:gluetun"'' composeText)
      "qbittorrent must share gluetun's network namespace so all torrent traffic exits through the VPN by default";

  chise-arr-stack-gluetun-loads-agenix-secret =
    mkEvalCheck "chise-arr-stack-gluetun-loads-agenix-secret"
      (lib.hasInfix "/run/agenix/arr-vpn-env" composeText)
      "gluetun must load its VPN credentials from the agenix-decrypted env file, not from a plaintext value in the repo";

  chise-arr-stack-vpn-secret-declared =
    mkEvalCheck "chise-arr-stack-vpn-secret-declared" (vpnSecret != null)
      "the arr-vpn-env agenix secret must be declared on chise so gluetun has decrypted credentials at /run/agenix/arr-vpn-env";

  chise-arr-stack-vpn-secret-owned-by-user = mkEvalCheck "chise-arr-stack-vpn-secret-owned-by-user" (
    vpnSecret != null && vpnSecret.owner == "zanoni"
  ) "the arr-vpn-env secret must be owned by zanoni so the user-run docker stack can read it";

  chise-arr-stack-no-plaintext-vpn-key = mkEvalCheck "chise-arr-stack-no-plaintext-vpn-key" (
    !(lib.hasInfix "WIREGUARD_PRIVATE_KEY" envText)
    && !(lib.hasInfix "WIREGUARD_PRIVATE_KEY" composeText)
  ) "no VPN private key may appear in the public compose or env files; secrets live only in agenix";

  chise-arr-stack-enabled-on-chise =
    mkEvalCheck "chise-arr-stack-enabled-on-chise" (moduleConditionForHostname "chise")
      "the arr-stack module must materialize on chise";

  chise-arr-stack-noop-off-chise =
    mkEvalCheck "chise-arr-stack-noop-off-chise"
      (!(moduleConditionForHostname "kira") && !(moduleConditionForHostname "rin"))
      "the arr-stack module must be a no-op on every host other than chise so kira/rin never deploy the stack";

  chise-arr-stack-published-ports-loopback-only =
    mkEvalCheck "chise-arr-stack-published-ports-loopback-only"
      (everyPublishedPortIsLoopbackBound && !composeBindsANonLoopbackInterface)
      "every published port must bind 127.0.0.1 only so the web UIs and download client are never exposed to the LAN; reaching them from another device must go through an SSH tunnel or Tailscale";

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
