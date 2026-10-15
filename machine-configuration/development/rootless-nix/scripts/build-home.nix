let
  flake = builtins.getFlake (builtins.toString ../../../..);
  base = flake.homeConfigurations.dot;
  configured = base.extendModules {
    modules = [
      {
        home.homeDirectory = base.pkgs.lib.mkForce (builtins.getEnv "HOME");
        home.username = base.pkgs.lib.mkForce (builtins.getEnv "USER");
      }
    ];
  };
in
configured.activationPackage
