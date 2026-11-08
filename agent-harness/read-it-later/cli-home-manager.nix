{
  pkgs,
  hostname ? "",
  ...
}:
{
  home.packages = [
    (import ./package.nix {
      inherit pkgs;
      forgePythonPath = ../agent-instructions/skills/development/forge/scripts;
      machineName = hostname;
    })
  ];
}
