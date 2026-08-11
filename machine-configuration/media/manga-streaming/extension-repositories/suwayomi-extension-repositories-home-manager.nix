{
  lib,
  pkgs,
  ...
}:
let
  suwayomiBindAddress = import ../../tailnet-bind-address.nix { inherit lib; };
  suwayomiGraphqlUrl = "http://${suwayomiBindAddress}:4567/api/graphql";
  extensionRepositoriesPackageDirectory = ./scripts/suwayomi_extension_repositories;
  declaredRepositoryListFile = "/run/agenix/suwayomi-extension-repositories";
  declaredRepositoryListDigest = builtins.hashFile "sha256" ../../../../secrets/credentials/suwayomi-extension-repositories.age;
in
{
  systemd.user.services.suwayomi-extension-repositories = {
    Unit = {
      Description = "Point Suwayomi at the declared extension repositories";
      After = [ "suwayomi-server.service" ];
      Requires = [ "suwayomi-server.service" ];
    };

    Service = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${pkgs.python3}/bin/python3 ${extensionRepositoriesPackageDirectory}";
      Environment = [
        "SUWAYOMI_GRAPHQL_URL=${suwayomiGraphqlUrl}"
        "SUWAYOMI_EXTENSION_REPOSITORIES_FILE=${declaredRepositoryListFile}"
        "SUWAYOMI_EXTENSION_REPOSITORIES_DECLARATION_DIGEST=${declaredRepositoryListDigest}"
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };
}
