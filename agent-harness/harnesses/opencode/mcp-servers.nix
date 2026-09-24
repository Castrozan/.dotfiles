{
  pkgs,
  latest,
  homeDir,
  bundle,
}:
let
  distribution = import ../../plugin-distribution { inherit pkgs; };
  servers = import ../../agent-instructions/production-plugin/mcp-servers.nix {
    inherit pkgs;
    homeDirectory = homeDir;
    chromePackage = latest.google-chrome;
  };
in
pkgs.lib.genAttrs (builtins.attrNames servers) (name: {
  type = "local";
  command = distribution.opencodeMcpCommand ++ [ name ];
  enabled = true;
  environment.PLUGIN_ROOT = "${bundle}/plugin";
  timeout = if name == "chrome-devtools" then 120000 else 60000;
})
