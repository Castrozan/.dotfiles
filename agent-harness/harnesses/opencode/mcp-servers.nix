{
  pkgs,
  latest,
  homeDir,
}:
let
  servers = import ../../agent-instructions/production-plugin/mcp-servers.nix {
    inherit pkgs;
    homeDirectory = homeDir;
    chromePackage = latest.google-chrome;
  };
in
pkgs.lib.mapAttrs (name: server: {
  type = "local";
  command = [ server.command ] ++ (server.args or [ ]);
  enabled = true;
  environment = server.env or { };
  timeout = if name == "chrome-devtools" then 120000 else 60000;
}) servers
