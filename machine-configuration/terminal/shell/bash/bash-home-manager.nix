{ pkgs, ... }:
let
  flylineVersion = "1.7.1";

  flylineReleaseAssetForSystem = {
    "aarch64-darwin" = {
      asset = "libflyline-v${flylineVersion}-aarch64-apple-darwin.tar.gz";
      hash = "sha256-2F+07gYBK1mbuWX+M1Rld41BkJTxVk4XZl8wnMoX8zI=";
    };
    "x86_64-linux" = {
      asset = "libflyline-v${flylineVersion}-x86_64-unknown-linux-gnu.tar.gz";
      hash = "sha256-oX+hhN2/rSmb2SmoR4+CnmSrGP++B/Ab1g108J3wREY=";
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

  shellAliasesForNonInteractiveBash = "$HOME/.dotfiles/machine-configuration/terminal/shell/bash/program-configuration/aliases.sh";
  interactiveBashConfiguration = "$HOME/.dotfiles/machine-configuration/terminal/shell/bash/program-configuration/bash_interactive.sh";
  flylineKeybindingsConfiguration = "$HOME/.dotfiles/machine-configuration/terminal/shell/bash/program-configuration/bash_flyline_config.sh";

  zoxideBashInit = pkgs.runCommand "zoxide-bash-init" { } ''
    mkdir -p "$out"
    ${pkgs.zoxide}/bin/zoxide init bash > "$out/zoxide-init.sh"
  '';

  carapaceBashInit = pkgs.runCommand "carapace-bash-init" { } ''
    mkdir -p "$out"
    ${pkgs.carapace}/bin/carapace _carapace bash > "$out/carapace-init.sh"
  '';
in
{
  home.sessionVariables.BASH_ENV = shellAliasesForNonInteractiveBash;

  programs = {
    bash = {
      enable = true;
      initExtra = ''
        if [[ $- == *i* && -t 0 && -t 1 ]]; then
          if enable -f ${flylineLoadableBuiltin}/lib/libflyline.loadable flyline 2>/dev/null; then
            if [ -r "${flylineKeybindingsConfiguration}" ]; then
              . "${flylineKeybindingsConfiguration}"
            fi
          fi
        fi
        if [ -r "${interactiveBashConfiguration}" ]; then
          . "${interactiveBashConfiguration}"
        fi
        if [ -r "${zoxideBashInit}/zoxide-init.sh" ]; then
          . "${zoxideBashInit}/zoxide-init.sh"
        fi
        if [ -r "${carapaceBashInit}/carapace-init.sh" ]; then
          . "${carapaceBashInit}/carapace-init.sh"
        fi
      '';
    };

    zoxide = {
      enable = true;
      enableBashIntegration = false;
      enableFishIntegration = false;
    };

    carapace = {
      enable = true;
      enableBashIntegration = false;
      enableFishIntegration = false;
    };
  };
}
