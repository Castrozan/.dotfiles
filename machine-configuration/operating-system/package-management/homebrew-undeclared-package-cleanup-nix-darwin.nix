{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config) homebrew;
  declaredBrewfile = pkgs.writeText "Brewfile" homebrew.brewfile;
in
{
  system.activationScripts.homebrew.text = lib.mkIf homebrew.enable (
    lib.mkAfter ''
      if [ -f "${homebrew.prefix}/bin/brew" ]; then
        echo >&2 "Homebrew uninstalling undeclared packages..."
        PATH="${homebrew.prefix}/bin:$PATH" sudo --preserve-env=PATH --user=${lib.escapeShellArg homebrew.user} --set-home \
          env HOMEBREW_NO_AUTO_UPDATE=1 brew bundle cleanup --force --file='${declaredBrewfile}'
      fi
    ''
  );
}
