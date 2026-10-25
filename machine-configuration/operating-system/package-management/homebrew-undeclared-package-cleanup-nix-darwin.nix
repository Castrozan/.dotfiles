{
  config,
  lib,
  pkgs,
  ...
}:
let
  homebrew = config.homebrew;
  declaredBrewfile = pkgs.writeText "Brewfile" homebrew.brewfile;
in
{
  system.activationScripts.homebrew.text = lib.mkIf homebrew.enable (
    lib.mkAfter ''
      echo >&2 "Homebrew uninstalling undeclared packages..."
      PATH="${homebrew.brewPrefix}:$PATH" sudo --preserve-env=PATH --user=${lib.escapeShellArg homebrew.user} --set-home \
        env HOMEBREW_NO_AUTO_UPDATE=1 brew bundle cleanup --force --file='${declaredBrewfile}'
    ''
  );
}
