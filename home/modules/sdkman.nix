{ pkgs, ... }:
let
  sdkmanDir = "$HOME/.sdkman";
  curlBin = "${pkgs.curl}/bin/curl";
in
{
  # Ensure dependencies needed by SDKMAN! itself
  home.packages = with pkgs; [
    curl
    zip
    unzip
    gnutar
  ];

  # Make SDKMAN! available during activation (after packages are installed).
  home.activation.installSdkman = {
    after = [ "installPackages" ];
    before = [ ];
    data = ''
      if [ -d "${sdkmanDir}" ] && [ -s "${sdkmanDir}/bin/sdkman-init.sh" ]; then
          echo "SDKMAN! already installed."
      else
          echo "Installing SDKMAN!..."
          # Ensure curl and unzip are available even though PATH may not yet include profile bins.
          export PATH="${pkgs.curl}/bin:${pkgs.unzip}/bin:${pkgs.zip}/bin:${pkgs.gnutar}/bin:$PATH"
          ${curlBin} -s "https://get.sdkman.io" | bash > /dev/null 2>&1
      fi
    '';
  };
}
