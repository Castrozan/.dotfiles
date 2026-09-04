{
  lib,
  pkgs,
  ...
}:
let
  suwayomiBindAddress = import ../../tailnet-bind-address.nix { inherit lib; };
  extensionRepositoriesPackageDirectory = ./scripts/suwayomi_extension_repositories;
  declaredRepositoryListFile = "/run/agenix/suwayomi-extension-repositories";
  declaredRepositoryListDigest = builtins.hashFile "sha256" ../../../../secrets/credentials/suwayomi-extension-repositories.age;
in
{
  systemd.services.suwayomi-extension-repositories = {
    description = "Point Suwayomi at the declared extension repositories";
    after = [ "suwayomi-server.service" ];
    requires = [ "suwayomi-server.service" ];
    wantedBy = [ "multi-user.target" ];
    restartTriggers = [ ../../../../secrets/credentials/suwayomi-extension-repositories.age ];
    environment = {
      SUWAYOMI_GRAPHQL_URL = "http://${suwayomiBindAddress}:4567/api/graphql";
      SUWAYOMI_EXTENSION_REPOSITORIES_FILE = declaredRepositoryListFile;
      SUWAYOMI_EXTENSION_REPOSITORIES_DECLARATION_DIGEST = declaredRepositoryListDigest;
    };
    serviceConfig = {
      Type = "oneshot";
      User = "zanoni";
      Group = "users";
      ExecStart = "${pkgs.python3}/bin/python3 ${extensionRepositoriesPackageDirectory}";
      TimeoutStartSec = "5min";
    };
  };
}
