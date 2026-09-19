{
  lib,
  pkgs,
  ...
}:
let
  suwayomiBindAddress = import ../../tailnet-bind-address.nix { inherit lib; };
  extensionRepositoriesPackageDirectory = ./scripts/suwayomi_extension_repositories;
  declaredRepositoryListFile = "/run/agenix/suwayomi-extension-repositories";
  declaredRepositoryListDigest = builtins.hashFile "sha256" ../../../../secrets/credentials/media/suwayomi-extension-repositories.age;
in
{
  systemd.services.suwayomi-extension-repositories = {
    description = "Point Suwayomi at the declared extension repositories";
    after = [ "arr-stack-front-ends-compose.service" ];
    requires = [ "arr-stack-front-ends-compose.service" ];
    wantedBy = [ "multi-user.target" ];
    restartTriggers = [ ../../../../secrets/credentials/media/suwayomi-extension-repositories.age ];
    environment = {
      SUWAYOMI_GRAPHQL_URL = "http://${suwayomiBindAddress}:4567/api/graphql";
      SUWAYOMI_EXTENSION_REPOSITORIES_FILE = declaredRepositoryListFile;
      SUWAYOMI_EXTENSION_REPOSITORIES_DECLARATION_DIGEST = declaredRepositoryListDigest;
    };
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      User = "zanoni";
      Group = "users";
      ExecStart = "${pkgs.python3}/bin/python3 ${extensionRepositoriesPackageDirectory}";
      TimeoutStartSec = "5min";
    };
  };
}
