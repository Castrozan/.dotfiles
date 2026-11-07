{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../vesktop/vesktop-home-manager.nix
    ../../terminal/visual-effects/cbonsai/cbonsai-chise-home-manager.nix
    ../install-nothing/install-nothing-home-manager.nix
    ../minecraft/minecraft-home-manager.nix
    ../horizon/horizon-home-manager.nix
  ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasPackage = name: builtins.any (package: lib.getName package == name) cfg.home.packages;
in
{
  domain-gaming-minecraft-prism-launcher =
    mkEvalCheck "domain-gaming-minecraft-prism-launcher" (hasPackage "prismlauncher")
      "Prism Launcher should be installed as the community-maintained Minecraft instance manager";

  domain-gaming-horizon-launcher =
    mkEvalCheck "domain-gaming-horizon-launcher" (hasPackage "horizon-launcher")
      "Horizon launcher should be installed to play the Rust rewrite of Minecraft: Java Edition";

  domain-gaming-horizon-multiplayer-ports =
    mkEvalCheck "domain-gaming-horizon-multiplayer-ports"
      (
        (import ../horizon/horizon-nixos.nix { }).networking.firewall.allowedTCPPorts == [
          25565
          25580
        ]
      )
      "friends must reach Horizon's dedicated server port and its Play with Friends invite port through the host firewall";

  domain-gaming-vesktop-config =
    mkEvalCheck "domain-gaming-vesktop-config" (hasFile ".config/vesktop/settings/settings.json")
      "vesktop config should be deployed";
}
