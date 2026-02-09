{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  version = "latest"; # MCPorter version
  prefix = "$HOME/.local/share/mcporter-npm";
in
{
  home = {
    packages = [ nodejs ];

    activation.installMcporter = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      export PATH="${nodejs}/bin:''${PATH:+:$PATH}"

      # Install mcporter globally to isolated prefix
      if ! ${nodejs}/bin/npm --prefix ${prefix} list -g mcporter 2>/dev/null | grep -q mcporter; then
        echo "Installing mcporter@${version}..."
        ${nodejs}/bin/npm install -g --prefix ${prefix} "mcporter@${version}" \
          --no-audit --no-fund --loglevel=error
      else
        echo "mcporter already installed"
      fi
    '';
  };

  # Add to PATH
  home.sessionPath = [ "${prefix}/bin" ];
}
