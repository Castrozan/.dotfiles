{ pkgs, ... }:
let
  flylineVersion = "1.3.0";

  flylineReleaseAssetForSystem = {
    "aarch64-darwin" = {
      asset = "libflyline-v${flylineVersion}-aarch64-apple-darwin.tar.gz";
      hash = "sha256-fYPAf3OGMrLu/r4rG98mZM1qXAagA9ZaI2KnY8vhhBc=";
    };
    "x86_64-linux" = {
      asset = "libflyline-v${flylineVersion}-x86_64-unknown-linux-gnu.tar.gz";
      hash = "sha256-IbsKeg5BdJb/aO+DecrcBdNeQq7jV/xkrZqNlfaTIPg=";
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
      mv "$out/lib/libflyline."* "$out/lib/libflyline.loadable"
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

  programs = {
    bash = {
      enable = true;
      initExtra = ''
        if [[ $- == *i* ]]; then
          if enable -f ${flylineLoadableBuiltin}/lib/libflyline.loadable flyline 2>/dev/null; then
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

    zoxide = {
      enable = true;
      enableBashIntegration = true;
      enableFishIntegration = false;
    };

    carapace = {
      enable = true;
      enableBashIntegration = true;
      enableFishIntegration = false;
    };
  };
}
