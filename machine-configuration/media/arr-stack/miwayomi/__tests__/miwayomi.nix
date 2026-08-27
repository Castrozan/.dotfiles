{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  provisionerScriptRequiredFragments = [
    "--retry-connrefused"
    "/api/v1/health"
    "/api/v1/extensions/repos"
    "{repos:.}"
    ".repos"
    "--data-binary @-"
  ];
  testPackages = pkgs // {
    writeShellScript =
      _name: scriptText:
      assert builtins.all (fragment: lib.hasInfix fragment scriptText) provisionerScriptRequiredFragments;
      "/nix/store/test-miwayomi-extension-repositories";
  };
  evalMiwayomiModule =
    settings:
    (lib.evalModules {
      specialArgs.pkgs = testPackages;
      modules = [
        ../miwayomi-nixos.nix
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.miwayomi = settings;
        }
      ];
    }).config;
  baseSettings = {
    enable = true;
    stackHomeDirectory = "/home/zanoni/arr-stack";
    baseUrl = "http://arr:4568";
    repositoryListSecretFile = "/run/agenix/suwayomi-extension-repositories";
    composePredecessorUnits = [ "arr-stack-drive-guard.service" ];
  };
  disabledConfiguration = evalMiwayomiModule (baseSettings // { enable = false; });
  enabledConfiguration = evalMiwayomiModule baseSettings;
  composeService = enabledConfiguration.systemd.services.miwayomi-compose;
  repositoryService = enabledConfiguration.systemd.services.miwayomi-extension-repositories;
  repositoryEnvironment = repositoryService.environment;

  composeText = builtins.readFile ../../stack/docker-compose.yml;
  stackModuleText = builtins.readFile ../../stack/arr-stack-home-manager.nix;
  chiseStackText = builtins.readFile ../../chise/chise-arr-stack-nixos.nix;
  chiseSystemText = builtins.readFile ../../../../machines/chise/system/nixos-system.nix;

  miwayomiImageIsPinned = lib.hasInfix "ghcr.io/miwayomi/miwayomi:0.2.9@sha256:8e7094088565b97091319dfa92b80a8c22497a712e72af09e2470454f5942ec4" composeText;
  flaresolverrImageIsPinned = lib.hasInfix "ghcr.io/miwayomi/flaresolverr:0.2.9@sha256:41207a879aebc3e36101734377041a9d82e7375db274aebc0d15c87e51134189" composeText;
  miwayomiIsTailnetOnly =
    lib.hasInfix "\"\${ARR_BIND_ADDR:?set in ~/arr-stack/.env}:4568:4567\"" composeText
    && !(lib.hasInfix "0.0.0.0:4568" composeText)
    && !(lib.hasInfix "127.0.0.1:4568" composeText);
  flaresolverrIsComposeInternal =
    lib.hasInfix "FLARESOLVERR_URL: http://flaresolverr:8191" composeText
    && !(lib.hasInfix "8191:8191" composeText);
  miwayomiStateIsPersistent = lib.hasInfix "\${ARR_CONFIG_ROOT}/miwayomi:/data" composeText;
  miwayomiUpdaterCannotWrite = lib.hasInfix "\${ARR_CONFIG_ROOT}/miwayomi-update-disabled:/data/update:ro" composeText;
  composeWaitsForFlaresolverr =
    lib.hasInfix "condition: service_healthy" composeText
    && lib.hasInfix "http://127.0.0.1:8191/" composeText;
  persistenceDirectoriesAreDeclared =
    lib.hasInfix ''"miwayomi"'' stackModuleText
    && lib.hasInfix ''"miwayomi-update-disabled"'' stackModuleText
    && lib.hasInfix ''"flaresolverr"'' stackModuleText;
  composeApplicatorIsOrdered =
    builtins.elem "docker.service" composeService.after
    && builtins.elem "home-manager-zanoni.service" composeService.after
    && builtins.elem "arr-stack-drive-guard.service" composeService.after
    && builtins.elem "docker.service" composeService.requires
    && builtins.elem "arr-stack-drive-guard.service" composeService.requires
    && builtins.elem "multi-user.target" composeService.wantedBy
    && lib.hasInfix "up --detach miwayomi flaresolverr" composeService.serviceConfig.ExecStart;
  repositoryProvisionerFollowsCompose =
    repositoryService.after == [ "miwayomi-compose.service" ]
    && repositoryService.requires == [ "miwayomi-compose.service" ]
    && builtins.elem "multi-user.target" repositoryService.wantedBy;
  repositoryProvisionerUsesEncryptedList =
    repositoryEnvironment.MIWAYOMI_EXTENSION_REPOSITORIES_FILE
    == "/run/agenix/suwayomi-extension-repositories"
    && repositoryEnvironment.MIWAYOMI_BASE_URL == "http://arr:4568";
  repositoryProvisionerIsBounded = repositoryService.serviceConfig.TimeoutStartSec == "150s";
  chiseWiresTheCapability =
    lib.hasInfix "miwayomi = {" chiseStackText
    && lib.hasInfix "suwayomi-extension-repositories" chiseStackText
    && lib.hasInfix ''"miwayomi"'' chiseStackText
    && lib.hasInfix ''"flaresolverr"'' chiseStackText
    && lib.hasInfix "../../../media/arr-stack/miwayomi/miwayomi-nixos.nix" chiseSystemText;
in
{
  chise-miwayomi-disabled-defines-no-services =
    mkEvalCheck "chise-miwayomi-disabled-defines-no-services"
      (!(disabledConfiguration.systemd.services or { } ? miwayomi-compose))
      "hosts that do not opt into Miwayomi must receive neither its Compose applicator nor its secret provisioner";

  chise-miwayomi-images-are-pinned =
    mkEvalCheck "chise-miwayomi-images-are-pinned" (miwayomiImageIsPinned && flaresolverrImageIsPinned)
      "Miwayomi and its FlareSolverr sidecar must use immutable upstream release digests instead of mutable latest tags";

  chise-miwayomi-listens-only-on-the-tailnet =
    mkEvalCheck "chise-miwayomi-listens-only-on-the-tailnet" miwayomiIsTailnetOnly
      "Miwayomi ships no authentication, so Docker must publish it only on chise's runtime tailnet address and never on wildcard or loopback";

  chise-miwayomi-flaresolverr-is-compose-internal =
    mkEvalCheck "chise-miwayomi-flaresolverr-is-compose-internal" flaresolverrIsComposeInternal
      "FlareSolverr serves only Miwayomi, so its port must stay inside the Compose network rather than being published on any host interface";

  chise-miwayomi-state-survives-container-replacement =
    mkEvalCheck "chise-miwayomi-state-survives-container-replacement" miwayomiStateIsPersistent
      "Miwayomi extensions, SQLite state, reading progress and watch history must live in the stack's persistent config root";

  chise-miwayomi-self-update-is-disabled =
    mkEvalCheck "chise-miwayomi-self-update-is-disabled" miwayomiUpdaterCannotWrite
      "Miwayomi starts its updater unconditionally, so the update subdirectory must be a read-only bind while normal state remains writable";

  chise-miwayomi-waits-for-flaresolverr =
    mkEvalCheck "chise-miwayomi-waits-for-flaresolverr" composeWaitsForFlaresolverr
      "Miwayomi must wait for a healthy FlareSolverr container so protected extension sources do not fail during cold startup";

  chise-miwayomi-persistence-directories-are-declared =
    mkEvalCheck "chise-miwayomi-persistence-directories-are-declared" persistenceDirectoriesAreDeclared
      "Home Manager must create writable Miwayomi and FlareSolverr state plus the updater directory before Docker bind-mounts them";

  chise-miwayomi-compose-is-applied-declaratively =
    mkEvalCheck "chise-miwayomi-compose-is-applied-declaratively" composeApplicatorIsOrdered
      "the NixOS applicator must wait for Home Manager and Docker, then bring up exactly Miwayomi and FlareSolverr on boot and rebuild";

  chise-miwayomi-repositories-follow-compose =
    mkEvalCheck "chise-miwayomi-repositories-follow-compose"
      (repositoryProvisionerFollowsCompose && repositoryProvisionerUsesEncryptedList)
      "the repository provisioner must require the Compose applicator and reconcile the agenix declaration through chise's tailnet alias";

  chise-miwayomi-repository-reconciliation-is-bounded =
    mkEvalCheck "chise-miwayomi-repository-reconciliation-is-bounded" repositoryProvisionerIsBounded
      "repository reconciliation must stop within 150 seconds while leaving bounded headroom after the 80-second health retry for repository reads and writes";

  chise-miwayomi-is-wired-into-the-stack =
    mkEvalCheck "chise-miwayomi-is-wired-into-the-stack" chiseWiresTheCapability
      "chise must import the NixOS capability, enable it with the encrypted repository list, and restore both containers with the other front ends";
}
