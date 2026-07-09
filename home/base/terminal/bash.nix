{ pkgs, lib, ... }:
let
  inherit (pkgs.stdenv.hostPlatform) isDarwin;

  flylineVersion = "1.3.0";

  flylineReleaseAssetForSystem = {
    "aarch64-darwin" = {
      asset = "libflyline-v${flylineVersion}-aarch64-apple-darwin.tar.gz";
      hash = "sha256-fYPAf3OGMrLu/r4rG98mZM1qXAagA9ZaI2KnY8vhhBc=";
    };
  };

  flylineReleaseAsset = flylineReleaseAssetForSystem.${pkgs.stdenv.hostPlatform.system};

  flylineLoadableBuiltin = pkgs.stdenvNoCC.mkDerivation {
    pname = "flyline";
    version = flylineVersion;
    src = pkgs.fetchurl {
      url = "https://github.com/HalFrgrd/flyline/releases/download/v${flylineVersion}/${flylineReleaseAsset.asset}";
      inherit (flylineReleaseAsset) hash;
    };
    dontUnpack = true;
    dontConfigure = true;
    dontBuild = true;
    dontStrip = true;
    installPhase = ''
      runHook preInstall
      mkdir -p "$out/lib"
      tar -xzf "$src" -C "$out/lib"
      mv "$out/lib/libflyline.dylib."* "$out/lib/libflyline.dylib"
      runHook postInstall
    '';
    meta = {
      description = "Bash loadable builtin replacing readline with a ratatui-based line editor";
      homepage = "https://github.com/HalFrgrd/flyline";
      platforms = builtins.attrNames flylineReleaseAssetForSystem;
    };
  };

  shellAliasesForNonInteractiveBash = "$HOME/.dotfiles/home/base/terminal/shell/aliases.sh";
  interactiveBashConfiguration = "$HOME/.dotfiles/home/base/terminal/shell/bash_interactive.sh";
  flylineKeybindingsConfiguration = "$HOME/.dotfiles/home/base/terminal/shell/bash_flyline_config.sh";
in
{
  home.sessionVariables.BASH_ENV = shellAliasesForNonInteractiveBash;

  programs.bash = lib.mkIf isDarwin {
    enable = true;
    initExtra = ''
      if [[ $- == *i* ]]; then
        if enable -f ${flylineLoadableBuiltin}/lib/libflyline.dylib flyline 2>/dev/null; then
          if [ -r "${flylineKeybindingsConfiguration}" ]; then
            . "${flylineKeybindingsConfiguration}"
          fi
        fi
      fi
      if [ -r "${interactiveBashConfiguration}" ]; then
        . "${interactiveBashConfiguration}"
      fi
    '';
  };

  programs.zoxide = lib.mkIf isDarwin {
    enable = true;
    enableBashIntegration = true;
    enableFishIntegration = false;
  };

  programs.carapace = lib.mkIf isDarwin {
    enable = true;
    enableBashIntegration = true;
    enableFishIntegration = false;
  };
}
