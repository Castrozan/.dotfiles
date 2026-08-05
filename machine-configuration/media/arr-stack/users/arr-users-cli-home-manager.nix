{ pkgs, stackRoot }:
let
  arrUsersPackageDirectory = ./scripts/arr_users;
in
pkgs.writeShellScriptBin "arr-users" ''
  set -Eeuo pipefail

  export ARR_USERS_JELLYFIN_API_KEY_FILE="''${ARR_USERS_JELLYFIN_API_KEY_FILE:-/run/agenix/jellyfin-admin-api-key}"
  export ARR_USERS_JELLYSEERR_SETTINGS_FILE="''${ARR_USERS_JELLYSEERR_SETTINGS_FILE:-${stackRoot}/config/jellyseerr/settings.json}"

  exec ${pkgs.python312}/bin/python3 ${arrUsersPackageDirectory}/__main__.py "$@"
''
