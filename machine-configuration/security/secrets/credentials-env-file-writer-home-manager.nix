{
  lib,
  pkgs,
  ...
}:
let
  credentialsEnvFileWriter = pkgs.writeShellScriptBin "write-credentials-env-file" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/write_credentials_env_file.py} "$@"
  '';
in
{
  options.secrets.credentialsEnvFileWriter = lib.mkOption {
    type = lib.types.package;
    default = credentialsEnvFileWriter;
    readOnly = true;
    description = "Writes a KEY=VALUE env file from literal values and agenix secret files, waiting for each secret to materialize and refusing to write anything when one never does. Skipping an unreadable secret instead leaves a partial credentials file behind and still reports success, which is how a truncated file survives unnoticed until the tool that needs the missing key fails.";
  };
}
