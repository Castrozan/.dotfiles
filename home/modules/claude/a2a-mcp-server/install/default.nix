{
  pkgs,
  homeDir,
  nodejs,
}:
let
  install = import ./install.nix {
    inherit pkgs homeDir nodejs;
  };

  a2aMcpNpmPrefix = "${homeDir}/.local/share/a2a-mcp-server-npm";
  a2aMcpBinary = "${a2aMcpNpmPrefix}/bin/a2a-mcp-server";
in
{
  mcpServerCommand = "${nodejs}/bin/node";
  mcpServerArgs = [ a2aMcpBinary ];
  inherit (install) installA2aMcpViaNpm;
}
