{
  pkgs,
  latest,
  homeDir,
}:
let
  browserMcp = import ../../../agents/skills/browser/install {
    inherit pkgs homeDir;
    nodejs = pkgs.nodejs_22;
    chromePackage = latest.google-chrome;
  };

  chromeDevtoolsStdioInvocation = [
    "${browserMcp.chromeDevtoolsMcpStdioCommand}"
  ]
  ++ browserMcp.chromeDevtoolsMcpStdioArgs;
in
{
  chrome-devtools = {
    type = "local";
    command = chromeDevtoolsStdioInvocation;
    enabled = true;
    timeout = 120000;
  };
}
