{
  pkgs,
  inputs,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
in
{
  home.packages = [
    (pkgs.writeShellApplication {
      name = "agent-session";
      runtimeInputs = [ herdrPackage ];
      text = builtins.readFile ./agent-session;
    })
  ];
}
